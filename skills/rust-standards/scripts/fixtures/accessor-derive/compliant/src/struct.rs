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
