# Upstream provenance

These skills are vendored from [MiniMax-AI/skills](https://github.com/MiniMax-AI/skills.git),
directory `skills/`.

- upstream commit: `60aaae52bb2af8162732751a4332f62a5fef518b`
- upstream ref: `main`
- last sync: 2026-10-28

Refresh with:

```shell
bash scripts/sync-minimax-skills.sh --ref main
bash scripts/sync-minimax-skills.sh --check
```

Do not hand-edit the vendored skill folders: the next sync overwrites them.
Local edits belong in a separate skill.

## Not vendored

- `android-native-dev` — this library already carries a curated, narrowed
  version of the same upstream skill under `skills/android-native-dev/`.
  Skill names must be unique across the library, so the upstream copy is
  skipped here.
- `buddy-sings`, `flutter-dev`, `gif-sticker-maker`, `minimax-docx`,
  `minimax-music-gen`, `minimax-music-playlist`, `minimax-xlsx`,
  `pptx-generator`, `react-native-dev` — removed 2026-11-27 after a
  cross-profile usage audit showed zero recorded uses; listed in
  `SKIP_SKILLS` so a sync does not restore them.

## Licensing

The upstream repository is MIT licensed; its `LICENSE`, `LICENSES/` and
`CREDITS.md` are vendored alongside the skills. Some upstream skills
derive from Apache-2.0 licensed sources credited in `CREDITS.md`.
