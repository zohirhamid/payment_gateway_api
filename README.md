# 💳 Payment Gateway API (Stripe-like)

A backend payment processing system built with FastAPI that allows merchants to create payments, confirm transactions, and receive webhook notifications — inspired by real-world systems like Stripe.

---

## 🚀 Overview

This project simulates a real-world payment gateway where merchants:

- authenticate using API keys
- create payment intents
- confirm payments (which creates charges)
- receive webhook events asynchronously

The system is designed with production-style patterns such as idempotency, event-driven architecture, and clean separation of concerns.

---

## ✨ Features

- 🔐 API key authentication (hashed storage)
- 💰 PaymentIntent lifecycle management
- ⚡ Charge creation and state transitions
- 🔁 Idempotency support (safe retries)
- 🔔 Webhook event creation and delivery with retry logic
- 🔄 Background task processing for webhooks
- 🧪 End-to-end integration tests (pytest)
- 🗄️ Database migrations with Alembic
- 🧱 Clean layered architecture (routes, services, models)

---

## 🛠 Tech Stack

- FastAPI — API framework  
- SQLAlchemy — ORM  
- SQLite (dev) — database  
- Alembic — database migrations  
- httpx — HTTP client for webhook delivery  
- pytest — testing  

---

## 🏗 Architecture

Client → FastAPI Routes → Services → Database  
                                 ↓  
                             Webhooks

- Routes: handle HTTP requests  
- Services: business logic  
- Models: database schema  
- Schemas: validation  

---

## 📁 Project Structure

```
app/
  api/
    deps.py          # Dependencies (auth, db, etc.)
    routes/
      auth_debug.py  # Auth debugging endpoints
      merchants.py   # Merchant management
      payment_intents.py  # Payment operations
      webhooks.py    # Webhook testing
  core/
    config.py        # App configuration
    logging.py       # Logging setup
    rate_limit.py    # Rate limiting
    security.py      # Security utilities
  db/
    base.py          # SQLAlchemy base
    models/          # Database models
      merchant.py
      payment_intent.py
      charge.py
      webhook_event.py
      idempotency_record.py
    session.py       # Database session management
  schemas/           # Pydantic schemas
    merchant.py
    payment_intent.py
    webhook.py
  services/          # Business logic
    auth_service.py
    payment_service.py
    webhook_service.py
    idempotency_service.py
    charge_service.py
  utils/             # Utilities
    api_key.py
    hashing.py
  workers/           # Background tasks
    celery_app.py
    tasks.py
    __init__.py

tests/               # Test suite
alembic/             # Database migrations
```

## 🔌 Core API Endpoints

### Merchants
- POST /merchants/  
- GET /merchants/me  

### Payment Intents
- POST /payment_intents/  
- GET /payment_intents/{id}  
- GET /payment_intents/  
- POST /payment_intents/{id}/confirm  

### Webhooks
- POST /webhooks/test-receiver  
- GET /webhooks/events  

---

## 💳 Payment Flow

1. Merchant creates a payment intent  
2. Status = requires_payment_method  
3. Merchant confirms payment  
4. System creates charge + updates status  
5. Webhook event is created  
6. Webhook is delivered asynchronously in background  

---

## 🔁 Idempotency Design

- Idempotency-Key header required  
- Same key + same payload → replay  
- Same key + different payload → 409  

---

## 🔔 Webhook System

- payment.succeeded  
- payment.failed  

Flow:
1. Event stored with retry tracking fields
2. Sent via POST in background task
3. Status updated (delivered/failed) with retry count and error details
4. Automatic retry logic for failed deliveries

Features:
- Retry count tracking
- Last attempt timestamp
- Error message storage
- Background delivery using FastAPI BackgroundTasks

## ⚙️ Local Setup

```bash
git clone <your-repo>
cd payment-gateway
pip install -r requirements.txt
alembic upgrade head
```

---

## ▶️ Running the App

```bash
uvicorn app.main:app --reload
```

http://127.0.0.1:8000/docs

---

## 🧪 Running Tests

```bash
pytest
```

---

## 📦 Example Request

```bash
curl -X POST http://127.0.0.1:8000/payment_intents/ \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1000, "currency": "gbp"}'
```

---

## 🧠 What I Learned

- API authentication and security
- Payment flows and state management
- Idempotency for safe API retries
- Webhook implementation with retry logic
- Background task processing with FastAPI
- Clean architecture and separation of concerns
- Database migrations and schema evolution
- Comprehensive testing strategies
- Error handling and logging
- Type safety with modern Python  

---

## 🚀 Future Improvements

- Advanced webhook retry strategies (exponential backoff)
- Celery integration for more robust background jobs
- Rate limiting
- Enhanced logging and monitoring
- Multi-currency support
- Fraud detection
- Webhook signature verification  

---

## 🎯 Summary

A production-inspired payment backend demonstrating real-world backend engineering concepts.
