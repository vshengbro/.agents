# Upstream provenance

Vendored from [google/agents-cli](https://github.com/google/agents-cli.git), directory `skills/`.

- upstream commit: `2fa159a803aceec3b4df808901e53a08a6f1fb2a`
- upstream ref: `main` (release v1.15.0)

These seven skills were installed by `agents-cli setup` (the CLI's own skill
installer). Every file is **byte-identical to upstream** — verified file by
file against a fresh clone of the upstream `skills/` directory. The upstream
`skills/README.md` is not part of the installed set.

The installer writes each skill flat at `skills/<skill-name>/`, so unlike the
other vendored trees in this repo (`minimax-skills/`, `blender-skills/`,
`mcode-stack/`) they cannot be grouped under one parent folder without
breaking the registered skill paths in `.skill-lock.json` and the Hermes skill
index. They are therefore listed individually in `DEFAULT_VENDORED_PREFIXES` in
`scripts/audit_skills.py`.

Upstream text is not ours to rewrite, so `audit_skills.py` waives the
description-length and keyword-dump budgets, the entry line budget and the
relative-link / anchor checks for this subtree. Frontmatter shape, name/folder
match and global name uniqueness still apply.

To refresh, re-run the installer and re-verify against upstream:

```shell
agents-cli setup
git clone --depth 1 --filter=blob:none --sparse https://github.com/google/agents-cli.git /tmp/gac
cd /tmp/gac && git sparse-checkout set skills
diff -r /tmp/gac/skills ~/.agents/skills
```

Do not hand-edit these skills; the next install replaces them.
