use lombok_macros::New;

#[derive(Clone, Debug, New)]
pub struct Config {
    host: String,
    port: u16,
}

impl Config {
    pub fn new(host: String) -> Self {
        Self { host, port: 8080 }
    }
}
