from celery import shared_task
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from celery.utils.log import get_task_logger
from flask.globals import current_app
from requests.exceptions import (
    ConnectionError,
    JSONDecodeError,
    HTTPError,
    RequestException,
)
from sqlalchemy.sql.expression import delete, desc, select
from ..celery import CELERY, FlaskTask

_name = "muse_for_anything.tasks"

TASK_LOGGER = get_task_logger(_name)

DEFAULT_BATCH_SIZE = 20


@shared_task
def example_task(data):
    print(f"Processing {data}")
    return "Task completed"
