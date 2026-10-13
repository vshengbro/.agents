# Serving a Python backend with the standard library only

When a service must add no dependency — an MLX/onnx runtime that ships
stdlib-only, an embedded agent, a private tool whose install surface you do not
want to widen — build it on `http.server`. This is the shape that works, and the
three defaults that silently break it.

## The listen backlog is the first thing that bites

`socketserver.TCPServer` hard-codes `request_queue_size = 5`. That is the
**kernel accept queue depth**, not a thread pool. A client burst larger than it
gets `ECONNRESET` at the TCP layer — the connection dies *before a single line
of your handler runs*, so there is no application log, no traceback, and the
health check still returns 200. The server looks perfectly healthy while clients
see a reset.

```python
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Server(ThreadingHTTPServer):
    request_queue_size = 128   # socketserver's default of 5 resets bursts
    daemon_threads = True      # don't block shutdown on in-flight requests
    allow_reuse_address = True # rebind immediately after restart
```

Measured on a local inference service, 200 requests per tier: 4 workers → 0
failures; 8 workers → 78/120 failed; 16 workers → 110/120 failed. After raising
the backlog: 0 failures at 4, 8, 16 and 32 workers, throughput flat at ~210
req/s. **Throughput that does not improve with concurrency is the signature of
a serialized resource, not a broken server** — see the next section before
"optimizing" it.

### Diagnosing it

A client-side `ConnectionResetError` / `URLError` while the server logs nothing
and `/health` still returns 200 is this bug, not a handler crash. Confirm by
sweeping worker counts and watching failures appear above a sharp threshold:

```python
for workers in (4, 8, 16, 32):
    # fire N requests through a ThreadPoolExecutor, count failures
    # → failures appearing at exactly one step = backlog, not logic
```

## Bound concurrency with a semaphore, not a lock

If the work is a GPU/accelerator call, the runtime already serializes execution.
Spawning unbounded threads adds nothing but queueing latency and memory
pressure. Bound it, and make saturation a **typed error that maps to 503**, not
an unbounded wait:

```python
class BusyError(TimeoutError):
    """Every inference slot occupied past the queue timeout."""

class Registry:
    def __init__(self, max_inflight=16, queue_timeout=60.0):
        self._inflight = threading.Semaphore(max_inflight)
        self.queue_timeout = queue_timeout

@contextmanager
def _slot(registry):
    if not registry._inflight.acquire(timeout=registry.queue_timeout):
        raise BusyError(f"all {registry.max_inflight} slots occupied")
    try:
        yield
    finally:
        registry._inflight.release()   # always release, including on raise
```

Release in a `finally` — a handler that raises mid-inference leaks a slot
permanently, and the service degrades to zero capacity with no error anywhere.

## Validate the request body before claiming a slot

The deep library raises `ValueError` for a bad question type, but it does so
*after* the request has already taken an inference slot. A request body is
untrusted input, so validate it at the boundary:

```python
def validate_question(qid, definition):
    if not isinstance(definition, dict):
        raise ServiceError(f"Question {qid!r} must be an object")
    kind = definition.get("type")
    if kind not in QUESTION_TYPES:          # your enum, not a truthiness check
        raise ServiceError(f"Question {qid!r} has unknown type {kind!r}")
    # ... per-type checks: non-empty, correct container, string labels, no dupes
```

Map exception types to status codes in one place, **ordered most-specific
first**:

```python
except BusyError    as e: self._send(503, {"error": str(e)})
except ServiceError as e: self._send(400, {"error": str(e)})   # subclass of ValueError
except ValueError   as e: self._send(400, ...)
except Exception    as e: self._send(500, ...)  # report, never kill the server
```

`ServiceError(ValueError)` must be caught **before** the bare `ValueError`
clause, or it is swallowed by the wrong branch and a malformed request reports
the wrong status.

## Cap the body size

`Content-Length` from a client is attacker-controlled. Read it into a variable,
reject negatives and absurd values, and only then allocate:

```python
length = int(self.headers.get("Content-Length") or 0)
if length < 0 or length > MAX_BODY_BYTES:
    raise ServiceError(f"body must be 0..{MAX_BODY_BYTES} bytes")
```

With `protocol_version = "HTTP/1.1"` you must always send a correct
`Content-Length` on the response, or clients hang waiting for a body that never
arrives:

```python
self.send_response(code)
self.send_header("Content-Type", "application/json; charset=utf-8")
self.send_header("Content-Length", str(len(body)))
self.end_headers()
```

## Stub the model in tests, never load real weights

A service whose handler tests need an 800MB checkpoint will not get run. Keep
the model behind a seam and inject a stub:

```python
class StubAgent:
    def predict(self, state, questions):
        return {"answers": {qid: {"type": d["type"], "confidence": 1.0}
                            for qid, d in questions.items()}}

registry._agents = {"english": StubAgent(), "multilingual": StubAgent()}
```

This tests the HTTP contract (status codes, payload shape, routing rule,
semaphore release under threads) in seconds with no accelerator. Keep the
real-weights path in a separate end-to-end script: `pytest` for the contract,
`smoke_*.py` against a live server for the wiring.

**A stub is not a validator.** A permissive stub returns 200 for a malformed
body that the real model would reject, so a test asserting "400 for a bad
question type" fails against the stub and passes in production — the test is
then testing the stub, not the service. Validate the payload in the service's
own code path, where the stub cannot bypass it.

## Load-once semantics for expensive resources

Model loading is slow and not thread-safe to construct twice. Use a lock for
construction only, and read the cache without it — the double-checked lock is
correct because the slow path is guarded:

```python
def get(self, name):
    agent = self._agents.get(name)
    if agent is not None:
        return agent                      # fast path, no lock
    with self._lock:
        if name not in self._agents:      # re-check inside the lock
            self._agents[name] = load(name)
        return self._agents[name]
```

Do **not** hold a lock across the prediction call — that serializes all
inference and defeats the threading server entirely. Construction is guarded;
execution is not.

## Dependency-resolution trap

`from . import __version__` inside a subpackage resolves to the **subpackage**,
not the parent. For `pkg/service/cli.py` wanting `pkg.__version__` you need
`from .. import __version__`. The failure is an `ImportError` naming the wrong
module and sends you into the wrong file.

## Verification before claiming it works

A concurrency-bound server has two independent failure modes (backlog, slot
leak) that a single sequential curl will never surface. Ship a script that runs
the full matrix and exits non-zero on the first failed check, so it can gate a
deploy:

```python
check("health -> 200", status == 200)
check("routing picks the right checkpoint", routed["checkpoint"] == expected)
check("concurrent burst completed", len(values) == N)
check("concurrent results deterministic", len(set(values)) == 1)
```

Assert **determinism** under concurrency, not just absence of exceptions. A
racing shared-state bug returns 200s with silently wrong answers, which is worse
than a crash because nothing alerts on it.
