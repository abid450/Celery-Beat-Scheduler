# celery_beat_system/__init__.py
from bt.celery import app as celery_app

__all__ = ('celery_app',)