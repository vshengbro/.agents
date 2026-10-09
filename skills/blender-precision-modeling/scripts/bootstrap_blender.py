#!/usr/bin/env python3
"""
bootstrap_blender.py -- make headless Blender work on a GPU-less / sandboxed macOS host.

THE PROBLEM
    Blender 4.5.4 through 5.2.0 all crash at startup on hosts where Metal is
    unavailable (headless sessions, VMs, GPU-denied sandboxes, CI runners):

        #0 BLI_system_backtrace_with_os_info
        #4 blender::gpu::supports_barycentric_whitelist(objcproto9MTLDevice*, objc_object*)
        #5 blender::gpu::MTLBackend::metal_is_supported()
        #6 GPU_backend_type_selection_detect()
        #7 wm_homefile_read_ex(...)
        #8 WM_init(...)
        #9 main

    Upstream source (source/blender/gpu/metal/mtl_backend.mm) has no nil guard:

        bool supports_barycentric_whitelist(id<MTLDevice> device) {
          NSString *gpu_name = [device name];          // nil if device is nil
          BLI_assert([gpu_name length]);                // compiled out in release
          const char *vendor = [gpu_name UTF8String];  // -> NULL
          ...
          if (strstr(vendor, "AMD") || ...)            // strstr(NULL,..) -> SIGSEGV
        }

    MTLCreateSystemDefaultDevice() returns NULL on such hosts, so this runs
    during GPU-backend detection -- before Python starts. No CLI flag skips it
    (macOS only accepts --gpu-backend metal), and DYLD_INSERT_LIBRARIES is
    stripped because Blender is signed with hardened runtime.

THE FIX
    Overwrite the first two instructions of that function with
    `mov w0, #0 ; ret`, so the probe reports "not on the whitelist".
    metal_is_supported() then returns false, Blender falls back to no-GPU
    operation (exactly what it does on any machine without a GPU), and Cycles
    on the CPU device renders normally.

    The system install is NEVER touched. A copy is patched, and only if the
    bytes at the target match the expected prologue.

    Modified binaries lose their signature, so the copy must be re-signed
    ad-hoc. `codesign` replaces files via rename(2); on hosts whose sandbox
    blocks rename (including /tmp), pass --stage-dir pointing at a directory
    where rename works, then copy the finished bundle wherever you like --
    the embedded signature travels with the bytes.

USAGE
    python3 bootstrap_blender.py --src /Applications/Blender.app \\
        --dest /path/to/Blender.app --stage-dir /path/where/rename/works
    python3 bootstrap_blender.py --check /path/to/Blender.app/Contents/MacOS/Blender
"""
import argparse
import os
import shutil
import subprocess
import sys

SYMBOL = "__ZN7blender3gpu30supports_barycentric_whitelistEPU19objcproto9MTLDevice11objc_object"
VMADDR_BASE = 0x100000000           # __TEXT vmaddr with fileoff 0; verified via otool -l
PATCH = bytes([0x00, 0x00, 0x80, 0x52,                # mov w0, #0
               0xC0, 0x03, 0x5F, 0xD6])                # ret
PROLOGUE = bytes([0xF6, 0x57, 0xBD, 0xA9,              # stp x22, x21, [sp, #-0x30]!
                  0xF4, 0x4F, 0x01, 0xA9])              # stp x20, x19, [sp, #0x10]
PATCHED_PREFIX = PATCH


def log(msg):
    print("[bootstrap] " + msg, flush=True)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def rename_works(directory):
    probe_a = os.path.join(directory, ".blender_bootstrap_probe")
    probe_b = probe_a + ".moved"
    try:
        with open(probe_a, "w") as fh:
            fh.write("x")
        os.rename(probe_a, probe_b)
        os.unlink(probe_b)
        return True
    except OSError:
        if os.path.exists(probe_a):
            try:
                os.unlink(probe_a)
            except OSError:
                pass
        return False


def find_offset(binary):
    out = run(["nm", "-arch", "arm64", binary]).stdout
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] == SYMBOL:
            return int(parts[0], 16) - VMADDR_BASE
    return None


def check(binary):
    """Report whether a Blender binary has the nil guard."""
    if not os.path.exists(binary):
        log("MISSING %s" % binary)
        return 2
    off = find_offset(binary)
    if off is None:
        log("symbol absent (stripped or unexpected build) -- cannot inspect")
        return 2
    with open(binary, "rb") as fh:
        fh.seek(off)
        cur = fh.read(8)
    if cur == PATCHED_PREFIX:
        log("PATCHED  %s (offset 0x%x)" % (binary, off))
        return 0
    if cur == PROLOGUE:
        log("VULNERABLE %s (offset 0x%x) -- run without --check to patch" % (binary, off))
        return 1
    log("UNKNOWN bytes at 0x%x: %s -- refusing to touch" % (off, cur.hex()))
    return 2


def macos_metal_available():
    try:
        import ctypes
        lib = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/Metal.framework/Metal")
        lib.MTLCreateSystemDefaultDevice.restype = ctypes.c_void_p
        return lib.MTLCreateSystemDefaultDevice() != 0
    except Exception:
        return None


def patch_bundle(src_app, dest_app, stage_dir):
    if os.path.exists(dest_app):
        log("destination already exists: %s" % dest_app)
        return 3
    if not rename_works(stage_dir):
        log("stage dir cannot rename(2): %s" % stage_dir)
        log("codesign needs rename to replace a signature; pick another stage dir")
        return 4
    log("staging copy in %s (rename verified)" % stage_dir)
    staged = os.path.join(stage_dir, "Blender.app")
    if os.path.exists(staged):
        shutil.rmtree(staged)
    log("copying %s -> %s" % (src_app, staged))
    shutil.copytree(src_app, staged, symlinks=True)

    binary = os.path.join(staged, "Contents", "MacOS", "Blender")
    off = find_offset(binary)
    if off is None:
        log("could not locate %s" % SYMBOL)
        return 5
    with open(binary, "rb") as fh:
        fh.seek(off)
        cur = fh.read(8)
    if cur == PATCHED_PREFIX:
        log("already patched")
    elif cur == PROLOGUE:
        with open(binary, "r+b") as fh:
            fh.seek(off)
            fh.write(PATCH)
        log("patched 8 bytes at 0x%x" % off)
    else:
        log("unexpected prologue %s -- refusing to patch" % cur.hex())
        return 6

    # drop any stray files codesign left inside the bundle
    macos_dir = os.path.join(staged, "Contents", "MacOS")
    for name in os.listdir(macos_dir):
        if name.endswith(".cstemp") or name.endswith(".orig"):
            try:
                os.unlink(os.path.join(macos_dir, name))
                log("removed stray %s" % name)
            except OSError:
                pass

    log("re-signing ad-hoc (this is what needs rename)")
    res = run(["codesign", "--force", "--deep", "--sign", "-", staged])
    if res.returncode != 0 or "replacing existing signature" not in res.stdout + res.stderr:
        log("codesign failed: %s" % (res.stderr or res.stdout).strip()[:400])
        return 7
    log("signed: %s" % (res.stdout + res.stderr).strip().splitlines()[-1])

    os.makedirs(os.path.dirname(os.path.abspath(dest_app)) or ".", exist_ok=True)
    if os.path.exists(dest_app):
        log("destination appeared during staging; leaving it alone")
        return 3
    log("installing -> %s" % dest_app)
    shutil.copytree(staged, dest_app, symlinks=True)
    try:
        shutil.rmtree(staged)
    except OSError:
        pass
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", help="source Blender.app to copy and patch")
    ap.add_argument("--dest", help="where to install the patched Blender.app")
    ap.add_argument("--stage-dir", default=os.getcwd(),
                    help="directory where rename(2) works, used for signing")
    ap.add_argument("--check", help="just report the state of this Blender binary")
    args = ap.parse_args()

    if args.check:
        return check(args.check)

    for tool in ("nm", "otool", "codesign", "clang"):
        if run(["which", tool]).returncode != 0:
            log("missing required tool: %s" % tool)
            return 2
    if sys.platform != "darwin":
        log("this bootstrap is macOS-specific; on Linux/Windows use the stock installer")
        return 0

    metal = macos_metal_available()
    if metal:
        log("Metal device available -- stock Blender should start; patching not needed")
    else:
        log("MTLCreateSystemDefaultDevice() == NULL (no Metal) -- patch required")

    if not args.src or not args.dest:
        ap.error("--src and --dest are required unless --check is used")
    return patch_bundle(args.src, args.dest, args.stage_dir)


if __name__ == "__main__":
    sys.exit(main())
