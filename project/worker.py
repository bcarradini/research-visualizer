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
from rq.exceptions import NoSuchJobError
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


def get_workers():
    q = Queue(connection=_get_redis_conn())
    return Worker.all(queue=q)


def queue_job(f, *args, **kwargs):
    """Queue job for worker."""
    print(f"queue_job(): {f}: {args}, {kwargs}")

    # Enqueue the job
    q = Queue(connection=_get_redis_conn())
    job = q.enqueue(f, *args, **kwargs)

    print(f"queue_job(): {f}: {job.id}")
    return job


def dequeue_job(job_id):
    """Dequeue job for worker."""
    print(f"queue_job(): job_id = {job_id}")
    if job_id:
        # Fetch the job
        q = Queue(connection=_get_redis_conn())
        job = q.fetch_job(job_id)
        if job:
            # Cancel and delete the job
            job.cancel()
            job.delete()


def get_pending_jobs():
    """Return list of rq Job objects that are still in queue or that are being executed by the worker."""
    q = Queue(connection=_get_redis_conn())

    # Get current job from worker (may be None)
    try:
        current_jobs = [worker.get_current_job() for worker in get_workers()]
    except NoSuchJobError:
        current_jobs = []

    # Return any jobs in the queue + the current job (if not None)
    return q.jobs + [job for job in current_jobs if job]

