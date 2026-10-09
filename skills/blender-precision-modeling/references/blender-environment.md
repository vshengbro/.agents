# Blender environment

## The startup crash on GPU-less hosts

Blender 4.5.4 through 5.2.0 all segfault during startup on a host where Metal is
unavailable — headless sessions, VMs, CI, or a sandbox that denies GPU access.
There is no flag that avoids it.

```
#0 BLI_system_backtrace_with_os_info
#4 blender::gpu::supports_barycentric_whitelist(id<MTLDevice>*, objc_object*)
#5 blender::gpu::MTLBackend::metal_is_supported()
#6 GPU_backend_type_selection_detect()
#7 wm_homefile_read_ex(...)      #8 WM_init(...)      #9 main
```

Upstream `source/blender/gpu/metal/mtl_backend.mm`:

```cpp
bool supports_barycentric_whitelist(id<MTLDevice> device) {
  NSString *gpu_name = [device name];            // nil when device is nil
  BLI_assert([gpu_name length]);                  // compiled out in release
  const char *vendor = [gpu_name UTF8String];    // -> NULL
  ...
  if (strstr(vendor, "AMD") || ...)              // strstr(NULL, ...) -> SIGSEGV
}
```

`MTLCreateSystemDefaultDevice()` returns NULL, so `[device name]` is nil and
`strstr(NULL, …)` faults — during GPU-backend detection, before Python runs.
Confirmed: this code is byte-identical in v4.5.4 and v4.5.14, and unchanged in
v5.2.0.

Check whether you have this problem:

```sh
python3 scripts/bootstrap_blender.py --check /Applications/Blender.app/Contents/MacOS/Blender
```

## The fix

Overwrite the first two instructions of that function with `mov w0, #0 ; ret`.
The probe then reports "not whitelisted", `metal_is_supported()` returns false,
and Blender falls back to no-GPU operation — exactly what it does on any machine
without a GPU. Cycles on the CPU device is unaffected.

```sh
python3 scripts/bootstrap_blender.py     --src /Applications/Blender.app     --dest /path/to/Blender.app     --stage-dir /path/where/rename/works
```

Three properties of that script worth keeping:

- **It never touches the system install.** It works on a copy.
- **It refuses to patch an unrecognised binary.** If the bytes at the symbol do
  not match the expected prologue, it aborts rather than writing 8 bytes at an
  offset it guessed.
- **It validates the measurement.** You can watch it fail on an unmodified
  binary; the whole point is that a silent no-op is impossible.

## Why `--stage-dir` exists

A modified binary loses its signature, and on arm64 macOS an invalidly signed
binary will not launch. `codesign` fixes that ad-hoc — but it replaces files
with `rename(2)`, and **some sandboxes deny `rename` outside the working
directory**. Stage the copy somewhere `rename` works, sign there, then copy the
finished bundle wherever you want it: the signature travels with the bytes.

Set `BLENDER_BIN` if Blender lives somewhere non-standard; `blrun.py` also
checks a conventional path.

## Sandboxed hosts

On a host whose sandbox is append-only (`/tmp` allows create and overwrite but
not `unlink`), expect three consequences:

- `.blend` files cannot be saved into `/tmp` — Blender refuses to overwrite a
  file carrying the sandbox provenance xattr. Save elsewhere, or skip them.
- Failed runs leave files behind; nothing can be deleted.
- `blender.crash.txt` may appear in a sandbox runtime directory.

None of this affects this pipeline: the harness writes PNGs and JSON, and every
run overwrites its own outputs in place.
