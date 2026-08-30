# Minimal behavioral test checklist.
# Run the API and POST the same event twice:
#
# First:  {"status": "processed"}
# Second: {"status": "duplicate_ignored"}
#
# The database PRIMARY KEY on event_id is the idempotency guard.
