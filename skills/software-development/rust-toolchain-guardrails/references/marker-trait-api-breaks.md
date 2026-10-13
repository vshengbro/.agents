# 大版本用 marker trait 收窄参数类型时的断裂

适用于:依赖升级后,编译器报一屏 `E0277`,而错误文案**讲的不是类型不匹配、是某种策略
或约定**(安全 / 注入 / 生命周期 / 编码)。

## 1. 识别:文案在讲策略 = 不是漏洞,是 trait 实现面变了

普通 trait 不满足的文案长这样:

```
the trait bound `Foo: Bar` is not satisfied
```

marker trait 的文案**指向一个策略名词**,容易把人带进安全排查的死胡同:

```
error[E0277]: dynamic SQL strings should be audited for possible injections:
              dynamic SQL string
```

看到这种文案,**立刻停止找漏洞**。上游做的事是:把这个参数的合法类型从「任何能转成
SQL 的东西」收窄成「一个显式声明白名单」,并且只给白名单里的类型实现新 trait。旧代码
按老约定写的调用点集体炸掉,和它们的数据是否真的不安全无关。

## 2. 诊断:一次拿到当前版本的「接受面」

不要读迁移指南(指南讲新特性,不列「哪些类型仍然被接受」)。直接 grep registry 源码里
这个 trait 的全部 `impl` —— 那就是完整白名单。

```bash
find ~/Library/Caches/cargo-home/registry/src -maxdepth 2 -name "<crate>-<新版本>"
grep -rn "impl .*SqlSafeStr for \|impl .*TraitName for " <该路径>/src/
```

典型输出的三种形态,对应三种修法:

| impl 形态 | 含义 | 修法 |
|-----------|------|------|
| `impl T for &'static str` 单独一行,另有 `pub struct OptIn<T>(pub T)` 且 `impl T for OptIn<&str> / String / Box<str> / Arc<str> / Cow` | 白名单 = static + 官方 opt-in 包装 | 用包装类型(§3) |
| 只有 `impl T for &'static str` 一个 | 白名单极窄 | 走 §4,考虑重写调用点 |
| `impl T for A` + `impl T for B` 若干普通类型 | 白名单就是这几个 | 直接改调用点的类型 |
| 泛型 impl,如 `impl<T: Encode<DB>> T for Marker<DB>` | 需要具体化类型参数 | 按签名补 turbofish 或局部标注 |

**同时确认这个 trait 的名字在哪导出**(`pub use sqlx_core::sql_str::{AssertSqlSafe, ...}`),
否则包装类型和 trait 同名不同 namespace,会写出 `AssertSqlSafe::AssertSqlSafe` 这类东西。

## 3. 逃生舱:opt-in 包装类型 vs `leak` vs 改写成 bind 参数

上游给了 opt-in 包装类型时,**三个选项按这个顺序考虑**:

### 3a. 包装类型(默认选它)

- **前提条件:被插值进字符串的每个表达式,来源都可枚举且都不含用户输入。** const、
  配置项、编译器生成的值、内部计数器 —— 这些可以包。
- **必须把枚举结论写进汇报**,而不是只说「加了个 wrapper」。审阅者需要看到「哪些值被
  插进去了」的清单才能判断这个 wrapper 是否诚实。
- 同一次调用里如果既有 const 插值又有请求参数,整条语句都不该包,走 3c。

### 3b. `String::leak()` —— 永远不要用

`&'static str` 是原生实现时,`format!(...).leak()` 确实能骗过编译器。但那是用**常驻
内存泄漏**换一个编译期约束:一次启动一次建表 = 泄漏一小块,看似无害;但同样的写法
复制到请求路径上就是每请求泄漏一段 SQL 字符串。**编译错误只是要你把这件事说清楚,
不是要你绕过它。**

### 3c. 改写成 bind 参数(最正确,但成本最高)

当被插值的值**真的**含用户输入,或者整条语句的值列表是动态生成的(`INSERT INTO ...
VALUES ...` 拼 N 个元组),bind 参数是唯一正解。注意:bind 参数要求语句能走 prepared
statement 路径,无法给部分动态片段(表名、列名、`LIMIT` 之后的东西)做绑定。

## 4. 最小修复 vs 重写:先绿,再谈好看

升级任务里出现断裂时,先问一句:**这次任务的验收标准是「构建绿」还是「顺便改好」?**

默认是前者。判据:

- 重写会改变**运行时行为**(执行计划、参数编码、错误类型),而你**多半没有可运行环境**
  去验证它 —— 初始化 / 迁移 / 数据灌装路径常常在 `#[cfg(feature = ...)]` 后面,本地
  连库都没有。
- 重写的正确形态是**第二个 commit**,且第一个 commit 必须已经绿。

如果你写了一版重写又退回来了,说明在做第三件事,收手。

## 5. 收尾验证

```bash
cargo check --all-features            # cfg 分支能编译
cargo clippy --all-features --all-targets   # 0 warning
cargo fmt --check                    # 0 diff
bash scripts/audit_baseline_diff.sh <repo> <改动的文件>   # 零新增违规
```

**汇报里显式区分「编译通过」与「运行验证」。** 上面四条全部只证明前者。`--all-features`
让 `#[cfg(feature = "dev")]` 里的语句编进去了,不代表它对着真库跑过 —— 这一句不写,
等于把 compile-green 交付成 run-green。