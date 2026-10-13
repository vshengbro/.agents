# Deriving real types for `let` bindings at scale

The explicit-type-on-every-`let` rule generates hundreds of findings whose
remedy cannot be guessed from the expression. `let x = lock.write();` is a
`Result<Guard, PoisonError<Guard>>`, a `Guard`, or an `Option`, depending on
the surrounding control flow. Type it wrong and the build breaks; type it
"helpfully" as a bare `()` or `&str` and you have written fiction.

**Let the compiler state each type, one site at a time.** This reference is
the harvest procedure, the four ways the harvest lies to you, and the shapes
that need a human decision.

## Procedure

1. Collect every finding site as `(file, line)`. The verifier prints them.
2. Back up every file you are about to touch. This is non-negotiable: the
   probe writes into your working tree, and a timeout mid-probe leaves a
   deliberately-broken annotation on disk with nothing reverting it.

   ```bash
   python3 - <<'PY'
   import json, pathlib
   sites = [tuple(s) for s in json.load(open('/tmp/let_sites.json'))]
   backup = {}
   for f, ln in sites:
       p = pathlib.Path(f)
       if f not in backup:
           backup[f] = p.read_text()
   json.dump(backup, open('/tmp/let_backup.json', 'w'))
   print(f"backed up {len(backup)} files for {len(sites)} sites")
   PY
   ```

3. For each site, substitute a deliberately-wrong type, build, and read the
   `found` side of the mismatch. Write the harvest to disk after **every**
   site so a timeout costs one site rather than the whole run.

   ```python
   PROBE = ': std::convert::Infallible'
   diag_re = re.compile(r'expected `([^`]*)`,\s*found `([^`]*)`')
   # rustc reports what the expression actually is on the `found` side
   ```

4. Apply the harvested types, then re-run the verifier. Its count is the
   scoreboard: it must reach 0 before you claim the rule is satisfied.
5. Restore from the backup and assert the tree is clean before finishing.

## The four ways this lies

**rustc stops reporting after a handful of errors per crate.** An E0308 limit
means a batch of N injected probes yields ~8 types and silently discards the
rest. If your progress counter reaches zero before the site list does, you
are reading a truncated run as a finished one. One site per invocation is
slow and is nonetheless the only version that does not under-report.

**Long generic types are truncated with an ellipsis.** A diagnostic carrying
`expected ... found Result<RwLockWriteGuard<'_, ...>, ...>` cannot be written
to source — it is not a type. Do not strip the ellipsis and hope. Read the
inferred type out of the source instead, and prefer a `type` alias the crate
already declares (`EventIter<'_>` for the `VecDeque::IntoIter` a diagnostic
may have normalised to `vec::IntoIter`).

**A progress counter that counts removals counts discards.** Counting "sites
no longer in the todo list" reports a dropped site identically to a resolved
one, and the run prints a total the file on disk cannot corroborate. Count
types you actually parsed and wrote, then assert that number against the
file. This failure presents as an impressive number followed by a build that
still fails.

**`build.rs` is its own crate with its own prelude.** A bare `Error` in a
build script is not the error type you assumed; the fully-qualified path may
be `std::io::Error`. Validate harvested types for a build script against
that crate alone.

## Sites the compiler cannot answer for

Three shapes report something other than a writable type, and each needs the
surrounding code read.

**A closure.** rustc says `found closure`. The usable type comes from the
macro or bound that consumes it — a `html!` handler parameterised
`F: FnMut(Event) + 'static` is written `Box<dyn FnMut(Event)> = Box::new(...)`.
Three plausible-looking answers are each wrong for a different reason: `impl
Trait` is illegal in a `let` binding, a bare `fn(Event)` cannot capture the
environment, and a `dyn` type cannot carry parameter names in the type
position.

**A generic parameter.** `found type parameter F` is already the answer — the
annotation is the parameter's own name.

**A value called and then moved.** `handler(); subscribe(handler);` cannot be
`Box`, which is not `Copy`. Either subscribe takes the closure by value and the
call comes first, or the value is a `Clone` handle (`Arc`) when both
consumers need it. A capture of `Signal<T>` additionally requires `'static`,
which a bare borrow does not have — build a second closure from the same
signal, or wrap so the reference is owned.

## Before and after

Report the verifier count, not the number of sites you visited, and re-run
the build and the test suite after the harvest. Annotations that typecheck are
not the same as annotations that preserve behaviour: a `let handler: () = …`
also compiles, and deleting the call it held is invisible to the compiler.
