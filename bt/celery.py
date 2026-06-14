import os
from celery import Celery
from celery.schedules import crontab
from celery.signals import task_prerun, task_postrun, task_failure
from django.utils import timezone


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bt.settings')

app = Celery('bt')

# ============= Base Configuration =============
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


#================  Beat Scheduler --------------------------------------
app.conf.beat_schedule = {

     # ---------- DAILY TASKS ----------
    'cleanup-expired-sessions': {
        'task': 'apps.scheduler.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=0, minute=0),  # প্রতিদিন রাত ১২টা
        'options': {
            'expires': 3600,
            'queue': 'cleanup',
        },
        'args': (),
        'kwargs': {},
    },
    
    'generate-daily-report': {
        'task': 'beat_schedule.tasks.generate_daily_report',
        'schedule': crontab(hour=8, minute=0),  # সকাল ৮টা
        'options': {
            'expires': 1800,
            'queue': 'reports',
        },
    },
    
    'backup-database': {
        'task': 'beat_schedule.tasks.backup_database',
        'schedule': crontab(hour=2, minute=0),  # রাত ২টা
        'options': {
            'expires': 7200,
            'queue': 'backup',
        },
    },
    
    'send-email-digest': {
        'task': 'beat_schedule.tasks.send_email_digest',
        'schedule': crontab(hour=9, minute=0),  # সকাল ৯টা
        'options': {
            'expires': 1800,
            'queue': 'email',
        },
    },
    
    # ---------- HOURLY TASKS ----------
    'update-stats-cache': {
        'task': 'beat_schedule.tasks.update_stats_cache',
        'schedule': crontab(minute=0),  # প্রতি ঘণ্টায়
        'options': {
            'expires': 3500,
            'queue': 'cache',
        },
    },  
    
    'check-low-stock': {
        'task': 'beat_schedule.tasks.check_low_stock',
        'schedule': crontab(minute=0),  # প্রতি ঘণ্টায়
        'options': {
            'expires': 3000,
            'queue': 'inventory',
        },
    },
    
    # ---------- EVERY 30 MINUTES ----------
    'process-pending-orders': {
        'task': 'beat_schedule.tasks.process_pending_orders',
        'schedule': crontab(minute='*/30'),
        'options': {
            'expires': 1500,
            'queue': 'orders',
        },
    },
    
    'sync-external-apis': {
        'task': 'beat_schedule.tasks.sync_external_apis',
        'schedule': crontab(minute='*/30'),
        'options': {
            'expires': 1500,
            'queue': 'integration',
        },
    },
    
    # ---------- EVERY 15 MINUTES ----------
    'check-health': {
        'task': 'beat_schedule.tasks.check_system_health',
        'schedule': crontab(minute='*/15'),
        'options': {
            'expires': 800,
            'queue': 'monitoring',
        },
    },
    
    # ---------- WEEKLY TASKS ----------
    'cleanup-old-logs': {
        'task': 'beat_schedule.tasks.cleanup_old_logs',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # রবিবার রাত ৩টা
        'options': {
            'expires': 10800,
            'queue': 'cleanup',
        },
    },
    
    'optimize-database': {
        'task': 'beat_schedule.tasks.optimize_database',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),  # রবিবার রাত ৪টা
        'options': {
            'expires': 14400,
            'queue': 'maintenance',
        },
    },
                                                                                            
    # ---------- MONTHLY TASKS ----------
    'generate-monthly-report': {
        'task': 'beat_schedule.tasks.generate_monthly_report',
        'schedule': crontab(hour=10, minute=0, day_of_month=1),  # মাসের ১ তারিখ
        'options': {
            'expires': 86400,
            'queue': 'reports',
        },
    },
    
    'rotate-logs': {
        'task': 'beat_schedule.tasks.rotate_logs',
        'schedule': crontab(hour=5, minute=0, day_of_month=1),  # মাসের ১ তারিখ
        'options': {
            'expires': 43200,
            'queue': 'maintenance',
        },
    },
}

# ============= Task Routes =============
app.conf.task_routes = {
    'beat_schedule.tasks.*': {'queue': 'default'},
    'beat_schedule.tasks.send_*': {'queue': 'email'},
    'beat_schedule.tasks.backup_*': {'queue': 'backup'},
    'beat_schedule.tasks.generate_*': {'queue': 'reports'},
    'beat_schedule.tasks.cleanup_*': {'queue': 'cleanup'},
    'beat_schedule.tasks.check_*': {'queue': 'monitoring'},
    'beat_schedule.tasks.sync_*': {'queue': 'integration'},
}

# ============= Task Queues =============
app.conf.task_queues = {
    'default': {'exchange': 'default', 'routing_key': 'default'},
    'email': {'exchange': 'email', 'routing_key': 'email'},
    'backup': {'exchange': 'backup', 'routing_key': 'backup'},
    'reports': {'exchange': 'reports', 'routing_key': 'reports'},
    'cleanup': {'exchange': 'cleanup', 'routing_key': 'cleanup'},
    'monitoring': {'exchange': 'monitoring', 'routing_key': 'monitoring'},
    'integration': {'exchange': 'integration', 'routing_key': 'integration'},
    'cache': {'exchange': 'cache', 'routing_key': 'cache'},
    'orders': {'exchange': 'orders', 'routing_key': 'orders'},
    'inventory': {'exchange': 'inventory', 'routing_key': 'inventory'},
    'maintenance': {'exchange': 'maintenance', 'routing_key': 'maintenance'},
}

# ============= Task Settings =============
app.conf.task_time_limit = 30 * 60  # 30 minutes
app.conf.task_soft_time_limit = 25 * 60  # 25 minutes
app.conf.task_max_retries = 3
app.conf.task_default_retry_delay = 60  # 1 minute
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.task_track_started = True
app.conf.task_send_sent_event = True

# ============= Result Settings =============
app.conf.result_expires = 7 * 24 * 60 * 60  # 7 days
app.conf.result_backend = 'django-db'

# ============= Worker Settings =============
app.conf.worker_prefetch_multiplier = 4
app.conf.worker_max_tasks_per_child = 100
app.conf.worker_max_memory_per_child = 200000  # 200MB

# ============= Celery Beat Settings =============
app.conf.beat_max_loop_interval = 300  # 5 minutes
app.conf.beat_sync_every = 3  # Sync every 3 tasks

# ============= Custom Signals for Monitoring =============

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Log when task starts"""
    from django.core.cache import cache
    cache.set(f'task_{task_id}_start', task_id, timeout=3600)
    print(f"[{task_id}] Task '{task.name}' started at {timezone.now()}")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **extra):
    """Log when task completes"""
    from django.core.cache import cache
    cache.delete(f'task_{task_id}_start')
    print(f"[{task_id}] Task '{task.name}' completed")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extra):
    """Handle task failures"""
    print(f"[{task_id}] Task failed: {exception}")


# ============= Debug Task =============
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    return f'Task executed successfully with ID: {self.request.id}'