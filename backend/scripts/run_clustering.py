"""Usage (from backend/):  python -m scripts.run_clustering --days 7"""
import argparse

from app.core.db import standalone_connection
from app.services.clustering import refresh_clusters

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--min-cluster-size", type=int, default=6)
    args = ap.parse_args()
    with standalone_connection() as conn:
        print(refresh_clusters(conn, days=args.days, min_cluster_size=args.min_cluster_size))