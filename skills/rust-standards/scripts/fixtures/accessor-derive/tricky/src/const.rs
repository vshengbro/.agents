use super::*;

/// A raw string whose contents spell out the trio.
pub(crate) const SAMPLE: &str = r#"
#[derive(Clone, Getter, GetterMut, Setter)]
pub struct InsideRawString {
    pub name: String,
}
"#;

/// A raw string holding a struct that BOTH rules would otherwise report, so
/// rule 2's field-scan is exercised against a string body too.
pub(crate) const GETTER_ONLY_SAMPLE: &str = r##"
#[derive(Clone, Debug, Data)]
pub struct InsideRawStringTwo {
    #[get(pub(crate))]
    #[get_mut(skip)]
    #[set(skip)]
    pub(crate) name: String,
}
"##;

/// A byte string with an escaped quote, then the trio after it — the escape
/// must not end the literal early.
pub(crate) const ESCAPED: &[u8] = b"#[derive(Clone, Getter, GetterMut, Setter)]";

/* A block comment whose contents spell out the trio:
   #[derive(Clone, Getter, GetterMut, Setter)]
   pub struct InsideBlockComment { pub name: String }
*/
pub(crate) const PLACEHOLDER: u8 = 0;
