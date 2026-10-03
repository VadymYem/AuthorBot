#!/usr/bin/env python3
"""Exercise the Termux installer without touching packages, profiles or Telegram."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
START = "# >>> AuthorBot autostart >>>"
END = "# <<< AuthorBot autostart <<<"


class TermuxInstallerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.app = root / "Author Bot — тест"
        (self.app / "scripts").mkdir(parents=True)
        shutil.copy(ROOT / "termux.sh", self.app / "termux.sh")
        shutil.copy(ROOT / "scripts/termux-runtime.sh", self.app / "scripts/termux-runtime.sh")
        self.prefix = root / "prefix"
        self.bin = self.prefix / "bin"
        self.bin.mkdir(parents=True)
        self.profile = root / "profile"
        self.profile.write_text("export KEEP_ME=yes\n", encoding="utf-8")
        self.calls = root / "calls.jsonl"
        self.env = {
            **os.environ,
            "PATH": f"{self.bin}:{os.environ['PATH']}",
            "PREFIX": str(self.prefix),
            "AUTHORBOT_PROFILE": str(self.profile),
            "AUTHORBOT_LOG_FILE": str(root / "install.log"),
            "AUTHORBOT_INSTALL_ONLY": "1",
            "MOCK_CALLS": str(self.calls),
        }
        self.env.pop("NO_AUTOSTART", None)
        mock = f"#!{sys.executable}\n" + '''import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ["MOCK_CALLS"], "a", encoding="utf-8") as log:
    log.write(json.dumps([name, *args]) + "\\n")
if name == "pkg" and os.environ.get("MOCK_FAIL_PKG"):
    print("package failure")
    sys.exit(7)
if name == "proot-distro":
    if args == ["install", "--help"]:
        print("--name NAME")
    elif args == ["list", "--quiet"]:
        if os.environ.get("MOCK_EXISTING"):
            print("authorbot")
    elif args and args[0] == "login" and os.environ.get("MOCK_FAIL_GUEST"):
        print("dependency failure")
        sys.exit(8)
'''
        for name in ("pkg", "proot-distro"):
            path = self.bin / name
            path.write_text(mock, encoding="utf-8")
            path.chmod(0o700)

    def install(self):
        return subprocess.run(["bash", str(self.app / "termux.sh")],
                              env=self.env, capture_output=True, text=True)

    def recorded(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()]

    def test_new_install_and_launcher_preserve_path_and_arguments(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(["proot-distro", "install", "debian:bookworm", "--name", "authorbot"], self.recorded())
        result = subprocess.run(["bash", str(self.bin / "authorbot"), "--help", "two words"],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.recorded()[-1], ["proot-distro", "login", "--bind",
                         f"{self.app}:/opt/authorbot", "authorbot", "--", "/bin/bash",
                         "/opt/authorbot/scripts/termux-runtime.sh", "run", "--help", "two words"])
        self.assertIn("export KEEP_ME=yes", self.profile.read_text())

    def test_existing_guest_is_preserved(self):
        self.env["MOCK_EXISTING"] = "1"
        self.assertEqual(self.install().returncode, 0)
        self.assertFalse(any(call[:3] == ["proot-distro", "install", "debian:bookworm"] for call in self.recorded()))

    def test_package_failure_stops_before_guest_and_profile_changes(self):
        self.env["MOCK_FAIL_PKG"] = "1"
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("package failure", result.stdout)
        self.assertEqual(self.profile.read_text(), "export KEEP_ME=yes\n")
        self.assertFalse((self.bin / "authorbot").exists())
        self.assertFalse(any(call[0] == "proot-distro" for call in self.recorded()))

    def test_guest_dependency_failure_does_not_enable_autostart(self):
        self.env["MOCK_FAIL_GUEST"] = "1"
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dependency failure", result.stdout)
        self.assertEqual(self.profile.read_text(), "export KEEP_ME=yes\n")
        self.assertFalse((self.bin / "authorbot").exists())

    def test_profile_migration_is_repeatable_and_preserves_user_settings(self):
        self.profile.write_text(f"export BEFORE=yes\n{START}\nexec old-python\n{END}\nexport AFTER=yes\n")
        self.assertEqual(self.install().returncode, 0)
        self.assertEqual(self.install().returncode, 0)
        content = self.profile.read_text()
        self.assertIn("export BEFORE=yes", content)
        self.assertIn("export AFTER=yes", content)
        self.assertNotIn("exec old-python", content)
        self.assertEqual(content.count(START), 1)

    def test_no_autostart_preserves_profile(self):
        self.env["NO_AUTOSTART"] = "1"
        self.assertEqual(self.install().returncode, 0)
        self.assertEqual(self.profile.read_text(), "export KEEP_ME=yes\n")

    def test_malformed_profile_is_not_truncated(self):
        content = f"export KEEP_ME=yes\n{START}\ncustom content\n"
        self.profile.write_text(content)
        self.assertNotEqual(self.install().returncode, 0)
        self.assertEqual(self.profile.read_text(), content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
