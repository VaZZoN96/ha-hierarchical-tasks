"""Offline HACS packaging tests; no GitHub/HA service is contacted."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.configure_repository import configure, parse_repository, parse_user
from tools.validate_package import check, ValidationError

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_PATH = Path("custom_components/hierarchical_tasks")


class ParsingTests(unittest.TestCase):
    def test_repository_short_and_https(self):
        for value in ("Alice/tasks", "https://github.com/Alice/tasks", "https://github.com/Alice/tasks.git/"):
            with self.subTest(value=value):
                self.assertEqual(parse_repository(value), ("Alice", "tasks"))

    def test_invalid_repositories(self):
        for value in ("Alice", "Alice/a/../b", "https://evil.example/Alice/repo", "http://github.com/Alice/repo",
                      "https://github.com/Alice/repo?token=secret", "https://github.com/Alice/repo#main",
                      "https://github.com@evil.example/Alice/repo", "Alice/..", "git@github.com:Alice/tasks",
                      "YOUR_GITHUB_USERNAME/tasks", "Alice/$(touch x)"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_repository(value)

    def test_username_valid(self):
        for value in ("Alice", "@alice-user", "a", "A" * 39):
            with self.subTest(value=value):
                self.assertEqual(parse_user(value), value.removeprefix("@"))

    def test_username_rejects_unsafe_and_template(self):
        for value in ("YOUR_GITHUB_USERNAME", "a/b", "a--b", "bad user", "a_foo", "-bad", "bad-", "x" * 40, "a;ls"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_user(value)


class PackageFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns("__pycache__", ".git", ".venv", "dist"))
        self.manifest = self.root / DOMAIN_PATH / "manifest.json"
        data = self.read_manifest()
        data.update(documentation="https://github.com/YOUR_GITHUB_USERNAME/ha-hierarchical-tasks",
                    issue_tracker="https://github.com/YOUR_GITHUB_USERNAME/ha-hierarchical-tasks/issues",
                    codeowners=["@YOUR_GITHUB_USERNAME"])
        self.write_manifest(data)
        (self.root / ".github/CODEOWNERS").write_text("* @YOUR_GITHUB_USERNAME\n")

    def read_manifest(self):
        return json.loads(self.manifest.read_text())

    def write_manifest(self, document):
        self.manifest.write_text(json.dumps(document, indent=2) + "\n")

    def ready(self):
        configure(self.root, "example-user/tasks", "test-maintainer")

    def tree(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}


class ConfigureTests(PackageFixture):
    def test_sets_all_metadata_and_preserves_runtime_settings(self):
        before = self.read_manifest()
        changed = configure(self.root, "example-user/tasks")
        after = self.read_manifest()
        self.assertEqual(after["documentation"], "https://github.com/example-user/tasks")
        self.assertEqual(after["issue_tracker"], "https://github.com/example-user/tasks/issues")
        self.assertEqual(after["codeowners"], ["@example-user"])
        for key in set(before) - {"documentation", "issue_tracker", "codeowners"}:
            self.assertEqual(after[key], before[key])
        self.assertEqual(len(changed), 3)

    def test_organization_uses_explicit_person(self):
        configure(self.root, "example-org/tasks", "@individual-user")
        self.assertEqual(self.read_manifest()["codeowners"], ["@individual-user"])
        self.assertIn("* @individual-user", (self.root / ".github/CODEOWNERS").read_text())

    def test_only_three_repository_files_change(self):
        before = self.tree()
        self.ready()
        after = self.tree()
        changed = {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)}
        self.assertEqual(changed, {str(DOMAIN_PATH / "manifest.json"), ".github/CODEOWNERS", "REPOSITORY.md"})

    def test_repeated_configuration_is_idempotent(self):
        self.ready()
        before = self.tree()
        self.assertEqual(configure(self.root, "example-user/tasks", "test-maintainer"), [])
        self.assertEqual(self.tree(), before)

    def test_invalid_input_does_not_modify_any_file(self):
        before = self.tree()
        with self.assertRaises(ValueError):
            configure(self.root, "../not-repository")
        self.assertEqual(self.tree(), before)

    def test_wrong_domain_is_rejected(self):
        doc = self.read_manifest()
        doc["domain"] = "wrong"
        self.write_manifest(doc)
        with self.assertRaises(ValueError):
            self.ready()

    def test_key_order_follows_home_assistant_convention(self):
        self.ready()
        keys = list(self.read_manifest())
        self.assertEqual(keys[:2], ["domain", "name"])
        self.assertEqual(keys[2:], sorted(keys[2:]))

    def test_cli_configures_and_checks_offline(self):
        args = [sys.executable, str(ROOT / "tools/configure_repository.py"), "example-user/tasks", "--root", str(self.root)]
        result = subprocess.run(args, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = subprocess.run([sys.executable, str(ROOT / "tools/validate_package.py"), "--root", str(self.root)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ValidationTests(PackageFixture):
    def test_template_is_rejected_by_default(self):
        with self.assertRaisesRegex(ValidationError, "Template metadata"):
            check(self.root)

    def test_template_can_be_inspected_with_explicit_warning(self):
        result = check(self.root, allow_template=True)
        self.assertTrue(any("TEMPLATE ONLY" in line for line in result))

    def test_template_cannot_claim_a_real_repository(self):
        with self.assertRaises(ValidationError):
            check(self.root, allow_template=True, repository="example-user/tasks")

    def test_configured_repo_passes_offline_checks(self):
        self.ready()
        self.assertGreaterEqual(len(check(self.root, repository="example-user/tasks")), 6)

    def test_different_repository_is_rejected(self):
        self.ready()
        with self.assertRaises(ValidationError):
            check(self.root, repository="someone-else/tasks")

    def test_missing_manifest_field_is_rejected(self):
        self.ready()
        doc = self.read_manifest()
        doc.pop("issue_tracker")
        self.write_manifest(doc)
        with self.assertRaises(ValidationError):
            check(self.root)

    def test_empty_codeowners_are_rejected(self):
        self.ready()
        doc = self.read_manifest()
        doc["codeowners"] = []
        self.write_manifest(doc)
        with self.assertRaises(ValidationError):
            check(self.root)

    def test_mismatched_issue_tracker_is_rejected(self):
        self.ready()
        doc = self.read_manifest()
        doc["issue_tracker"] = "https://github.com/other-user/tasks/issues"
        self.write_manifest(doc)
        with self.assertRaises(ValidationError):
            check(self.root)

    def test_mismatched_codeowners_file_is_rejected(self):
        self.ready()
        (self.root / ".github/CODEOWNERS").write_text("* @someone-else\n")
        with self.assertRaises(ValidationError):
            check(self.root)

    def test_missing_card_is_rejected(self):
        self.ready()
        (self.root / DOMAIN_PATH / "frontend/hierarchical-tasks-card.js").unlink()
        with self.assertRaises(ValidationError):
            check(self.root)

    def test_extra_integration_is_rejected(self):
        self.ready()
        (self.root / "custom_components/another_integration").mkdir()
        with self.assertRaises(ValidationError):
            check(self.root)

    def test_mismatched_card_version_is_rejected(self):
        self.ready()
        path = self.root / DOMAIN_PATH / "frontend/hierarchical-tasks-card.js"
        path.write_text(path.read_text().replace('const VERSION = "', 'const VERSION = "99.'))
        with self.assertRaises(ValidationError):
            check(self.root)

    def test_missing_brand_icon_is_rejected(self):
        self.ready()
        (self.root / DOMAIN_PATH / "brand/icon.png").unlink()
        with self.assertRaises(ValidationError):
            check(self.root)

    def test_non_square_brand_is_rejected(self):
        self.ready()
        path = self.root / DOMAIN_PATH / "brand/icon.png"
        data = bytearray(path.read_bytes())
        data[16:24] = struct.pack(">II", 256, 100)
        path.write_bytes(data)
        with self.assertRaises(ValidationError):
            check(self.root)

    def test_wrong_storage_path_is_rejected(self):
        self.ready()
        path = self.root / DOMAIN_PATH / "const.py"
        path.write_text(path.read_text().replace('.storage/hierarchical_tasks.json', 'data.json'))
        with self.assertRaises(ValidationError):
            check(self.root)

    def test_obsolete_resource_version_is_rejected(self):
        self.ready()
        (self.root / "examples/resource.yaml").write_text("url: /wrong?v=99.0.0\n")
        with self.assertRaises(ValidationError):
            check(self.root)

    def test_zip_release_mode_is_rejected(self):
        self.ready()
        path = self.root / "hacs.json"
        doc = json.loads(path.read_text())
        doc["zip_release"] = True
        path.write_text(json.dumps(doc))
        with self.assertRaises(ValidationError):
            check(self.root)

    def test_invalid_json_is_rejected(self):
        self.ready()
        self.manifest.write_text("{not json")
        with self.assertRaises(ValueError):
            check(self.root)

    def test_cli_rejects_template_before_publication(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/validate_package.py"), "--root", str(self.root)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Template metadata", result.stdout)


if __name__ == "__main__":
    unittest.main()
