use lombok_macros::New;

// COMPLIANT: every `fn new` and `#[derive(..)]` below is inside a comment or a
// string literal, so it must not be read as code.
#[derive(Clone, Debug, Data, New)]
pub struct Real {
    field: String,
}

const SAMPLE: &str = r#"
impl Real {
    pub fn new(field: String) -> Self { Self { field } }
}
"#;

/*
impl Real {
    pub fn new(field: String) -> Self { Self { field } }
}
*/

// doc comment mentioning it: /// see `fn new` and #[derive(New)]
pub fn unrelated() -> u8 {
    7
}
