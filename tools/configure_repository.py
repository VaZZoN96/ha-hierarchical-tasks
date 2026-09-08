#!/usr/bin/env python3
"""Set real GitHub metadata locally. Standard library only; no network access.

Usage:
    python tools/configure_repository.py OWNER/REPO
    python tools/configure_repository.py ORG/REPO --codeowner GITHUB_USER

The script edits only manifest.json, .github/CODEOWNERS and REPOSITORY.md.
It never reads Home Assistant configuration, task data or credentials.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "hierarchical_tasks"
TEMPLATE_OWNER = "YOUR_GITHUB_USERNAME"
USER_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\Z")
REPO_PATTERN = re.compile(r"[A-Za-z0-9_.-]{1,100}\Z")


def parse_user(value: str) -> str:
    """Validate a personal GitHub handle, not an organization/team path."""
    value = value.strip().removeprefix("@")
    if value == TEMPLATE_OWNER or not USER_PATTERN.fullmatch(value) or "--" in value:
        raise ValueError("Use a real GitHub username, without spaces, underscores or /team.")
    return value


def parse_repository(value: str) -> tuple[str, str]:
    """Accept OWNER/REPO or an https://github.com/OWNER/REPO URL."""
    value = value.strip().rstrip("/")
    if "://" in value:
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or parsed.netloc != "github.com"
                or parsed.query or parsed.fragment):
            raise ValueError("Use OWNER/REPO or an HTTPS GitHub repository URL.")
        value = parsed.path.lstrip("/")
    value = value.removesuffix(".git")
    parts = value.split("/")
    if len(parts) != 2:
        raise ValueError("Expected OWNER/REPO, not a branch, file, ZIP or SSH URL.")
    owner, repository = parse_user(parts[0]), parts[1]
    if not REPO_PATTERN.fullmatch(repository) or repository in {".", ".."}:
        raise ValueError("Invalid GitHub repository name.")
    return owner, repository


def _write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
    return True


def configure(root: Path, repository: str, codeowner: str | None = None) -> list[str]:
    owner, name = parse_repository(repository)
    maintainer = parse_user(codeowner if codeowner is not None else owner)
    path = root / "custom_components" / DOMAIN / "manifest.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("domain") != DOMAIN:
        raise ValueError("This is not the Hierarchical Tasks repository.")
    url = f"https://github.com/{owner}/{name}"
    document.update(documentation=url, issue_tracker=f"{url}/issues", codeowners=[f"@{maintainer}"])
    # Home Assistant's convention: domain and name first, remaining keys sorted.
    document = {key: document[key] for key in ("domain", "name", *sorted(set(document) - {"domain", "name"}))}
    files = {
        path: json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        root / ".github/CODEOWNERS": f"# Maintainer of this repository.\n* @{maintainer}\n",
        root / "REPOSITORY.md": (
            "# Repository metadata\n\n"
            f"Repository: [{owner}/{name}]({url})\n\n"
            f"Issue tracker: [{url}/issues]({url}/issues)\n\n"
            f"Code owner: `@{maintainer}`\n\n"
            f"For HACS: Custom repositories > `{url}` > **Integration**.\n\n"
            "These values were configured locally; this file is NOT evidence that the\n"
            "repository is public, reachable or has passed the official HACS checks.\n"
            "Enable Issues, add a description and topics on GitHub, then run Validate.\n\n"
            "See [PUBLISHING_HACS.md](PUBLISHING_HACS.md) for complete instructions.\n"
        ),
    }
    return [str(p.relative_to(root)) for p, content in files.items() if _write_if_changed(p, content)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="OWNER/REPO or https://github.com/OWNER/REPO")
    parser.add_argument("--codeowner", help="Personal GitHub username; required for an organization owner")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        changed = configure(args.root.resolve(), args.repository, args.codeowner)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Configuration failed: {error}\n")
    for path in changed:
        print(f"Updated {path}")
    print("Metadata ready. No files were uploaded and no GitHub repository was created.")
    print("Next: python tools/validate_package.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
