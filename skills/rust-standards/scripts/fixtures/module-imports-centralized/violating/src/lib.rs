//! §6.1 fixture: private root `use` is compliant (reaches descendants);
//! this crate still exits 1 through the §6.2/§6.3 violations in siblings.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use self::inner::Helper;
use super::other::Thing;

pub mod inner;
