use lombok_macros::{Data, New};

// VIOLATION: New-derived struct with a hand-written `new` that also forces
// `email` as a parameter, which `#[new(skip)]` exists to avoid.
#[derive(Clone, Debug, Data, New)]
pub struct User {
    name: String,
    email: String,
}

impl User {
    pub fn new(name: String) -> Self {
        Self {
            name,
            email: String::new(),
        }
    }
}
