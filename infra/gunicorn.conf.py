import os
import multiprocessing

bind = "0.0.0.0:8000"
workers = int(
    os.getenv("WEB_CONCURRENCY", str(min(4, max(2, multiprocessing.cpu_count()))))
)
threads = int(os.getenv("WEB_THREADS", "2"))
timeout = 60
graceful_timeout = 30
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
