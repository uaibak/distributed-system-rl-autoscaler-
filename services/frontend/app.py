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
import requests
from flask import Flask, Response, g, jsonify, render_template, request
from prometheus_client import Counter, Histogram
from prometheus_flask_exporter import PrometheusMetrics

"""
Frontend microservice for distributed system monitoring practice.
This service provides multiple endpoints and exposes Prometheus metrics.
"""

INSTANCE_ID = os.getenv("INSTANCE_ID", socket.gethostname())
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:5001")
SERVICE_NAME = "frontend"

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


def primes_up_to(limit: int) -> list[int]:
    """Compute prime numbers up to the given limit using a simple sieve."""
    if limit < 2:
        return []
    sieve = [True] * (limit + 1)
    sieve[0:2] = [False, False]
    for number in range(2, int(limit**0.5) + 1):
        if sieve[number]:
            # Mark multiples as non-prime.
            sieve[number * number : limit + 1 : number] = [False] * len(
                range(number * number, limit + 1, number)
            )
    return [idx for idx, is_prime_val in enumerate(sieve) if is_prime_val]


@app.route("/")
def index():
    """Render the Hello World page."""
    try:
        timestamp = datetime.utcnow().isoformat() + "Z"
        return render_template(
            "index.html",
            instance_id=INSTANCE_ID,
            timestamp=timestamp,
            backend_url=BACKEND_URL,
        )
    except Exception:
        logger.exception("Failed to render index", extra={"request_id": g.get("request_id")})
        return jsonify({"error": "Failed to render page"}), 500


@app.route("/api/info")
def info():
    """Return service info."""
    try:
        return jsonify(
            {
                "service": SERVICE_NAME,
                "instance_id": INSTANCE_ID,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "backend_url": BACKEND_URL,
            }
        )
    except Exception:
        logger.exception("Failed to build info response", extra={"request_id": g.get("request_id")})
        return jsonify({"error": "Failed to fetch info"}), 500


@app.route("/api/calculate")
def calculate():
    """Perform CPU-intensive prime calculation."""
    try:
        n_value = request.args.get("n", "1000")
        if not n_value.isdigit():
            return jsonify({"error": "Query parameter 'n' must be a positive integer"}), 400
        n_value_int = int(n_value)
        if n_value_int <= 0 or n_value_int > 200000:
            return jsonify({"error": "Parameter 'n' must be between 1 and 200000"}), 400
        time.sleep(random.uniform(0.1, 0.5))
        primes = primes_up_to(n_value_int)
        return jsonify(
            {
                "n": n_value_int,
                "prime_count": len(primes),
                "largest_prime": primes[-1] if primes else None,
                "instance_id": INSTANCE_ID,
            }
        )
    except Exception:
        logger.exception("Failed to calculate prime", extra={"request_id": g.get("request_id")})
        return jsonify({"error": "Calculation failed"}), 500


@app.route("/api/call-backend")
def call_backend():
    """Call backend process endpoint."""
    try:
        payload = {"requested_at": datetime.utcnow().isoformat() + "Z"}
        response = requests.post(f"{BACKEND_URL}/api/process", json=payload, timeout=3)
        if response.status_code != 200:
            return jsonify({"error": "Backend error", "status": response.status_code}), 502
        return jsonify({"frontend_instance_id": INSTANCE_ID, "backend": response.json()})
    except requests.RequestException:
        logger.exception("Backend request failed", extra={"request_id": g.get("request_id")})
        return jsonify({"error": "Backend request failed"}), 502


@app.route("/api/health")
def health():
    """Return service health."""
    try:
        return jsonify({"status": "healthy", "instance_id": INSTANCE_ID})
    except Exception:
        logger.exception("Failed to build health response", extra={"request_id": g.get("request_id")})
        return jsonify({"error": "Failed to fetch health"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
