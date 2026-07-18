from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "codex-plugin" / "fredo"
PLUGIN_MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE_MANIFEST = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
SKILL_MANIFEST = PLUGIN_ROOT / "skills" / "fredo-call" / "SKILL.md"


def _json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _frontmatter(path: Path) -> dict[str, str]:
    contents = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(?P<header>.*?)\n---\n", contents, flags=re.DOTALL)
    assert match is not None, f"{path} must start with closed YAML frontmatter"

    fields: dict[str, str] = {}
    for line in match.group("header").splitlines():
        key, separator, value = line.partition(":")
        assert separator and key and value.strip(), f"invalid frontmatter line: {line!r}"
        fields[key.strip()] = value.strip()
    return fields


def test_plugin_manifest_is_minimal_and_versioned() -> None:
    manifest = _json_object(PLUGIN_MANIFEST)

    assert manifest["name"] == "fredo"
    assert manifest["version"] == "0.1.0"
    assert manifest["skills"] == "./skills/"
    assert "apps" not in manifest
    assert "mcpServers" not in manifest


def test_repo_marketplace_points_to_fredo_plugin() -> None:
    marketplace = _json_object(MARKETPLACE_MANIFEST)
    plugins = marketplace["plugins"]
    assert isinstance(plugins, list) and len(plugins) == 1

    entry = plugins[0]
    assert entry["name"] == "fredo"
    assert entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert entry["category"] == "Productivity"

    source_path = entry["source"]["path"]
    assert isinstance(source_path, str) and source_path.startswith("./")
    resolved_plugin = REPO_ROOT / source_path.removeprefix("./")
    assert (resolved_plugin / ".codex-plugin" / "plugin.json").is_file()


def test_skill_frontmatter_and_safety_contract() -> None:
    frontmatter = _frontmatter(SKILL_MANIFEST)
    contents = SKILL_MANIFEST.read_text(encoding="utf-8")

    assert frontmatter["name"] == "fredo-call"
    assert "English or French" in frontmatter["description"]
    assert contents.index("Prepare Fredo demo") < contents.index(
        "uv run fredo doctor --json"
    ) < contents.index("uv run fredo demo")
    assert '{"platform":"macos-arm64","profile":"hosted-voice-mvp"}' in contents
    assert "apps search" in contents
    assert "prepare Fredo hosted voice demo" in contents
    assert "<resolved-maker>/fredo-demo" in contents
    assert "Do not ask the judge" in contents
    assert "--ginse-demo-session-id '<demo_session_id>'" in contents
    assert "--ginse-expires-at '<expires_at>'" in contents
    assert "not cryptographic call authorization" in contents
    assert "explicit recipient-consent" in contents
    assert "Never send a phone number" in contents
    assert "no real phone call was made" in contents
