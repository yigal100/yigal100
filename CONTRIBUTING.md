# Contributing to yigal100

Thank you for contributing to the **yigal100** GitHub Profile Console repository.

---

## Development Environment

We use [`mise`](https://mise.jdx.dev/) for deterministic toolchain, runtime, and task management.

### Prerequisites

Ensure you have `mise` installed on your machine. Refer to the [mise installation guide](https://mise.jdx.dev/getting-started.html).

### Shell Activation (Recommended)

For the best local development experience, activate `mise` in your shell:

```bash
# For zsh:
eval "$(mise activate zsh)"

# For bash:
eval "$(mise activate bash)"
```

### Toolchain Installation

Install all tools declared in [`.mise/config.toml`](.mise/config.toml):

```bash
mise install
```

### Local Configuration & Overrides

If you need custom toolchain versions, local environment variables (such as `PROFILE_TOKEN` or `DEV_API_KEY`), copy the local template:

```bash
cp .mise/config.local.toml.sample .mise/config.local.toml
```

All `*.local.toml` and `.mise/*.local.toml` files are excluded in [`.gitignore`](.gitignore).

### Task Automation

The repository configures tasks inside [`.mise/config.toml`](.mise/config.toml). Inspect available tasks with:

```bash
mise tasks
```

Common tasks:

```bash
mise run render          # Render profile SVGs from data/*.json
mise run update          # Re-render SVGs and synchronize README.md
mise run changelog       # Generate CHANGELOG.md via git-cliff
mise run release:dry-run # Preview next release version and notes
```

---

## Quality and Standards

- **Conventional Commits**: Format all commits using `<type>[optional scope]: <description>` (e.g. `feat:`, `fix:`, `docs:`, `chore:`).
- **Markdown**: Adhere to clean markdownlint conventions.
