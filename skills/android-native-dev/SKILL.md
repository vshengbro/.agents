---
name: android-native-dev
description: "Use when building or debugging an Android native app: Gradle build failures, Kotlin/Compose, unit and instrumentation tests. 安卓 原生 Android 应用构建与 Gradle 测试。"
license: MIT
metadata:
  version: "1.1.0"
  category: mobile
---

# Android Native Dev

Entry point for Android native work: **Kotlin / Jetpack Compose / Gradle build and
tests**, plus UI-compliance review. Design specs, test code, and platform
reference tables live in `references/` — load the one the task needs.
## Index

§1 Toolchain gate (run before writing any Kotlin) · §2 Baseline build before business logic · §3 Kotlin rules that prevent real crashes · §4 Compose essentials · §5 Resources and icons · §6 Build-error triage · §7 Tests — only when the user asks for them · §8 Reference router · §9 Resources you spawn


## When NOT to use

- React Native / Flutter / Cordova — this skill assumes native Gradle modules.
- Desktop or backend Kotlin/JVM with no Android plugin.

## 1. Toolchain gate (run before writing any Kotlin)

```bash
java -version                 # JDK 17+ for AGP 8.x; older JDKs fail at configure time
./gradlew --version           # wrapper prints Gradle + AGP; if no wrapper:
gradle wrapper                # one-off, only when the project ships none
```

**Done when:** `./gradlew --version` prints a Gradle + AGP pair. No SDK path
means `ANDROID_HOME`/`local.properties` is missing — fix that, not the code.

## 2. Baseline build before business logic

```bash
./gradlew assembleDebug       # the gate: green before adding features
./gradlew tasks --group=build # list real variant names when flavors exist
./gradlew :app:dependencies   # resolve Duplicate class / version conflicts
./gradlew assembleDebug --stacktrace
./gradlew --refresh-dependencies   # last resort only
```

The minimum project shape, the `gradle.properties` baseline, and the two
AGP 8+ traps that look like missing code are in
[references/project-shape-and-gradle-properties.md](references/project-shape-and-gradle-properties.md).

## 3. Kotlin rules that prevent real crashes

| Rule | Wrong | Right |
|---|---|---|
| No force-unwrap on anything remote | `user!!.name` | `user?.name ?: "Unknown"` |
| Network/model fields are nullable | `val id: String = ""` | `val id: String? = null` |
| No uninitialized `lateinit` read | `lateinit var d: String` | `var d: String? = null` |
| `return` inside a lambda is non-local | `forEach { if (it.isEmpty()) return }` | `return@forEach` |
| Exceptions propagate, don't vanish | `catch (e: Exception) {}` | `runCatching { … }.onFailure { … }` |
| Observers are removed symmetrically | add in `onAttachedToWindow` | also remove in `onDetachedFromWindow` |

Dispatchers: UI + state → `Main`; network, disk, DB → `IO`; CPU-bound parse/encrypt
→ `Default`. A `suspend fun` in a repository should switch itself, so callers stay
main-safe. Never mutate UI state from `launch(Dispatchers.IO)`, and never block
`Main` (that is the ANR).

Log with intent: `i` checkpoints, `w` recoverable fallbacks, `e` real failures.

## 4. Compose essentials

- A composable body may only be called from another `@Composable`; suspend work
  belongs in `LaunchedEffect`, never in the body.
- Never construct a ViewModel inside a composable — take
  `viewModel: MyViewModel = viewModel()` as a parameter.
- `remember` survives recomposition; `derivedStateOf` for derived booleans.
- ViewModel holds `MutableStateFlow` private, exposes `asStateFlow()`.

## 5. Resources and icons

Prefix everything (`ic_`, `bg_`, `color_`) and never name a resource after an
Android system name (`background`, `icon`, `text`, `view`, `theme`, `app`) — it
collides at build time.

Adaptive icon (the `xmlns:android` declaration is required or AAPT fails):

```xml
<!-- res/mipmap-anydpi-v26/ic_launcher.xml -->
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
```

Keep legacy PNG fallbacks in `mipmap-*` for pre-API-26 devices.

## 6. Build-error triage

| Message | Cause | Action |
|---|---|---|
| `Unresolved reference` | missing import or dependency | check import, then `:app:dependencies` |
| `Cannot access …` | visibility | check `private`/`internal`, data-class fields crossing modules |
| `Duplicate class` | two artifacts on one path | `:app:dependencies`, force one version |
| `AAPT: error` | malformed XML/resource | re-read the file; reserved resource name is a common cause |
| `@Composable invocations` | called from a non-composable | annotate the caller |
| `OutOfMemoryError` during build | too little heap | raise `org.gradle.jvmargs` |

## 7. Tests — only when the user asks for them

```bash
./gradlew test                        # all modules, JVM only
./gradlew :app:testDebugUnitTest --tests "com.example.myapp.CounterViewModelTest"
./gradlew connectedDebugAndroidTest   # needs a real device/emulator
./gradlew pixel6Api34DebugAndroidTest # Gradle managed device (defined in build.gradle.kts)
./gradlew testDebugUnitTest jacocoTestReport
```

Before adding a test dependency, match the project's existing versions:
`kotlinx-coroutines-test` ↔ `kotlinx-coroutines-core`, `ui-test-junit4` ↔ the
Compose BOM, `mockk` ↔ the Kotlin version. Robolectric additionally needs
`android { testOptions { unitTests.isIncludeAndroidResources = true } }`.
Full patterns: `references/testing.md`.

## 8. Reference router

| Question | File |
|---|---|
| Colors, type scale, spacing, touch targets | `references/visual-design.md` |
| Style for this app category | `references/design-style-guide.md` |
| Durations, easing, transitions | `references/motion-system.md` |
| Labels, focus, TalkBack | `references/accessibility.md` |
| Foldables, tablets, configuration changes | `references/adaptive-screens.md` |
| Vitals, startup, ANR, memory | `references/performance-stability.md` |
| Permissions, storage, network security | `references/privacy-security.md` |
| Audio, video, notifications | `references/functional-requirements.md` |
| Test code and managed devices | `references/testing.md` |

Load exactly the rows the task needs — every one of these is a spec sheet, not
a workflow.

## 9. Resources you spawn

Gradle daemons, emulators/managed devices, and profiler sessions are
task-created resources: register them, then on success, failure, timeout, or
cancel stop them explicitly (`./gradlew --stop`; `adb emu kill` for an emulator
you launched; close profilers). Never kill by name and never touch a daemon or
device that predates the task.
