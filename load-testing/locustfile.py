import random

from locust import FastHttpUser, between, task

"""
Locust load testing file for distributed system.
Simulates realistic user behavior against all endpoints.
"""


class MicroserviceUser(FastHttpUser):
    """User class that hits frontend endpoints with weighted tasks."""

    wait_time = between(1, 3)

    @task(40)
    def home(self) -> None:
        """Visit the home page."""
        with self.client.get("/", name="/", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(20)
    def info(self) -> None:
        """Fetch service info."""
        with self.client.get("/api/info", name="/api/info", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(20)
    def calculate(self) -> None:
        """Run CPU-intensive calculation."""
        n_value = random.randint(1000, 5000)
        with self.client.get(
            f"/api/calculate?n={n_value}",
            name="/api/calculate",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(10)
    def call_backend(self) -> None:
        """Trigger backend call through frontend."""
        with self.client.get(
            "/api/call-backend",
            name="/api/call-backend",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(10)
    def health(self) -> None:
        """Check service health."""
        with self.client.get(
            "/api/health",
            name="/api/health",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")
