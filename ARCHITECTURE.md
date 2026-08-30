# Architecture Notes

## Small but production-relevant problem

Payment webhooks are delivered over an unreliable distributed network.

The provider may retry an event if:

- your service times out
- the connection drops after processing
- your server returns a transient error
- the provider does not receive an acknowledgement

Therefore:

`at-least-once delivery` + `non-idempotent business logic` = duplicate side effects

## Design

```text
                 +------------------+
                 | Payment Provider |
                 +--------+---------+
                          |
                          | webhook
                          v
                 +------------------+
                 | Webhook API      |
                 +--------+---------+
                          |
                          v
                 +------------------+
                 | Idempotency DB   |
                 | UNIQUE(event_id) |
                 +----+---------+----+
                      |         |
                first |         | duplicate
                      v         v
                 Business     200 OK
                   Action
                      |
                      v
                 Queue/Outbox
                      |
                      v
               Async Workers
```

## Why database uniqueness matters

An in-memory Python set is not enough when multiple API instances exist:

```text
Request A -> Server 1 -> memory set
Request B -> Server 2 -> memory set
```

Both servers may think the event is new.

A shared persistent store with a unique constraint provides a stronger guarantee.

## Production improvement

For critical payment flows, combine:

1. webhook signature verification
2. database uniqueness on provider event ID
3. transactionally recorded payment state
4. transactional outbox
5. asynchronous downstream processing
6. observability and replay tooling
