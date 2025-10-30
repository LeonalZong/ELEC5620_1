#!/usr/bin/env python3
"""
Celery Worker and Beat Scheduler Startup Script
"""
import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def start_celery_worker():
    """Start Celery worker"""
    print("🚀 Starting Celery Worker...")
    cmd = [
        "celery", "-A", "app.celery_app", "worker",
        "--loglevel=info",
        "--concurrency=4",
        "--queues=monitoring,data_update,reports,alerts"
    ]
    subprocess.run(cmd)

def start_celery_beat():
    """Start Celery beat scheduler"""
    print("⏰ Starting Celery Beat Scheduler...")
    cmd = [
        "celery", "-A", "app.celery_app", "beat",
        "--loglevel=info"
    ]
    subprocess.run(cmd)

def start_celery_flower():
    """Start Celery Flower monitoring"""
    print("🌸 Starting Celery Flower...")
    cmd = [
        "celery", "-A", "app.celery_app", "flower",
        "--port=5555"
    ]
    subprocess.run(cmd)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start Celery components")
    parser.add_argument("component", choices=["worker", "beat", "flower", "all"], 
                       help="Component to start")
    
    args = parser.parse_args()
    
    if args.component == "worker":
        start_celery_worker()
    elif args.component == "beat":
        start_celery_beat()
    elif args.component == "flower":
        start_celery_flower()
    elif args.component == "all":
        print("🔄 Starting all Celery components...")
        print("Note: Run each component in a separate terminal:")
        print("  python start_celery.py worker")
        print("  python start_celery.py beat")
        print("  python start_celery.py flower")






