import json
import logging
import os
import random
import signal
import socket
import sys
import time
import uuid
from datetime import datetime

from flask import Flask, Response, g, jsonify, request
from prometheus_client import Counter, Histogram
from prometheus_flask_exporter import PrometheusMetrics

"""
Backend microservice for distributed system monitoring practice.
Processes requests from frontend and exposes Prometheus metrics.
"""

INSTANCE_ID = os.getenv("INSTANCE_ID", socket.gethostname())
SERVICE_NAME = "backend"

app = Flask(__name__)
metrics = PrometheusMetrics(app)

REQUEST_COUNT = Counter(
    "request_count",
    "Total HTTP requests by endpoint",
    ["service", "endpoint", "method", "http_status"],
)
REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "HTTP request latency in seconds by endpoint",
    ["service", "endpoint", "method", "http_status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)


class JsonFormatter(logging.Formatter):
    """JSON log formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON string."""
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "service": SERVICE_NAME,
            "instance_id": INSTANCE_ID,
        }
        for key in ("request_id", "method", "path", "status", "duration_ms"):
            if hasattr(record, key):
                log_record[key] = getattr(record, key)
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def configure_logging() -> None:
    """Configure JSON logging to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]


logger = logging.getLogger(SERVICE_NAME)
configure_logging()


def handle_shutdown(signum: int, frame) -> None:
    """Handle SIGTERM for graceful shutdown."""
    logger.info("Received SIGTERM, shutting down gracefully...")
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_shutdown)


@app.before_request
def start_timer() -> None:
    """Start request timer and set request ID."""
    g.start_time = time.time()
    g.request_id = str(uuid.uuid4())


@app.after_request
def record_metrics(response: Response) -> Response:
    """Record request metrics after response is prepared."""
    try:
        latency = time.time() - g.start_time
        endpoint = request.path
        method = request.method
        status = response.status_code
        REQUEST_COUNT.labels(SERVICE_NAME, endpoint, method, str(status)).inc()
        REQUEST_LATENCY.labels(SERVICE_NAME, endpoint, method, str(status)).observe(latency)
        logger.info(
            "request.completed",
            extra={
                "request_id": g.get("request_id"),
                "method": method,
                "path": endpoint,
                "status": status,
                "duration_ms": round(latency * 1000, 2),
            },
        )
    except Exception:
        logger.exception("Failed to record metrics", extra={"request_id": g.get("request_id")})
    return response


@app.errorhandler(Exception)
def handle_exception(error: Exception):
    """Handle unexpected exceptions with structured logging."""
    logger.exception("Unhandled exception", extra={"request_id": g.get("request_id")})
    return jsonify({"error": "Internal Server Error"}), 500


@app.route("/api/process", methods=["POST"])
def process():
    """Simulate backend processing work with random delay."""
    try:
        # Simulate variable processing time to create measurable latency.
        delay = random.uniform(0.2, 1.0)
        time.sleep(delay)
        data = request.get_json(silent=True) or {}
        payload = {
            "status": "processed",
            "processing_time": delay,
            "instance_id": INSTANCE_ID,
            "received": data,
            "processed_by": INSTANCE_ID,
        }
        return jsonify(payload)
    except Exception:
        logger.exception("Failed to process request", extra={"request_id": g.get("request_id")})
        return jsonify({"error": "Processing failed"}), 500


@app.route("/api/health")
def health():
    """Return service health."""
    try:
        return jsonify({"status": "healthy", "instance_id": INSTANCE_ID})
    except Exception:
        logger.exception("Failed to build health response", extra={"request_id": g.get("request_id")})
        return jsonify({"error": "Failed to fetch health"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
