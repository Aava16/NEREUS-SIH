import time
from typing import Any, Dict
from sqlalchemy import text
from sqlalchemy.orm import Session


class HealthRepository:
    """Repository handling low-level database connectivity and diagnostics."""

    def ping_database(self, db: Session) -> Dict[str, Any]:
        """Execute a lightweight probe query against the database and measure latency."""
        start_time = time.perf_counter()
        query = text("SELECT 1 AS is_alive, current_database() AS db_name")
        result = db.execute(query).mappings().one()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "is_alive": result["is_alive"] == 1,
            "database_name": result["db_name"],
            "latency_ms": round(elapsed_ms, 2),
        }
