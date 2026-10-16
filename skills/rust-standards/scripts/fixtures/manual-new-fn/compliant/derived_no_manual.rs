use lombok_macros::{Data, New};

// COMPLIANT: `New` derives the constructor; nothing is hand-written.
#[derive(Clone, Debug, Data, New)]
pub struct User {
    name: String,
    email: String,
}

// A different type's manual `new` in the same file must not be attributed to
// `User` — the impl target has to match the New-derived struct's name.
#[derive(Clone, Debug)]
pub struct Session {
    id: u32,
}

impl Session {
    pub fn new(id: u32) -> Self {
        Self { id }
    }
}
