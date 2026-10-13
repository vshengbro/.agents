# Triage: a lint firing inside a macro DSL

Worked example from the `euv` repo (`html!` macro, `macros/src/html/`). Load
when a warning fires on an `html!` invocation, or when changing that parser.

## The case

`unused_braces: unnecessary braces around function argument` on:

```rust
div {
    class: { CLASS_FEATURE_CARD_ICON }
    {
        feature.icon
    }
}
```

Two plausible readings, opposite conclusions:

- **False positive.** The macro DSL needs the braces; rustc sees a block
  wrapping a lone argument. Report it, do not suppress, do not let
  `cargo clippy --fix` strip them (that yields `error: expected ,` at the
  *next* field).
- **Design defect.** The framework intends braces for *dynamic* values only. A
  static constant is not dynamic, so being forced into braces is the macro
  being wrong. Fix the parser, then drop the braces at the call sites.

Empirically the second was right, and the user's framing is the tell: a
workaround that many call sites must adopt is not a lint being inconvenient, it
is the macro charging admission for a construct it should accept.

## Why the bare form failed

`parse_attr_value` called `content.parse()` for the value. `syn` then read
`CLASS_FEATURE_CARD_ICON { feature.icon }` as a struct literal and swallowed the
child. The neighbouring constructs did not have this problem because they used
`parse_expr_until_brace`, which stops at a body brace.

## The fix, and the trap on the way

Do **not** just swap in `parse_expr_until_brace`. In an attribute list the
delimiter is the next `key:` or the element's closing brace — not a body brace —
so the helper runs past a call's closing paren:

```rust
class: c_error_box()     // helper keeps consuming; children get eaten
```

That broke ~115 call sites. The attribute list needs its own disambiguator.

The one that works peeks *inside* the brace group:

```rust
// a struct literal's braces must start with a field initialiser (`ident :`),
// which can never be a child expression; a child block holds a plain expr
if content.peek(Ident) && content.peek2(Brace) {
    let forked: ParseBuffer<'_> = content.fork();
    let _probe: Ident = forked.parse()?;
    let inner: ParseBuffer<'_>;
    braced!(inner in forked);
    let is_struct_literal: bool = inner.peek(Ident) && inner.peek2(Colon);
    if !is_struct_literal {
        let ident: Ident = content.parse()?;
        return Ok(HtmlAttrValue::Expr(Expr::Path(syn::ExprPath {
            attrs: vec![], qself: None, path: syn::Path::from(ident),
        })));
    }
}
```

Separately, unwrap a single-expression block *after* parsing so the braces
never reach codegen — reuse the existing `strip_braces_from_expr` (already
present for `if` conditions) rather than adding a near-identical helper.

## The test that compilation could not give

No attribute in the repo passed a struct literal, so that path was untested by
construction: it compiles green whether or not you broke it. Three cases were
needed, and none were optional:

| Case | Guards |
|---|---|
| bare const + `{ }` child | the newly supported form |
| braced const + `{ }` child | the form must still parse (additive, not breaking) |
| struct literal as an attribute | the path with no existing caller |
| call expression + `{ }` child | not mistaken for bare path + child |

## Lesson to carry forward

Two failures in sequence, both mine: first treating a design defect as a lint
false positive, then reaching for an existing helper without reading its
contract. The parser's *intent* was discoverable from the fact that
`if`/`for`/`match` already solved the same ambiguity — the gap was that nobody
applied it to attributes.
