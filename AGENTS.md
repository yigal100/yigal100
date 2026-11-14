# AGENTS.md

## Repository: yigal100 (GitHub Profile Console)

### 1. Vision & Core Objective

This repository powers the personal GitHub profile (`yigal100/yigal100`) for **Yigal Chripun**.
It features a self-contained cyberpunk console aesthetic rendered into dynamic SVGs and scheduled updates via GitHub Actions:

- Live GitHub contribution activity and stats.
- Featured project showcase (`second-brain`, `photon`, `quartz`, `yigal100`).
- Modular tech stack matrix and writing highlights.
- Deterministic font subsetting (JetBrains Mono) embedded directly in vector assets.

---

### 2. Standards & Repository Conventions

We strictly adhere to open, vendor-neutral standards:

- **Agent Instructions**: This `AGENTS.md` is the primary source of truth for agent behavior and repository rules. Avoid vendor-specific configuration formats unless strictly required.
- **Agent Skills**: Reusable agent capabilities and tools reside in `.agents/skills/` following open skill formats.
- **Task & Tooling Management**: Use `mise` (`.mise/config.toml`) for managing project tasks, tools (`git-cliff`, `markdownlint-cli2`), and local overrides (`.mise/config.local.toml`).
- **Markdown Standards**: Strictly adhere to markdown standards across all markdown files (blank lines surrounding headings, lists, and code fences; explicit language tags on fenced code blocks; no trailing spaces; single trailing newline).
- **Commit Messages**: Strictly follow the [Conventional Commits](https://www.conventionalcommits.org/) specification (`<type>[optional scope]: <description>`) for all git commit messages (e.g., `feat`, `fix`, `docs`, `refactor`, `test`, `chore`).

---

### 3. Repository Structure

```text
yigal100/
├── .github/
│   └── workflows/
│       └── update-profile.yml  # Daily GitHub Actions workflow
├── .agents/
│   └── skills/                 # Open agent skills
├── .mise/
│   ├── config.toml             # Mise tools and automation tasks
│   └── config.local.toml.sample
├── .vscode/                    # Editor settings and recommendations
├── assets/                     # Rendered profile SVGs
├── tools/
│   └── profile/
│       ├── data/               # Cached stats and calendar data
│       ├── fonts/              # Source JetBrains Mono WOFF2 fonts
│       ├── fetch.py            # API fetcher
│       ├── render.py           # SVG renderer with font subsetter
│       └── readme.py           # README synchronizer
├── AGENTS.md                   # Agent guidelines and standards
├── CHANGELOG.md                # Generated changelog
├── cliff.toml                  # Git-cliff configuration
├── CONTRIBUTING.md             # Development setup and contribution guide
├── LICENSE                     # MIT License
└── README.md                   # Profile console README
```

---

### 4. Agent Operating Principles

When working in this repository:

1. **Deterministic Rendering**: The embedded JetBrains Mono fonts in `tools/profile/render.py` are subset deterministically. Do not introduce external non-deterministic timestamps or unpinned fonts that cause unnecessary diff churn.
2. **Resilience**: Data fetch failures should degrade gracefully without corrupting existing profile SVGs or data files.
3. **Conventional Commits**: Format all git commit messages strictly according to Conventional Commits.
4. **Markdown Quality**: Respect markdownlint rules when editing or creating markdown documents.
