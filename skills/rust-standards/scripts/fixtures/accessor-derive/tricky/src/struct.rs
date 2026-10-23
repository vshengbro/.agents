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

/// RULE 2 exemption: a `cfg_attr` decides whether the skips exist, so the
/// unconditional shape cannot be proven and the struct is left alone.
/// EVERY field is getter-only shaped — without the exemption this struct
/// would be reported, which is what makes the fixture load-bearing.
#[derive(Clone, Debug, Data)]
pub struct TrickyCfgAttr {
    /// Always getter-only.
    #[get(pub(crate))]
    #[get_mut(skip)]
    #[set(skip)]
    pub(crate) name: String,
    /// Its mutator appears only under a feature flag.
    #[get(pub(crate))]
    #[cfg_attr(feature = "extra", get_mut(pub(crate)))]
    #[get_mut(skip)]
    #[set(skip)]
    pub(crate) other: String,
}

/// RULE 2 exemption: plain `cfg` on the field means the accessor set is
/// conditional even without `cfg_attr`. Again every field is getter-only
/// shaped, so only the exemption keeps this quiet.
#[derive(Clone, Debug, Data)]
pub struct TrickyCfgField {
    /// Always getter-only.
    #[get(pub(crate))]
    #[get_mut(skip)]
    #[set(skip)]
    pub(crate) name: String,
    /// Only present on wasm.
    #[cfg(target_arch = "wasm32")]
    #[get(pub(crate))]
    #[get_mut(skip)]
    #[set(skip)]
    pub(crate) other: String,
}

/// RULE 2 exemption: one field skips only half of the pair, so a mutator
/// still exists. Partial skips are the common real-world case.
#[derive(Clone, Debug, Data)]
pub struct TrickyPartialSkip {
    /// Still settable.
    #[get(pub(crate))]
    #[get_mut(skip)]
    pub(crate) name: String,
    /// Read-only.
    #[get(pub(crate))]
    #[get_mut(skip)]
    #[set(skip)]
    pub(crate) other: String,
}

/// RULE 2 exemption: `type(...)` config mentioning a `skip`-named type must
/// not be read as `#[set(skip)]` — the inner group is stripped first.
#[derive(Clone, Debug, Data)]
pub struct TrickySkipInsideType {
    /// A conversion whose target type is named `skip`.
    #[get(pub(crate))]
    #[get_mut(skip)]
    #[set(type(skip))]
    pub(crate) name: String,
}
