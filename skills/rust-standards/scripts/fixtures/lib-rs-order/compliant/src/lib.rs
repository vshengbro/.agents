//! §6.1-compliant: mod -> #[cfg(test)] mod -> pub use local -> pub use external -> pub(crate) -> private.

mod first;
mod second;

#[cfg(test)]
#[path = "../tests/mod.rs"]
mod tests;

pub use {first::*, second::*};

pub use {external_a::*, external_b::*};

pub(crate) use crate::Widget;

use std::collections::HashMap;

use {clap::Parser, log::SetLoggerError, serde::Serialize};
