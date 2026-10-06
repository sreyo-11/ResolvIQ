"""Usage (from backend/):  python -m scripts.rescore_sla"""
from app.core.db import standalone_connection
from app.services import sla_service

if __name__ == "__main__":
    with standalone_connection() as conn:
        print(f"Re-scored {sla_service.rescore_open(conn)} open tickets")