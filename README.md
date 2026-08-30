# Payment Webhook Idempotency — Real-Time Backend Demo

## Real-world problem

A customer pays ₹999 through a payment gateway.

The gateway sends a webhook:

`payment.success`

But payment providers retry webhooks when your server is slow, temporarily unavailable, or the network fails.

Your backend may receive:

```text
payment.success
payment.success
payment.success
```

If the API blindly processes every event, the same business action can happen multiple times:

- duplicate order confirmation
- duplicate email/SMS
- duplicate wallet/loyalty credit
- incorrect order state
- duplicate fulfillment

This is a small problem, but it is extremely real in production.

## Core solution

Use an **idempotency key/event ID** and persist the processing state.

```text
Payment Gateway
      |
      | webhook event
      v
+-------------+
| Webhook API |
+------+------+
       |
       v
+------------------+
| Idempotency Store|
| event_id UNIQUE  |
+--------+---------+
         |
    first event?
      /       \
    yes        no
    |           |
    v           v
 Process      Return
 business     success
 action       safely
```

## Demo behavior

The FastAPI demo stores webhook events in SQLite.

When the same `event_id` arrives again:

1. The first request processes the payment.
2. The event ID is stored.
3. Duplicate requests are detected.
4. The business action is not executed twice.
5. The API returns a safe duplicate response.

## Run locally

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Open:

`http://127.0.0.1:8000/docs`

## Test the duplicate webhook

Send:

```json
{
  "event_id": "evt_1001",
  "payment_id": "pay_5001",
  "order_id": "order_123",
  "amount": 999
}
```

Send the exact same event again.

Expected result:

```text
First request  -> processed
Second request -> duplicate_ignored
```

## Production architecture

```text
Payment Provider
       |
       v
 API Gateway / Load Balancer
       |
       v
 Webhook Service
       |
       +--------------------+
       |                    |
       v                    v
Idempotency DB          Message Queue
       |                    |
       |                    v
       |              Order Worker
       |                    |
       |                    v
       |              Order DB
       |
       +--> duplicate event -> 200 OK
```

For a larger system:

- PostgreSQL with a UNIQUE constraint on `event_id`
- Redis for short-lived deduplication where appropriate
- Kafka/SQS/RabbitMQ for asynchronous processing
- transactional outbox pattern for reliable event publishing
- retry with exponential backoff
- dead-letter queue
- structured logs and distributed tracing

## Why return 200 for a duplicate?

A duplicate webhook has already been handled successfully.

Returning an error can make the payment provider retry it again, creating unnecessary traffic.

The exact behavior should follow the payment provider's webhook contract.

## Security considerations

Never trust a webhook just because it contains a payment ID.

Production systems should:

- verify webhook signatures
- validate timestamp/replay windows
- authenticate the source according to provider requirements
- validate amount/currency/order mapping
- avoid trusting client-supplied payment status
- use TLS
- log correlation/event IDs

## Key engineering lesson

Retries are normal in distributed systems.

Therefore, important operations should be designed to be **idempotent**.

The goal is not to prevent every duplicate request.

The goal is to make duplicate requests **safe**.

## Interview answer

Question:

"How do you prevent duplicate payment processing when a gateway retries a webhook?"

Strong short answer:

> "I would treat the provider's event ID as an idempotency key, enforce uniqueness at the database level, process the business action transactionally, and return success for already-processed events. For larger workflows I'd decouple downstream work through a queue/outbox pattern."

## Limitations of this demo

This is intentionally small.

It does not implement:

- real payment-provider signature verification
- distributed multi-instance locking
- PostgreSQL
- Kafka/SQS
- transactional outbox
- production observability
- payment-provider-specific webhook contracts

Those are the next production-hardening steps.
