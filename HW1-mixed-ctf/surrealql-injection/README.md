# SurrealQL Injection

**Category:** Web Exploitation
**Techniques:** Blind (time-based) NoSQL injection, boolean/time oracle scripting
**Difficulty (personal impression):** ★★☆☆☆

## Objective
The app runs a SurrealQL query (`SELECT * FROM article ORDER BY created_at ${sortOrder};`) built
directly from user input. Goal: exfiltrate a secret table's contents (containing the flag)
despite the page only ever rendering the first query's result.

## Vulnerability
The injection point sits after `ORDER BY`, and while it's possible to append arbitrary SurrealQL
statements, none of their results are ever displayed directly — a purely blind injection.

## Approach
Since results can't be read directly, used `SLEEP(...)` combined with conditional logic as a
boolean-to-timing oracle: an injected statement like
`LET $info = INFO FOR DB; LET $keys = object::keys($info.tables); ... SELECT * FROM article WHERE
({condition}) AND SLEEP({sleep_time}s) IS NONE` only delays the response when `{condition}` holds.
This let the attack enumerate, one character at a time:
1. The secret table's name (via `INFO FOR DB` metadata).
2. Its column names (via `DESC` + reading a sample record's keys).
3. The flag value itself, character by character.

`blind_injection.py` automates all three enumeration phases end-to-end.

## Key Takeaway
A query language that blocks direct disclosure of a second query's results doesn't stop
exfiltration if it exposes any conditional side channel (here, timing) — the same blind-injection
methodology used against SQL databases carries over almost directly to a NoSQL/graph database
like SurrealDB.
