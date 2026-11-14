"""Configuration models and loader for profile-console."""

from __future__ import annotations

import datetime
import os
import pathlib
import random
import tomllib
from dataclasses import dataclass

PACKAGE_DIR = pathlib.Path(__file__).resolve().parent


def get_repo_root() -> pathlib.Path:
    """Walk upward from the package directory to locate the repository root."""
    for parent in [PACKAGE_DIR, *PACKAGE_DIR.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return pathlib.Path.cwd()


@dataclass(frozen=True)
class Paths:
    """Resolved filesystem paths used across fetch, render, and readme tasks."""

    root: pathlib.Path
    data_dir: pathlib.Path
    assets_dir: pathlib.Path
    readme_path: pathlib.Path
    config_path: pathlib.Path
    fonts_dir: pathlib.Path = PACKAGE_DIR / "fonts"
    icons_path: pathlib.Path = PACKAGE_DIR / "icons.json"

    @classmethod
    def resolve(
        cls,
        *,
        data_dir: pathlib.Path | None = None,
        out_dir: pathlib.Path | None = None,
        config_path: pathlib.Path | None = None,
    ) -> Paths:
        root = get_repo_root()
        default_data = root / "data" if (root / "data").exists() else root / "tools" / "profile" / "data"
        return cls(
            root=root,
            data_dir=pathlib.Path(data_dir) if data_dir is not None else default_data,
            assets_dir=pathlib.Path(out_dir) if out_dir is not None else root / "assets",
            readme_path=root / "README.md",
            config_path=pathlib.Path(config_path) if config_path is not None else root / "profile.toml",
        )


@dataclass(frozen=True)
class ProfileInfo:
    """Personal identity, status, and bio lines rendered in the console."""

    github_user: str
    dev_user: str
    name: str
    handle: str
    tagline_handle: str
    node_label: str
    status_label: str
    header_title: str
    header_desc: str
    bio: tuple[str, ...]


@dataclass(frozen=True)
class LinkItem:
    """Social/channel button rendered in the links row."""

    icon: str
    label: str
    handle: str
    url: str
    filename: str

    @classmethod
    def from_dict(cls, raw: dict[str, str]) -> LinkItem:
        icon = raw["icon"]
        return cls(
            icon=icon,
            label=raw["label"],
            handle=raw["handle"],
            url=raw["url"],
            filename=raw.get("filename", icon),
        )


@dataclass(frozen=True)
class ProjectItem:
    """Featured project card configuration."""

    slug: str
    name: str
    url: str
    tag: str
    tag_color: str
    stars: int
    stack: str
    desc: str

    @classmethod
    def from_dict(cls, raw: dict) -> ProjectItem:
        return cls(
            slug=raw["slug"],
            name=raw["name"],
            url=raw["url"],
            tag=raw["tag"],
            tag_color=raw["tag_color"],
            stars=int(raw.get("stars", 0)),
            stack=raw["stack"],
            desc=raw["desc"],
        )


@dataclass(frozen=True)
class StackCategory:
    """Single row in the tech stack loadout."""

    category: str
    items: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: dict) -> StackCategory:
        return cls(
            category=raw["category"],
            items=tuple(raw["items"]),
        )


@dataclass(frozen=True)
class ReadingItem:
    """Recommended reading entry configured in profile.toml."""

    title: str
    url: str
    source: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, str]) -> ReadingItem:
        return cls(
            title=raw["title"],
            url=raw["url"],
            source=raw.get("source", ""),
        )


THEMES_DIR = PACKAGE_DIR / "themes"


def available_themes() -> tuple[str, ...]:
    """Return sorted theme preset names discovered from themes/*.toml."""
    return tuple(sorted(p.stem for p in THEMES_DIR.glob("*.toml")))


VALID_THEMES = available_themes()
VALID_MODES = ("dark", "light", "adaptive")
VALID_STRATEGIES = ("fixed", "rotate", "random")


@dataclass(frozen=True)
class ThemeConfig:
    """Theme rendering settings loaded from profile.toml."""

    mode: str = "adaptive"
    scifi_labels: bool = False

    @classmethod
    def from_dict(cls, raw: dict | None) -> ThemeConfig:
        if not raw:
            return cls()
        mode = str(raw.get("mode", "adaptive")).strip().lower()
        if mode not in VALID_MODES:
            raise ValueError(f"Unknown theme mode {mode!r}; expected one of {VALID_MODES}")
        themed_labels = raw.get("themed_labels", raw.get("scifi_labels", False))
        return cls(
            mode=mode,
            scifi_labels=bool(themed_labels),
        )

    def resolve(
        self,
        *,
        theme_override: str | None = None,
        mode_override: str | None = None,
        strategy_override: str | None = None,
        today: datetime.date | None = None,
    ) -> tuple[str, str]:
        """Resolve concrete (theme_name, mode) from CLI theme/strategy/mode arguments."""
        mode = (mode_override or self.mode).strip().lower()
        if mode not in VALID_MODES:
            raise ValueError(f"Unknown theme mode {mode!r}; expected one of {VALID_MODES}")

        if theme_override:
            name = theme_override.strip().lower()
            if name not in VALID_THEMES:
                raise ValueError(f"Unknown theme name {name!r}; expected one of {VALID_THEMES}")
            return name, mode

        strategy = (strategy_override or "rotate").strip().lower()
        if strategy not in VALID_STRATEGIES:
            raise ValueError(f"Unknown theme strategy {strategy!r}; expected one of {VALID_STRATEGIES}")

        if strategy == "random":
            return random.choice(VALID_THEMES), mode
        if strategy == "fixed":
            return VALID_THEMES[0], mode
        day = today or datetime.date.today()
        return VALID_THEMES[day.toordinal() % len(VALID_THEMES)], mode


@dataclass(frozen=True)
class ProfileConfig:
    """Top-level configuration loaded from profile.toml."""

    profile: ProfileInfo
    theme: ThemeConfig
    links: tuple[LinkItem, ...]
    projects: tuple[ProjectItem, ...]
    stack: tuple[StackCategory, ...]
    reading: tuple[ReadingItem, ...] = ()


def load_config(config_path: pathlib.Path | None = None) -> ProfileConfig:
    """Load profile configuration from TOML, applying optional env overrides."""
    path = config_path or (get_repo_root() / "profile.toml")
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    p = raw["profile"]

    github_user = os.environ.get("GITHUB_ACTOR") or p["github_user"]
    dev_user = os.environ.get("DEV_USER", p.get("dev_user", ""))

    profile = ProfileInfo(
        github_user=github_user,
        dev_user=dev_user,
        name=p["name"],
        handle=p["handle"],
        tagline_handle=p["tagline_handle"],
        node_label=p["node_label"],
        status_label=p["status_label"],
        header_title=p["header_title"],
        header_desc=p["header_desc"],
        bio=tuple(p["bio"]),
    )
    return ProfileConfig(
        profile=profile,
        theme=ThemeConfig.from_dict(raw.get("theme")),
        links=tuple(LinkItem.from_dict(item) for item in raw.get("links", [])),
        projects=tuple(ProjectItem.from_dict(item) for item in raw.get("projects", [])),
        stack=tuple(StackCategory.from_dict(item) for item in raw.get("stack", [])),
        reading=tuple(ReadingItem.from_dict(item) for item in raw.get("reading", [])),
    )
