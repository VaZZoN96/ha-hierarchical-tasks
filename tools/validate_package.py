#!/usr/bin/env python3
"""Offline structural checks, NOT the official HACS or hassfest validator.

Default mode rejects template metadata. --allow-template is only for inspecting
an unpublished distribution archive, never for marking a repository HACS-ready.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path

try:
    from .configure_repository import DOMAIN, ROOT, TEMPLATE_OWNER, parse_repository, parse_user
except ImportError:
    from configure_repository import DOMAIN, ROOT, TEMPLATE_OWNER, parse_repository, parse_user


class ValidationError(ValueError):
    """Invalid package structure or metadata."""


def check(root: Path, *, allow_template: bool = False, repository: str | None = None) -> list[str]:
    checks: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ValidationError(message)

    component = root / "custom_components" / DOMAIN
    dirs = sorted(p.name for p in (root / "custom_components").iterdir()
                  if p.is_dir() and p.name != "__pycache__")
    require(dirs == [DOMAIN], "Expected exactly custom_components/hierarchical_tasks.")
    for name in ("__init__.py", "config_flow.py", "const.py", "model.py", "storage.py",
                 "runtime.py", "services.py", "websocket.py", "manifest.json", "strings.json",
                 "services.yaml", "translations/en.json", "translations/pl.json",
                 "frontend/hierarchical-tasks-card.js", "brand/icon.png"):
        require((component / name).is_file(), f"Missing runtime file: {name}")
    for name in ("README.md", "LICENSE", "hacs.json", "PUBLISHING_HACS.md", "INSTALLATION.md",
                 "REPOSITORY.md", "CHANGELOG.md", ".github/CODEOWNERS",
                 ".github/workflows/validate.yml", ".github/workflows/prepare-repository.yml"):
        require((root / name).is_file(), f"Missing repository file: {name}")
    checks.append("One integration; frontend and brand assets are inside its directory")

    for path in component.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    hacs = json.loads((root / "hacs.json").read_text(encoding="utf-8"))
    require(hacs.get("name") == "Hierarchical Tasks", "Wrong HACS display name")
    require(hacs.get("content_in_root", False) is False, "content_in_root must be false")
    require(hacs.get("zip_release", False) is False, "This repository uses source downloads, not ZIP releases")
    require(hacs.get("homeassistant") == "2026.9.0", "Minimum HA version must match the documented baseline")
    checks.append("JSON files parse; HACS manifest matches the source-directory layout")

    manifest = json.loads((component / "manifest.json").read_text(encoding="utf-8"))
    required = {"domain", "name", "documentation", "issue_tracker", "codeowners", "version"}
    require(required <= manifest.keys(), "Missing required integration manifest fields")
    require(manifest["domain"] == DOMAIN, "Wrong integration domain")
    require(manifest.get("config_flow") is True, "Config flow must be enabled")
    require(manifest.get("single_config_entry") is True, "Only one config entry is supported")
    owners = manifest["codeowners"]
    require(isinstance(owners, list) and len(owners) > 0, "At least one code owner is required")
    metadata = json.dumps({key: manifest[key] for key in ("documentation", "issue_tracker", "codeowners")})
    is_template = TEMPLATE_OWNER in metadata
    if is_template:
        require(allow_template, "Template metadata remains. Run tools/configure_repository.py OWNER/REPO or Prepare repository first.")
        require(repository is None, "A template cannot be validated against a real GitHub repository.")
        checks.append("TEMPLATE ONLY: real repository metadata still must be configured before HACS")
    else:
        for handle in owners:
            require(isinstance(handle, str) and handle.startswith("@"), "Code owners must be @user handles")
            parse_user(handle)
        owner, repo = parse_repository(manifest["documentation"])
        url = f"https://github.com/{owner}/{repo}"
        require(manifest["documentation"] == url, "Documentation must link to the repository root")
        require(manifest["issue_tracker"] == url + "/issues", "Issue tracker points to another repository")
        codeowners = (root / ".github/CODEOWNERS").read_text(encoding="utf-8")
        require(f"* {' '.join(owners)}" in codeowners, "CODEOWNERS and manifest do not match")
        if repository:
            require(parse_repository(repository) == (owner, repo), "Manifest points to a different GitHub repository")
        checks.append("Repository links and code owners are configured consistently (syntax only)")

    version = manifest["version"]
    require(isinstance(version, str) and re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version) is not None,
            "Invalid integration version")
    constants = (component / "const.py").read_text(encoding="utf-8")
    card = (component / "frontend/hierarchical-tasks-card.js").read_text(encoding="utf-8")
    require(f'VERSION = "{version}"' in constants, "Python version differs from manifest")
    require(f'const VERSION = "{version}";' in card, "Card version differs from manifest")
    require(f"?v={version}" in (root / "examples/resource.yaml").read_text(encoding="utf-8"), "Resource example has an old version")
    require('STORAGE_FILE = ".storage/hierarchical_tasks.json"' in constants, "Storage path must stay outside the installed code directory")
    checks.append(f"Version {version} agrees across backend, card and resource example; storage path preserved")

    for filename in ("icon.png", "icon@2x.png"):
        data = (component / "brand" / filename).read_bytes()
        require(data.startswith(b"\x89PNG\r\n\x1a\n") and data[12:16] == b"IHDR", f"Invalid PNG: {filename}")
        width, height = struct.unpack(">II", data[16:24])
        require(width == height and width >= 128, f"Brand icon must be square, >=128 px: {filename}")
    checks.append("Local brand icons have valid PNG headers and square dimensions")
    for path in component.rglob("*.py"):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    checks.append("Integration Python source compiles without importing Home Assistant")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-template", action="store_true", help="Inspect unpublished ZIP; not a HACS-ready verdict")
    parser.add_argument("--repository", help="Also require metadata to match OWNER/REPO")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        checks = check(args.root.resolve(), allow_template=args.allow_template, repository=args.repository)
    except (ValueError, OSError, KeyError, TypeError, SyntaxError) as error:
        print(f"FAIL: {error}")
        return 1
    for message in checks:
        print(f"PASS: {message}")
    print("Offline checks only. Run the official HACS/hassfest workflow on your public repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
