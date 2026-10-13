# One-shot CLI as an alternative to a resident service

A resident HTTP service is the right default for repeated calls. It is the wrong
shape when the caller is a cron job, a Makefile target, a shell script, or
another program's `subprocess` — anything that wants a decision and then wants
the process gone. Offer **both**; they share the layout resolver, the question
validator and the presets, so the second one is small.

The tell that the user wants this is phrasing like "so I don't have to keep it
running" or "without a resident process". Do not make them ask twice.

## Measure the cost before recommending either shape

A one-shot invocation re-reads the weights every time; that cost dominates
completely. Inference itself is often single-digit milliseconds while process
start plus weight load is hundreds.

Benchmark both shapes on the same machine, same checkpoint, same number of
sequential calls, and put the numbers in the README:

```bash
time (for i in 1 2 3; do mytool-decide --model ./m --state x --questions "$Q" >/dev/null; done)
time (for i in 1 2 3; do curl -sS -X POST localhost:PORT/predict -d "$B" >/dev/null; done)
```

Expect roughly an order of magnitude or more. Then state the guidance plainly —
occasional or scripted calls take the CLI; high volume or concurrency needs the
service. Do not leave the reader to benchmark it themselves, and do not imply the
two are interchangeable.

## Exit codes are the CLI's real interface

A shell script cannot parse prose, so the exit code is the contract. Use
distinct codes and document them:

| Code | Meaning |
|---|---|
| 0 | success |
| 2 | bad usage: missing/invalid argument, malformed JSON, invalid question definition |
| 3 | unusable checkpoint, or a model failure (non-finite output, load error) |

Separating 2 from 3 matters: a script can retry 3 (transient load/IO) without
replaying 2, which is a caller bug and will never succeed.

**A traceback with exit 1 is a bug, not a warning.** When the CLI validates by
calling a shared validator that raises a `ValueError` subclass, the bare
`except ValueError` will not catch the specific type and Python's default
handler exits 1 with a stack trace. Catch the specific type first, and map it to
the usage code:

```python
try:
    questions = read_questions(args)
except SystemExit as e:            # argparse and your own usage errors
    print(f"{prog}: {e}", file=sys.stderr); return EXIT_USAGE
except (ServiceError, json.JSONDecodeError, OSError) as e:
    print(f"{prog}: {e}", file=sys.stderr); return EXIT_USAGE
```

Note `ServiceError` subclasses `ValueError` — the same ordering trap as the HTTP
status mapping, and it bites twice if both entry points share the validator.

## Defer the heavy import until weights are needed

A metadata/inspection flag (`--describe`) and every usage error should not pay
for accelerator runtime startup. Import the model module *inside* `main`, after
argument validation:

```python
def main(argv=None):
    args = parse_args(argv)
    if args.describe:
        print(json.dumps(describe(path))); return 0     # never imported MLX
    try:
        questions = read_questions(args); state = read_state(args)
    except ...:
        return EXIT_USAGE
    from .agent import Agent        # ← paid for only on the real path
```

Two wins beyond latency: `--describe` becomes usable in a health check or shell
completion, and an import-time failure in the model runtime cannot turn a
`--help` into a stack trace.

## Accept state on stdin, and make flag groups mutually exclusive

Reading state from `--state`, `--state-file` *or* stdin removes the need to
author a temp file for a one-off question:

```bash
echo 'some text' | mytool-decide --model ./m --questions "$Q"
```

Reaching stdin only when the terminal is interactive keeps an interactive
invocation from hanging on a read. Validate exclusivity explicitly — argparse
`add_mutually_exclusive_group` does not cover combinations across separately
declared arguments, and silently letting both through produces a
last-one-wins result the caller did not intend:

```python
if args.questions is not None and args.questions_file is not None:
    raise SystemExit("Use only one of --questions or --questions-file")
```

## Offer JSON by default and a compact mode for humans

Emit machine-readable JSON on stdout so the CLI composes with `jq` and
`subprocess`, and add `--compact` for one-answer-per-line human reading. Keep
errors on **stderr** so stdout stays parseable even on failure.

## Testing a CLI: two traps

**argparse exits, it does not return.** `parser.parse_args()` calls
`sys.exit(2)` on a missing required argument, so a test asserting
`main([]) == EXIT_USAGE` fails with a `SystemExit` unless you catch it:

```python
with pytest.raises(SystemExit) as info:
    main([])
assert info.value.code == EXIT_USAGE
```

If a real usage error raises `SystemExit` yourself, catch it explicitly in
`main` so it becomes a clean one-line message plus the code, rather than letting
it propagate with argparse's own formatting.

**Build test fixtures from the real thing.** When a CLI repairs a flattened
checkpoint layout, the test fixture must reproduce the actual on-disk shape —
flat tokenizer **files** at the top level, not a `tokenizer/` directory. A
fixture built from your mental model of the format will not exercise the branch
you wrote. Read the real directory before writing the fixture.

Keep CLI tests stub-based like the service tests, and assert the **exit code**
per failure mode, not just that an error was printed — the code is the contract
a shell script depends on.
