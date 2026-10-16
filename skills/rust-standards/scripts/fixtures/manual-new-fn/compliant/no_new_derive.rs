// COMPLIANT: no `New` derive, so a hand-written constructor is not this rule's
// business — `New` would demand every field as a parameter.
pub struct Plain {
    a: u32,
    b: String,
}

impl Plain {
    pub fn new(a: u32) -> Self {
        Self {
            a,
            b: String::new(),
        }
    }
}
