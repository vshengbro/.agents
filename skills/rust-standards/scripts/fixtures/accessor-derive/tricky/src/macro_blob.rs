use super::*;

/// A struct-shaped token blob inside a function-like macro invocation is
/// NOT an item: no proc-macro derive ever reaches it, so both rules stay
/// silent. `macro_rules!` is the deliberate contrast — its transcriber holds
/// real items and IS checked (see the end of this file).
const _: () = {
    let _ = build_all! {
        #[derive(Clone, Debug, Data)]
        pub struct Ghost {
            #[get(pub(crate))]
            #[get_mut(skip)]
            #[set(skip)]
            pub(crate) name: String,
        }
    };
    let _ = tuple_all![
        #[derive(Clone, Getter, GetterMut, Setter)]
        pub struct GhostTuple { pub name: String }
    ];
    let _ = brace_all! {
        #[derive(Clone, Debug, Data)]
        pub struct GhostBrace {
            #[get(pub(crate))]
            #[get_mut(skip)]
            #[set(skip)]
            pub(crate) name: String,
        }
    };
};

/// The raw IDENTIFIER `r#type` is code, not a raw string. Its field keeps a
/// live setter, so the scanner must read PAST the identifier and stay silent
/// — if `r#` were mistaken for a raw-string opener, this struct's field
/// attributes would go unread and it would be reported.
#[derive(Clone, Debug, Data)]
pub struct TrickyRawIdentifier {
    /// A field named with a raw identifier.
    #[get(pub(crate))]
    #[get_mut(pub(crate))]
    #[set(pub(crate))]
    pub(crate) r#type: u32,
}

/// A `//` comment holding the getter-only shape, plus a nested block comment
/// holding the trio. Neither is code.
#[derive(Clone, Debug, Data)]
pub struct TrickyCommentedShape {
    // #[get_mut(skip)]
    // #[set(skip)]
    /* #[derive(Clone, Getter, GetterMut, Setter)] */
    /* outer /* #[get(skip)] */ */
    #[get(pub(crate))]
    #[get_mut(pub(crate))]
    #[set(pub(crate))]
    pub(crate) name: String,
}

/// `macro_rules!` bodies compile, so a real struct in there is real. This one
/// keeps a live setter, so both rules stay silent — the fixture proves the
/// scanner does not blanket-skip macro bodies.
macro_rules! define_config {
    ($name:ident) => {
        #[derive(Clone, Debug, Data)]
        pub struct $name {
            #[get(pub(crate))]
            #[get_mut(pub(crate))]
            #[set(pub(crate))]
            pub(crate) name: String,
        }
    };
}
