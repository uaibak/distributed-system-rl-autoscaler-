# Distributed System RL Autoscaler

This repository is a research practice project focused on intelligent monitoring and optimization of distributed systems using machine learning and reinforcement learning. Phase 1 establishes a baseline microservices environment with monitoring and load testing.

## Phase 1 Overview
**Goal:** Build a runnable microservices setup with observability and repeatable load tests to capture baseline behavior.

Phase 1 includes:
- Frontend and backend Flask services
- Prometheus for metrics collection
- Grafana for visualization
- Locust for load generation
- Jupyter notebook for baseline analysis

## Prerequisites
- Docker Desktop (or Docker Engine with Compose)
- Python 3.9+ (optional for notebook and Locust)

## Quick Start
1. Start the stack:
```
docker compose up --build
```
2. Open the frontend:
```
http://localhost:5000
```

## Service Endpoints
| Service | Endpoint | Description |
| --- | --- | --- |
| Frontend | `/` | HTML landing page |
| Frontend | `/api/info` | Service info |
| Frontend | `/api/calculate?n=1000` | Prime calculation |
| Frontend | `/api/call-backend` | Calls backend |
| Frontend | `/api/health` | Health check |
| Frontend | `/metrics` | Prometheus metrics |
| Backend | `/api/process` | Process payload (POST) |
| Backend | `/api/health` | Health check |
| Backend | `/metrics` | Prometheus metrics |

## Access URLs
- Frontend UI: `http://localhost:5000`
- Backend Health: `http://localhost:5001/api/health`
- Prometheus Targets: `http://localhost:9090/targets`
- Grafana: `http://localhost:3000` (admin/admin)

## Load Testing
```
cd load-testing
locust -f locustfile.py --host=http://localhost:5000
```
Then open `http://localhost:8089`.

## Grafana Metrics
A dashboard named **Microservices Monitoring - Phase 1** is automatically provisioned.
- Request rate
- P95 latency
- Error rate
- Service health
- Instance count

**Note:** CPU/memory panels require a container metrics exporter (e.g., cAdvisor).

## Project Structure
```
services/        # Flask microservices
monitoring/      # Prometheus + Grafana provisioning
load-testing/    # Locust scripts
analysis/        # Baseline notebook and plots
docs/            # Phase documentation
```

## Phase 1 Completion Checklist
- [ ] `docker compose up --build` starts all services
- [ ] Frontend loads at `http://localhost:5000`
- [ ] Backend health at `http://localhost:5001/api/health`
- [ ] Prometheus targets show UP
- [ ] Grafana loads with dashboard
- [ ] Locust tests run successfully
- [ ] Notebook generates plots under `analysis/plots/`

## Next Phases Preview
- Phase 2: Metrics pipeline and RL-friendly data collection
- Phase 3: Baseline autoscaling policies and training loops
- Phase 4: RL-based autoscaler integration and evaluation

## License
MIT (see `LICENSE`).

## Contributing
- Keep changes focused and documented.
- Run services locally before submitting changes.
- Open a PR with a concise summary and verification steps.
