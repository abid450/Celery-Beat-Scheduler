# apps/scheduler/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from django.core.mail import EmailMultiAlternatives


logger = get_task_logger(__name__)


# ============= DAILY TASKS =============

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def cleanup_expired_sessions(self):
    """Clean up expired user sessions"""
    try:
        from django.contrib.sessions.models import Session
        
        deleted_count = 0
        for session in Session.objects.all():
            try:
                if session.get_decoded():
                    pass
            except:
                session.delete()
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} expired sessions")
        return {'status': 'success', 'deleted': deleted_count}
        
    except Exception as e:
        logger.error(f"Session cleanup failed: {str(e)}")
        raise self.retry(exc=e, countdown=300)




@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def generate_daily_report(self):
    """
    Generate beautiful HTML daily analytics report
    """
    try:
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        today = timezone.now().date()
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
        # ============= Statistics Calculation =============
        
        # New users today
        new_users = User.objects.filter(date_joined__range=(today_start, today_end)).count()
        
        # Verified users today
        verified_users = User.objects.filter(email_verified_at__range=(today_start, today_end)).count()
        
        # Total users
        total_users = User.objects.count()
        verified_total = User.objects.filter(is_email_verified=True).count()
        
        
        # Calculate percentages
        verification_percentage = round((verified_total / total_users * 100), 1) if total_users > 0 else 0
        growth_rate = round((new_users / total_users * 100), 1) if total_users > 0 else 0
        
        # ============= HTML Template with Embedded CSS =============
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="bn">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Daily Report</title>
            <style>
                /* Reset and Base Styles */
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f0f2f5;
                    line-height: 1.6;
                    color: #333;
                }}
                
                .email-container {{
                    max-width: 650px;
                    margin: 20px auto;
                    background: #ffffff;
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                }}
                
                /* Header Section */
                .email-header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 40px 30px;
                    text-align: center;
                    color: white;
                }}
                
                .email-header h1 {{
                    font-size: 28px;
                    margin-bottom: 10px;
                    font-weight: 600;
                }}
                
                .email-header p {{
                    font-size: 16px;
                    opacity: 0.9;
                }}
                
                .date-badge {{
                    display: inline-block;
                    background: rgba(255, 255, 255, 0.2);
                    padding: 8px 20px;
                    border-radius: 50px;
                    margin-top: 15px;
                    font-size: 14px;
                    backdrop-filter: blur(10px);
                }}
                
                /* Content Section */
                .email-content {{
                    padding: 30px;
                }}
                
                /* Greeting Section */
                .greeting {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 25px;
                    border-left: 4px solid #667eea;
                }}
                
                .greeting h2 {{
                    color: #667eea;
                    font-size: 20px;
                    margin-bottom: 8px;
                }}
                
                /* Stats Grid */
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                
                .stat-card {{
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    padding: 20px;
                    border-radius: 16px;
                    text-align: center;
                    transition: transform 0.3s ease;
                    border: 1px solid #e0e0e0;
                }}
                
                .stat-icon {{
                    font-size: 40px;
                    margin-bottom: 10px;
                }}
                
                .stat-number {{
                    font-size: 32px;
                    font-weight: 700;
                    color: #667eea;
                    margin: 10px 0;
                }}
                
                .stat-label {{
                    color: #666;
                    font-size: 14px;
                    font-weight: 500;
                }}
                
                /* Progress Section */
                .progress-section {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 16px;
                    margin-bottom: 30px;
                }}
                
                .progress-section h3 {{
                    margin-bottom: 15px;
                    color: #333;
                }}
                
                .progress-item {{
                    margin-bottom: 20px;
                }}
                
                .progress-label {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                    font-weight: 500;
                }}
                
                .progress-bar {{
                    background: #e0e0e0;
                    height: 10px;
                    border-radius: 10px;
                    overflow: hidden;
                }}
                
                .progress-fill {{
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    height: 100%;
                    border-radius: 10px;
                    width: {verification_percentage}%;
                }}
                
                /* Alert Boxes */
                .alert-box {{
                    background: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px 20px;
                    border-radius: 12px;
                    margin-bottom: 30px;
                }}
                
                .alert-box.success {{
                    background: #d1fae5;
                    border-left-color: #10b981;
                }}
                
                .alert-title {{
                    font-weight: 700;
                    margin-bottom: 5px;
                    color: #92400e;
                }}
                
                /* Footer */
                .email-footer {{
                    background: #f8f9fa;
                    padding: 25px 30px;
                    text-align: center;
                    border-top: 1px solid #e0e0e0;
                }}
                
                .email-footer p {{
                    color: #666;
                    font-size: 12px;
                    margin: 5px 0;
                }}
                
                .social-links {{
                    margin-top: 15px;
                }}
                
                .social-links a {{
                    display: inline-block;
                    margin: 0 10px;
                    color: #667eea;
                    text-decoration: none;
                    font-size: 14px;
                }}
                
                /* Responsive */
                @media (max-width: 600px) {{
                    .email-container {{
                        margin: 10px;
                        border-radius: 12px;
                    }}
                    
                    .email-header {{
                        padding: 25px 20px;
                    }}
                    
                    .email-header h1 {{
                        font-size: 22px;
                    }}
                    
                    .email-content {{
                        padding: 20px;
                    }}
                    
                    .stats-grid {{
                        grid-template-columns: repeat(2, 1fr);
                        gap: 15px;
                    }}
                    
                    .stat-number {{
                        font-size: 24px;
                    }}
                }}
                
                @media (max-width: 480px) {{
                    .stats-grid {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <!-- Header -->
                <div class="email-header">
                    <h1>📊 Daily Analytics Report</h1>
                    <p>Your daily performance overview</p>
                    <div class="date-badge">
                        <span>📅 {today.strftime('%B %d, %Y')}</span>
                    </div>
                </div>
                
                <!-- Content -->
                <div class="email-content">
                    <!-- Greeting -->
                    <div class="greeting">
                        <h2>Hello Admin! 👋</h2>
                        <p>Here's your daily performance summary for <strong>{today.strftime('%B %d, %Y')}</strong>. Keep up the great work!</p>
                    </div>
                    
                    <!-- Stats Grid -->
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-icon">👥</div>
                            <div class="stat-number">{new_users}</div>
                            <div class="stat-label">New Users Today</div>
                        </div>
                        
                        <div class="stat-card">
                            <div class="stat-icon">✅</div>
                            <div class="stat-number">{verified_users}</div>
                            <div class="stat-label">Email Verified Today</div>
                        </div>
                        
                        <div class="stat-card">
                            <div class="stat-icon">👥</div>
                            <div class="stat-number">{total_users}</div>
                            <div class="stat-label">Total Users</div>
                        </div>
                        
                        <div class="stat-card">
                            <div class="stat-icon">🔐</div>
                            <div class="stat-number">{verified_total}</div>
                            <div class="stat-label">Total Verified</div>
                        </div>
                    </div>
                    
                    <!-- Progress Section -->
                    <div class="progress-section">
                        <h3>📈 Progress Overview</h3>
                        <div class="progress-item">
                            <div class="progress-label">
                                <span>Verified Users</span>
                                <span>{verification_percentage}%</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill"></div>
                            </div>
                        </div>
                        <div class="progress-item">
                            <div class="progress-label">
                                <span>Growth Rate</span>
                                <span>{growth_rate}%</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {growth_rate}%;"></div>
                            </div>
                        </div>
                    </div>
                    
                
                <!-- Footer -->
                <div class="email-footer">
                    <p>📧 This is an automated report generated by your system.</p>
                    <p>🕐 Generated at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <div class="social-links">
                        <a href="#">🔗 Dashboard</a>
                        <a href="#">📊 Analytics</a>
                        <a href="#">⚙️ Settings</a>
                    </div>
                    <p style="margin-top: 15px;">&copy; 2024 Email Verification System. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version (fallback for email clients that don't support HTML)
        text_content = f"""
        Daily Report - {today.strftime('%B %d, %Y')}
        ========================================
        
        Hello Admin!
        
        Today's Statistics:
        📝 New Users: {new_users}
        ✅ Email Verified Today: {verified_users}
        
        Overall Statistics:
        👥 Total Users: {total_users}
        🔐 Verified Users: {verified_total}
                
        Verification Progress: {verification_percentage}%
        Growth Rate: {growth_rate}%
        
        Generated at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        This is an automated report.
        """
        
        subject = f'📊 Daily Report - {today.strftime("%B %d, %Y")}'
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_HOST_USER],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Daily report sent for {today}")
        
        return {
            'status': 'success',
            'date': str(today),
            'new_users': new_users,
            'verified_users': verified_users,
            'total_users': total_users,
            'verified_total': verified_total,
            'verification_percentage': verification_percentage,
        }
        
    except Exception as e:
        logger.error(f"Daily report failed: {str(e)}")
        raise self.retry(exc=e, countdown=600)


@shared_task
def backup_database():
    """Backup database to cloud storage"""
    try:
        import subprocess
        import os
        from django.conf import settings
        
        # Generate backup filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"/tmp/db_backup_{timestamp}.sql"
        
        # Run pg_dump
        result = subprocess.run([
            'pg_dump',
            '-h', settings.DB_HOST,
            '-U', settings.DB_USER,
            '-d', settings.DB_NAME,
            '-f', backup_file
        ], capture_output=True)
        
        if result.returncode == 0:
            # Upload to S3 or cloud storage (placeholder)
            logger.info(f"Database backup created: {backup_file}")
            return {'status': 'success', 'file': backup_file}
        else:
            raise Exception(result.stderr)
            
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


@shared_task
def send_email_digest():
    """Send daily email digest to users"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        users = User.objects.filter(is_active=True, is_email_verified=True)[:1000]
        sent_count = 0
        
        for user in users:
            # Send personalized email (batch processing)
            pass
        
        logger.info(f"Email digest sent to {sent_count} users")
        return {'status': 'success', 'sent_count': sent_count}
        
    except Exception as e:
        logger.error(f"Email digest failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ============= HOURLY TASKS =============

@shared_task
def update_stats_cache():
    """Update system statistics cache"""
    try:
        from django.contrib.auth import get_user_model
        from django.db.models import Count, Sum
        
        User = get_user_model()
        
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'verified_users': User.objects.filter(is_email_verified=True).count(),
            'last_7_days': User.objects.filter(date_joined__gte=timezone.now() - timedelta(days=7)).count(),
            'updated_at': str(timezone.now())
        }
        
        # Cache stats for 1 hour
        cache.set('system_stats', stats, 3600)
        
        logger.info("System stats cache updated")
        return stats
        
    except Exception as e:
        logger.error(f"Stats cache update failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


@shared_task
def check_low_stock():
    """Check for low stock products"""
    try:
        # Add your product model here
        # low_stock_products = Product.objects.filter(stock__lt=10)
        
        low_stock_count = 0
        
        if low_stock_count > 0:
            send_mail(
                subject='Low Stock Alert',
                message=f'There are {low_stock_count} products with low stock.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
            )
        
        logger.info(f"Low stock check completed: {low_stock_count} items")
        return {'status': 'success', 'low_stock_count': low_stock_count}
        
    except Exception as e:
        logger.error(f"Low stock check failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ============= EVERY 30 MINUTES =============

@shared_task
def process_pending_orders():
    """Process pending orders"""
    try:
        # Add your order processing logic here
        processed_count = 0
        
        logger.info(f"Processed {processed_count} pending orders")
        return {'status': 'success', 'processed_count': processed_count}
        
    except Exception as e:
        logger.error(f"Order processing failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


@shared_task
def sync_external_apis():
    """Sync data with external APIs"""
    try:
        # Add your API sync logic here
        synced_count = 0
        
        logger.info(f"Synced {synced_count} records with external APIs")
        return {'status': 'success', 'synced_count': synced_count}
        
    except Exception as e:
        logger.error(f"API sync failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ============= EVERY 15 MINUTES =============

@shared_task
def check_system_health():
    """Check system health and send alerts if needed"""
    try:
        import redis
        from django.db import connection
        
        health = {
            'database': 'ok',
            'redis': 'ok',
            'celery': 'ok',
            'timestamp': str(timezone.now())
        }
        
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check Redis
        r = redis.Redis(host='localhost', port=6370)
        r.ping()
        
        # Log health status
        logger.info(f"System health check: {health}")
        
        return health
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ============= WEEKLY TASKS =============

@shared_task
def cleanup_old_logs():
    """Clean up old log files"""
    try:
        import os
        from pathlib import Path
        
        log_dir = Path(settings.BASE_DIR) / 'logs'
        deleted_count = 0
        cutoff_date = timezone.now() - timedelta(days=30)
        
        for log_file in log_dir.glob('*.log'):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old log files")
        return {'status': 'success', 'deleted': deleted_count}
        
    except Exception as e:
        logger.error(f"Log cleanup failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


@shared_task
def optimize_database():
    """Optimize database (VACUUM, ANALYZE, REINDEX)"""
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("VACUUM ANALYZE;")
            cursor.execute("REINDEX DATABASE CONCURRENTLY;")
        
        logger.info("Database optimization completed")
        return {'status': 'success'}
        
    except Exception as e:
        logger.error(f"Database optimization failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ============= MONTHLY TASKS =============

@shared_task
def generate_monthly_report():
    """Generate monthly analytics report"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        now = timezone.now()
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        new_users = User.objects.filter(date_joined__gte=first_day_of_month).count()
        
        report = {
            'month': now.strftime('%B %Y'),
            'new_users': new_users,
            'total_users': User.objects.count(),
            'generated_at': str(now)
        }
        
        # Cache monthly report
        cache.set(f'monthly_report_{now.strftime("%Y%m")}', report, 2592000)  # 30 days
        
        # Email report to admin
        send_mail(
            subject=f'Monthly Report - {now.strftime("%B %Y")}',
            message=f"Monthly Report\nNew Users: {new_users}\nTotal Users: {report['total_users']}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
        )
        
        logger.info(f"Monthly report generated for {now.strftime('%B %Y')}")
        return report
        
    except Exception as e:
        logger.error(f"Monthly report failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


@shared_task
def rotate_logs():
    """Rotate log files"""
    try:
        import os
        import gzip
        import shutil
        from pathlib import Path
        
        log_dir = Path(settings.BASE_DIR) / 'logs'
        rotated_count = 0
        
        for log_file in log_dir.glob('*.log'):
            if log_file.stat().st_size > 10 * 1024 * 1024:  # 10MB
                # Compress old log
                rotated_file = log_file.with_suffix(f'.log.{timezone.now().strftime("%Y%m%d_%H%M%S")}.gz')
                with open(log_file, 'rb') as f_in:
                    with gzip.open(rotated_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Clear original log
                open(log_file, 'w').close()
                rotated_count += 1
        
        logger.info(f"Rotated {rotated_count} log files")
        return {'status': 'success', 'rotated': rotated_count}
        
    except Exception as e:
        logger.error(f"Log rotation failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}