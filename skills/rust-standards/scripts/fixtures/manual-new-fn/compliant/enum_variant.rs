use lombok_macros::New;

// COMPLIANT: `New` decorates a STRUCT here; the enum's own `new` is a
// constructor over variants, which is a different shape entirely.
#[derive(Clone, Debug, New)]
pub struct Marker {
    tag: String,
}

pub enum Shape {
    Circle(u32),
    Square(u32),
}

impl Shape {
    pub fn new(circle: u32) -> Self {
        Self::Circle(circle)
    }
}
