# hyperlane-cli complete pub API

Source: `cli/src/` — auto-extracted from `pub` declarations.

**Note**: `hyperlane-cli` provides six subcommands — `watch / new / template /
fmt / help / version` — plus the `-h`/`--help` and `-v`/`--version` flags.
`bump / sync / publish` come from the external `crate-cli`. The `fmt`
sub-command (added in `9e5b0fc`) is the `hyperlane fmt` entry point: it takes
`--check` and `--path <PATH>`, and it delegates to `crate_cli::execute_unified_fmt`
before applying Hyperlane attribute normalization. See
[SKILL.md](../SKILL.md) §Mandatory Standards item 4.

### `command::enum`

- `enum` **`CommandType`** — `pub enum CommandType {`

### `fmt::fn`

- `fn` **`execute_fmt`** — `pub async fn execute_fmt(target_root: &Path, check: bool) -> io::Result<HyperlaneFmtReport> {...}`
- `fn` **`format_hyperlane_attributes_in_source`** — `pub fn format_hyperlane_attributes_in_source(source: &str) -> (String, usize) {...}`
- `fn` **`format_hyperlane_attributes_in_workspace`** — `pub fn format_hyperlane_attributes_in_workspace( root: &Path, check: bool, ) -> io::Result<(usize, Vec<String>)> {...}`

### `fmt::struct`

- `struct` **`HyperlaneFmtReport`** — `pub struct HyperlaneFmtReport {`

### `config::fn`

- `fn` **`parse_args`** — `pub fn parse_args() -> Args {...}`
- `fn` **`parse_args_from`** — `pub fn parse_args_from(raw_args: &[String]) -> Args {...}`

### `config::struct`

- `struct` **`Args`** — `pub struct Args {`

### `help::fn`

- `fn` **`print_help`** — `pub fn print_help() {...}`

### `logger::impl`

- `fn` **`init`** — `pub fn init(level_filter: log::LevelFilter) {...}`

### `logger::static`

- `static` **`LOGGER`** — `pub(crate) static LOGGER: Logger = Logger;`

### `logger::struct`

- `struct` **`Logger`** — `pub struct Logger;`

### `new::enum`

- `enum` **`NewError`** — `pub enum NewError {`

### `new::fn`

- `fn` **`execute_new`** — `pub async fn execute_new(project_name: &str) -> Result<(), NewError> {...}`

### `new::impl`

- `fn` **`new`** — `pub fn new(project_name: String) -> Self {...}`

### `new::struct`

- `struct` **`NewProjectConfig`** — `pub struct NewProjectConfig {`

### `template::enum`

- `enum` **`TemplateType`** — `pub enum TemplateType {`
- `enum` **`ModelSubType`** — `pub enum ModelSubType {`
- `enum` **`TemplateError`** — `pub enum TemplateError {`

### `template::fn`

- `fn` **`execute_template`** — `pub async fn execute_template( template_type: TemplateType, component_name: &str, model_sub_type: Option<ModelSubType>, ) -> Result<(), TemplateError> {...}`

### `template::impl`

- `fn` **`new`** — `pub fn new( template_type: TemplateType, component_name: String, model_sub_type: Option<ModelSubType>, ) -> Self {...}`

### `template::struct`

- `struct` **`TemplateConfig`** — `pub struct TemplateConfig {`

### `version::fn`

- `fn` **`print_version`** — `pub fn print_version() {...}`

### `watch::fn`

- `fn` **`execute_watch`** — `pub async fn execute_watch() -> Result<(), io::Error> {...}`
