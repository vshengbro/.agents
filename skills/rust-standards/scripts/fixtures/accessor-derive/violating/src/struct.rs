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

/// RULE 2 (§17.16.1): every field skips both mutators, so `Data` promises
/// `get_mut_*` / `set_*` that no field ever generates.
#[derive(Clone, Debug, Data)]
pub struct DataWithoutMutators {
    /// Surface width in pixels.
    #[get(pub(crate), type(copy))]
    #[get_mut(skip)]
    #[set(skip)]
    pub(crate) width: u32,
    /// The immutable backend identity.
    #[get(pub(crate))]
    #[get_mut(skip)]
    #[set(skip)]
    pub(crate) backend: RayTraceBackend,
    /// A generic type with commas and nesting must stay ONE field.
    #[get(pub(crate), type(copy))]
    #[get_mut(skip)]
    #[set(skip)]
    pub(crate) table: HashMap<String, Vec<u32>>,
}

/// RULE 2: one getter, and a multi-line attribute run above the field.
#[derive(Clone, Debug, Data)]
pub struct DataWithoutMutatorsMultiLine {
    /// A single field with the skips spelled across lines.
    #[get(
        pub(crate),
        type(copy)
    )]
    #[get_mut(skip)]
    #[set(skip)]
    pub(crate) count: u32,
}
