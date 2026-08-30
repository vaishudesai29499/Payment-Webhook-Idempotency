from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import sqlite3
from pathlib import Path

app = FastAPI(title="Payment Webhook Idempotency Demo")

DB = Path("webhooks.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS webhook_events (
            event_id TEXT PRIMARY KEY,
            payment_id TEXT NOT NULL,
            order_id TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

class PaymentWebhook(BaseModel):
    event_id: str = Field(min_length=1)
    payment_id: str
    order_id: str
    amount: float = Field(gt=0)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/webhooks/payment")
def payment_webhook(event: PaymentWebhook):
    conn = get_db()

    try:
        # Database uniqueness is the final source of truth.
        cursor = conn.execute(
            """
            INSERT INTO webhook_events
            (event_id, payment_id, order_id, amount, status)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO NOTHING
            """,
            (
                event.event_id,
                event.payment_id,
                event.order_id,
                event.amount,
                "PROCESSED",
            ),
        )
        conn.commit()

        if cursor.rowcount == 0:
            return {
                "status": "duplicate_ignored",
                "event_id": event.event_id,
                "message": "Webhook was already processed safely.",
            }

        # Demo business action.
        # Production: publish an outbox event / queue message here.
        return {
            "status": "processed",
            "event_id": event.event_id,
            "order_id": event.order_id,
            "message": "Payment accepted once.",
        }
    finally:
        conn.close()
