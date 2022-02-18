"""
Utilities for interacting with RQ workers.

References:
https://python-rq.org/
https://devcenter.heroku.com/articles/python-rq
"""
# 3rd party
from django import db
from django.conf import settings
from rq import Connection, Queue, Worker
import redis

# Constants
ALL_QUEUES = ['high', 'default', 'low']


#
# -- Private functions
#


def _get_redis_conn():
    """Return redis connection for workers."""
    return redis.from_url(settings.REDISTOGO_URL)


#
# -- Public functions
#


def worker():
    """Start worker."""
    print(f"worker(): start")

    with Connection(_get_redis_conn()):
        # Close DB connection prior to starting worker to force the forked worker process to open
        # its own connection. Otherwise, queries will fail.
        db.connections.close_all()

        # Setup worker to listen to all work queues
        worker = Worker(ALL_QUEUES)

        # Start worker
        worker.work(burst=False)

    print(f"worker(): exit")


def queue_job(f, *args, **kwargs):
    """Queue job for worker."""
    print(f"queue_job(): {f}: {args}, {kwargs}")

    # Enqueue the job
    q = Queue(connection=_get_redis_conn())
    job = q.enqueue(f, *args, **kwargs)

    print(f"queue_job(): {f}: {job.id}")

    return job
