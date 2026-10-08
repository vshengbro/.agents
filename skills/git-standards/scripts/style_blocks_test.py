#!/usr/bin/env python3
"""Fixtures for the CSS-in-a-host-language detector (Layer A'').

Each case is (name, path, pre, post, expected) where expected is
"DIRECT_PUSH" or "NEEDS_PR". Run directly:

    python3 style_blocks_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import classify_change as cc  # noqa: E402
import style_blocks as sb  # noqa: E402


def diff_of(pre: str, post: str) -> str:
    """A unified diff with zero context, matching what classify_change reads."""
    import difflib
    return "\n".join(difflib.unified_diff(
        pre.split("\n"), post.split("\n"), n=0, lineterm=""))


def route(path: str, pre: str, post: str) -> str:
    removed, added = sb.changed_declarations(diff_of(pre, post))
    v = sb.classify_style_container(cc.lex, cc.code_sequence, path, pre, post,
                                    pre_changed=removed, post_changed=added)
    return "DIRECT_PUSH" if v else "NEEDS_PR"


# The real euv shell file shape.
EUV_HEAD = """use super::*;

class! {

    // Layout Shell

    pub c_app_root {
        display: "flex";
        height: "100%";
    }

    pub c_app_nav {
        width: var!(nav-width);
        background: var!(background);
        border-left: format!("2px solid {}", var!(border));
        display: "flex";
    }
}
"""

EUV_NO_BORDER = EUV_HEAD.replace('        border-left: format!("2px solid {}", var!(border));\n', "")

FIXTURES = [
    # --- the observed regression: a declaration edit must direct-push -------
    ("euv-border-removed.rs", "ui/src/style/class/shell/fn.rs", EUV_HEAD, EUV_NO_BORDER,
     "DIRECT_PUSH", "deleting a CSS declaration inside class! is presentation"),

    ("euv-colour-changed.rs", "ui/src/style/class/shell/fn.rs", EUV_HEAD,
     EUV_HEAD.replace('background: var!(background);', 'background: var!(muted);'),
     "DIRECT_PUSH", "changing a colour value"),

    ("euv-declaration-added.rs", "ui/src/style/class/shell/fn.rs", EUV_HEAD,
     EUV_HEAD.replace('        width: var!(nav-width);',
                      '        width: var!(nav-width);\n        outline: "none";'),
     "DIRECT_PUSH", "adding a paint-only declaration"),

    # --- these must stay NEEDS_PR: behaviour, not paint -------------------
    ("euv-hover-added.rs", "ui/src/style/class/shell/fn.rs", EUV_HEAD,
     EUV_HEAD.replace('        display: "flex";\n    }\n\n    pub c_app_nav',
                      '        display: "flex";\n        &:hover {\n            color: var(--accent);\n        }\n    }\n\n    pub c_app_nav'),
     "NEEDS_PR", "a nested :hover selector is a behavioural surface"),

    ("euv-display-none.rs", "ui/src/style/class/shell/fn.rs", EUV_HEAD,
     EUV_HEAD.replace('        height: "100%";', '        display: "none";'),
     "NEEDS_PR", "display:none hides a subtree"),

    ("euv-media-query.rs", "ui/src/style/class/shell/fn.rs", EUV_HEAD,
     EUV_HEAD.replace('        height: "100%";\n    }',
                      '        height: "100%";\n        @media (max-width: 767px) {\n            display: "none";\n        }\n    }'),
     "NEEDS_PR", "an @media block is behaviour"),

    # --- these must stay NEEDS_PR: real code in the same file -------------
    ("rust-statement-changed.rs", "src/lib.rs",
     "pub fn f() {\n    let x = 1;\n    let _ = x;\n}\n",
     "pub fn f() {\n    let x = 2;\n    let _ = x;\n}\n",
     "NEEDS_PR", "a plain Rust statement change (no style block at all)"),

    ("code-alongside-style.rs", "ui/src/style/class/fn.rs",
     'use super::*;\n\nclass! {\n    pub c_a {\n        color: "red";\n    }\n}\n\npub fn helper() -> u8 {\n    1\n}\n',
     'use super::*;\n\nclass! {\n    pub c_a {\n        color: "red";\n    }\n}\n\npub fn helper() -> u8 {\n    2\n}\n',
     "NEEDS_PR", "a real fn changed in a file that also holds style blocks"),

    ("class-call-changed.rs", "ui/src/style/class/fn.rs",
     'use super::*;\n\nclass! {\n    pub c_a {\n        color: "red";\n    }\n}\n\nlet extra = 1;\n',
     'use super::*;\n\nclass! {\n    pub c_a {\n        color: "red";\n    }\n}\n\nlet extra = 2;\n',
     "NEEDS_PR", "a statement outside the blocks changed"),

    # --- TS/Vue equivalents ----------------------------------------------
    ("ts-style-object.ts", "src/styles.ts",
     "export const s = {\n  '.a': {\n    color: 'red',\n    padding: '4px',\n  },\n};\n",
     "export const s = {\n  '.a': {\n    color: 'blue',\n    padding: '4px',\n  },\n};\n",
     "NEEDS_PR", "a TS object literal is code, not a CSS block macro"),

    ("vue-style-block.vue", "src/App.vue",
     "<style>\n.a {\n  color: red;\n}\n</style>\n",
     "<style>\n.a {\n  color: blue;\n}\n</style>\n",
     "NEEDS_PR", "a .vue SFC is handled by its own path rules, not this layer"),

    # --- blank / comment only --------------------------------------------
    ("style-comment-only.rs", "ui/src/style/class/shell/fn.rs", EUV_HEAD,
     EUV_HEAD.replace('        width: var!(nav-width);',
                      '        // the historic floor\n        width: var!(nav-width);'),
     "DIRECT_PUSH", "a comment added inside a style block is documentation"),
]


def main() -> int:
    print("style_blocks fixtures (CSS-in-a-host-language, Layer A'')")
    print("=" * 78)
    failures = 0
    for name, path, pre, post, expected, why in FIXTURES:
        got = route(path, pre, post)
        ok = got == expected
        failures += 0 if ok else 1
        print("  %-4s %-26s -> %-11s %s" % ("PASS" if ok else "FAIL", name, got, why))
    print("=" * 78)
    print("%d/%d fixtures passed" % (len(FIXTURES) - failures, len(FIXTURES)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())