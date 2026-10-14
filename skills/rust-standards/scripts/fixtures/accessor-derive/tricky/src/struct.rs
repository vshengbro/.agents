use super::*;

/// An enum carrying the trio: the generator rejects enums outright
/// (`_ => panic!(UNSUPPORTED_DATA_DERIVE)`), so the rule is struct-scoped
/// and stays silent here.
#[derive(Clone, Copy, Debug, Eq, Getter, GetterMut, PartialEq, Setter)]
pub enum TrickyEnum {
    /// First variant.
    First,
}

/// Two derives where the third name only appears inside another macro's
/// path segment: `lombok_macros::Getter` alone is not the trio.
#[derive(Clone, Debug, lombok_macros::Getter)]
pub struct TrickySingleQualified {
    /// Public field.
    pub name: String,
}

/// A trait is not decorated by accessor derives at all.
#[derive(Clone, Debug, Data)]
pub struct TrickyDeriveOnStruct {
    /// Public field.
    pub name: String,
}
