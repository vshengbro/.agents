use super::*;

/// The full trio spelled out: `Data` does exactly this.
#[derive(Clone, CustomDebug, DisplayDebug, Getter, GetterMut, Setter)]
pub struct TrioPlain {
    /// Route map.
    pub(super) static_route: String,
}

/// The trio in a different order is the same redundancy.
#[derive(Setter, GetterMut, Getter, Clone)]
pub struct TrioReordered {
    /// Public field.
    pub name: String,
}

/// Path-qualified trio: `lombok_macros::Data` replaces all three.
#[derive(Clone, Debug, lombok_macros::Getter, lombok_macros::GetterMut, lombok_macros::Setter)]
pub struct TrioQualified {
    /// Public field.
    pub name: String,
}

/// The trio listed next to `Data` is the same redundancy from the other
/// side, and it does not even compile (duplicate methods).
#[derive(Clone, Debug, Data, Getter, GetterMut, Setter)]
pub struct TrioWithData {
    /// Public field.
    pub name: String,
}
