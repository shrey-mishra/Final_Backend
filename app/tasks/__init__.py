from celery import Celery

# Define the Celery app
celery = Celery(
    "bitcoin_trading",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.tasks.trading_tasks"]
)

# Configure Celery
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)