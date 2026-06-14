# 🚀 Celery Beat Schedule Scheduler

A production-ready **Celery Beat Scheduler** for managing periodic tasks, automated emails, database backups, and real-time monitoring with Django & Redis.

[![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django)](https://www.djangoproject.com/)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A?logo=celery)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?logo=redis)](https://redis.io/)
[![Flower](https://img.shields.io/badge/Flower-2.0-FF69B4?logo=flower)](https://flower.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 Features

| Category | Features |
|----------|----------|
| **Daily Tasks** | Session cleanup, daily reports, database backup, email digest |
| **Hourly Tasks** | Cache update, stock monitoring |
| **30-Minute Tasks** | Order processing, API sync |
| **Weekly Tasks** | Log cleanup, database optimization |
| **Monthly Tasks** | Monthly reports, log rotation |
| **Monitoring** | Real-time task monitoring with Flower |
| **Easy Setup** | One-command startup with Celery Starter |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| 🐍 **Python 3.11+** | Core language |
| 🎯 **Django 6.0** | Web framework |
| 🔄 **Celery** | Task queue management |
| 🌸 **Flower** | Real-time monitoring dashboard |
| 🚀 **Celery Starter** | One-command Celery management |
| ⚡ **Redis** | Message broker & cache |
| 🐘 **PostgreSQL/SQLite** | Database |
| 📧 **SMTP** | Email notifications |
| 🐳 **Docker** | Containerization |

---

## 📋 Prerequisites

- Python 3.11+
- Redis Server
- Git

---

## ⚙️ Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/abid450/celery-beat-scheduler.git
cd celery-beat-scheduler
