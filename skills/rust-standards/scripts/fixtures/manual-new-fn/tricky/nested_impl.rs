use lombok_macros::New;

// COMPLIANT: `New`-derived, and the only `fn new` in this file belongs to an
// UNRELATED type further down. The impl scan is scoped to each impl target's
// own braces, so `Unrelated::new` must NOT be attributed to `Inner`.
#[derive(Clone, Debug, New)]
pub struct Inner {
    value: u32,
}

// A method that is not `new` on a New-derived struct — not this rule's business.
impl Inner {
    pub fn with_zero() -> Self {
        Self { value: 0 }
    }
}

pub struct Unrelated;

impl Unrelated {
    pub fn new() -> Self {
        Self
    }
}
