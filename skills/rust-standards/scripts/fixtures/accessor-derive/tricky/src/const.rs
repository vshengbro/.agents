use super::*;

/// A raw string whose contents spell out the trio.
pub(crate) const SAMPLE: &str = r#"
#[derive(Clone, Getter, GetterMut, Setter)]
pub struct InsideRawString {
    pub name: String,
}
"#;

/* A block comment whose contents spell out the trio:
   #[derive(Clone, Getter, GetterMut, Setter)]
   pub struct InsideBlockComment { pub name: String }
*/
pub(crate) const PLACEHOLDER: u8 = 0;
