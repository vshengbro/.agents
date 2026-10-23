use super::*;

/// Accessors come from `Data`, which is the trio.
#[derive(Clone, CustomDebug, Data, DisplayDebug)]
pub struct CompliantOne {
    /// Public field.
    pub name: String,
}

/// Two derives with no combined macro stay as they are.
#[derive(Clone, Debug, Getter, Setter)]
pub struct CompliantPair {
    /// Public field.
    pub count: u32,
}

/// `GetterMut + Setter` has no combined derive either.
#[derive(Clone, Debug, GetterMut, Setter)]
pub struct CompliantOtherPair {
    /// Public field.
    pub count: u32,
}

/// A lone `Getter` is not the trio.
#[derive(Clone, Debug, Getter)]
pub struct CompliantOnly {
    /// Public field.
    pub name: String,
}

/// A path-qualified `Data` still counts as `Data`.
#[derive(Clone, Debug, lombok_macros::Data)]
pub struct CompliantQualified {
    /// Public field.
    pub name: String,
}

/// A doc comment that spells out the trio is prose, not a derive list.
///
///     #[derive(Clone, Getter, GetterMut, Setter)]
///     pub struct Documented { pub name: String }
///
#[derive(Clone, Debug, Data)]
pub struct CompliantDocumented {
    /// Public field.
    pub name: String,
}

/// A raw string holding sample code must not be read as a derive list.
#[derive(Clone, Debug, Data)]
pub struct CompliantRawString {
    /// Sample text.
    pub sample: &'static str,
}

/// RULE 2 (§17.16.1), already-fixed shape: `Getter` with the mutator
/// attributes removed. Nothing to report.
#[derive(Clone, Debug, Getter)]
pub struct GetterOnlyFixed {
    /// Surface width in pixels.
    #[get(pub(crate), type(copy))]
    pub(crate) width: u32,
    /// The immutable backend identity.
    #[get(pub(crate))]
    pub(crate) backend: RayTraceBackend,
}

/// A `Data` struct that still generates a setter for one field is genuinely
/// `Data`, however few call sites use it. No call-site counting here.
#[derive(Clone, Debug, Data)]
pub struct DataStillSettable {
    /// Written by the builder.
    #[get(pub(crate))]
    #[get_mut(pub(crate))]
    #[set(pub(crate))]
    pub(crate) value: u32,
}

/// A `Data` struct that still generates one `get_mut` stays `Data`.
#[derive(Clone, Debug, Data)]
pub struct DataStillMutable {
    /// Written by the backend.
    #[get(skip)]
    #[get_mut(pub(crate))]
    #[set(pub(crate))]
    pub(crate) adapter: RayTraceBackendAdapter,
}

/// Every field skips `get` too, so no accessor is generated at all and
/// `Getter` would not describe this struct either.
#[derive(Clone, Debug, Data)]
pub struct DataNoAccessorsAtAll {
    /// Never exposed.
    #[get(skip)]
    #[get_mut(skip)]
    #[set(skip)]
    pub(crate) secret: u32,
}

/// An empty `Data` struct has no field to read a skip off.
#[derive(Clone, Debug, Data)]
pub struct DataEmpty {}

/// Tuple and unit structs have no named field to anchor a skip to.
#[derive(Clone, Debug, Data)]
pub struct DataTuple(pub(crate) u32);

/// `Getter` on its own is the fixed form of rule 2 — never reported.
#[derive(Clone, Debug, Getter)]
pub struct PlainGetter {
    /// Public field.
    pub name: String,
}
