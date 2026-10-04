#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

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
        shutil.copy(ROOT / "bootstrap-termux.sh", self.app / "bootstrap-termux.sh")
        shutil.copy(ROOT / "scripts/termux-runtime.sh", self.app / "scripts/termux-runtime.sh")
        self.prefix = root / "prefix"
        self.bin = self.prefix / "bin"
        self.bin.mkdir(parents=True)
        (self.prefix / "tmp").mkdir()
        (self.bin / "bash").symlink_to(shutil.which("bash"))
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
        for name in ("AUTHORBOT_BOOTSTRAPPED", "AUTHORBOT_LOG_INITIALIZED", "AUTHORBOT_PROGRESS_FILE"):
            self.env.pop(name, None)
        mock = f"#!{sys.executable}\n" + '''import json, os, sys
from pathlib import Path
import shutil
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ["MOCK_CALLS"], "a", encoding="utf-8") as log:
    log.write(json.dumps([name, *args]) + "\\n")
if name == "pkg" and os.environ.get("MOCK_FAIL_PKG"):
    print("package failure")
    sys.exit(7)
if name == "pkg":
    print("MOCK PACKAGE NOISE", file=sys.stderr)
if name == "git":
    if os.environ.get("MOCK_FAIL_GIT"):
        print("git failure")
        sys.exit(9)
    if args and args[0] == "ls-remote" and os.environ.get("MOCK_BEFORE_TRANSFER") and "VadymYem" in args[-2]:
        sys.exit(9)
    if args and args[0] == "clone":
        destination = Path(args[-1])
        shutil.copytree(os.environ["MOCK_BOOTSTRAP_SOURCE"], destination)
        (destination / ".git").mkdir()
if name == "curl":
    if os.environ.get("MOCK_FAIL_CURL"):
        print("download failure", file=sys.stderr)
        sys.exit(10)
    shutil.copy(os.environ["MOCK_BOOTSTRAP_SCRIPT"], args[-1])
if name == "proot-distro":
    if args == ["install", "--help"]:
        stream = sys.stderr if os.environ.get("MOCK_HELP_STDERR") else sys.stdout
        print("--name NAME", file=stream)
        if os.environ.get("MOCK_LONG_HELP"):
            print("x" * 200000, file=stream)
        sys.exit(int(os.environ.get("MOCK_HELP_STATUS", "0")))
    elif args == ["list", "--quiet"]:
        if os.environ.get("MOCK_EXISTING"):
            print("authorbot")
    elif args and args[0] == "login" and os.environ.get("MOCK_FAIL_GUEST"):
        print("dependency failure")
        sys.exit(8)
    elif args and args[0] == "login" and "install" in args:
        import time
        progress = Path(args[2].split(":/opt/authorbot")[0]) / ".install-progress"
        for stage in range(4, 8):
            temporary = progress.with_suffix(".tmp")
            temporary.write_text(f"{stage}|{stage}/8 · Test stage\\n")
            temporary.replace(progress)
            time.sleep(0.23)
    elif args and args[0] == "login" and "run" in args and os.environ.get("MOCK_AUTH"):
        print("API INPUT: ", end="", flush=True)
        print("AUTH_OK=" + input())
'''
        for name in ("pkg", "proot-distro", "git", "curl"):
            path = self.bin / name
            path.write_text(mock, encoding="utf-8")
            path.chmod(0o700)

    def install(self):
        return subprocess.run(["bash", str(self.app / "termux.sh")],
                              env=self.env, capture_output=True, text=True)

    def recorded(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()]

    def bootstrap(self):
        return subprocess.run(["bash", str(ROOT / "bootstrap-termux.sh")],
                              env=self.env, capture_output=True, text=True)

    def test_bootstrap_installs_into_a_new_checkout(self):
        destination = self.app.parent / "new checkout"
        self.env["AUTHORBOT_APP_DIR"] = str(destination)
        self.env["MOCK_BOOTSTRAP_SOURCE"] = str(self.app)
        result = self.bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((destination / ".git").is_dir())
        self.assertTrue((self.bin / "authorbot").exists())
        self.assertTrue(any(call[:2] == ["git", "clone"] for call in self.recorded()))

    def test_bootstrap_updates_existing_checkout_without_reset(self):
        (self.app / ".git").mkdir()
        self.env["AUTHORBOT_APP_DIR"] = str(self.app)
        result = self.bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(["git", "-C", str(self.app), "fetch", "origin", "main"], self.recorded())
        self.assertIn(["git", "-C", str(self.app), "merge", "--ff-only", "origin/main"], self.recorded())
        self.assertFalse(any("reset" in call for call in self.recorded()))

    def test_bootstrap_uses_current_repository_until_transfer(self):
        destination = self.app.parent / "before transfer"
        self.env.update(AUTHORBOT_APP_DIR=str(destination), MOCK_BOOTSTRAP_SOURCE=str(self.app), MOCK_BEFORE_TRANSFER="1")
        result = self.bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        clone = next(call for call in self.recorded() if call[:2] == ['git', 'clone'])
        self.assertIn('https://github.com/AuthorGramProject/AuthorBot.git', clone)

    def test_bootstrap_prefers_destination_after_transfer(self):
        destination = self.app.parent / "after transfer"
        self.env.update(AUTHORBOT_APP_DIR=str(destination), MOCK_BOOTSTRAP_SOURCE=str(self.app))
        result = self.bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        clone = next(call for call in self.recorded() if call[:2] == ['git', 'clone'])
        self.assertIn('https://github.com/VadymYem/AuthorBot.git', clone)

    def test_bootstrap_does_not_replace_custom_repository(self):
        destination = self.app.parent / "custom"
        self.env.update(AUTHORBOT_APP_DIR=str(destination), MOCK_BOOTSTRAP_SOURCE=str(self.app),
                        MOCK_BEFORE_TRANSFER="1", AUTHORBOT_REPO_URL="https://example.org/custom.git")
        result = self.bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        clone = next(call for call in self.recorded() if call[:2] == ['git', 'clone'])
        self.assertIn('https://example.org/custom.git', clone)
        self.assertFalse(any('AuthorGramProject' in str(call) for call in self.recorded()))

    def test_bootstrap_stops_on_git_failure(self):
        (self.app / ".git").mkdir()
        self.env["AUTHORBOT_APP_DIR"] = str(self.app)
        self.env["MOCK_FAIL_GIT"] = "1"
        result = self.bootstrap()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.bin / "authorbot").exists())
        self.assertEqual(self.profile.read_text(), "export KEEP_ME=yes\n")

    def test_bootstrap_preserves_existing_non_repository_directory(self):
        self.env["AUTHORBOT_APP_DIR"] = str(self.app)
        result = self.bootstrap()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.app / "termux.sh").is_file())
        self.assertFalse((self.app / ".git").exists())
        self.assertFalse(any(call[0] == "git" for call in self.recorded()))

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

    def test_supported_help_on_stderr_is_accepted(self):
        self.env["MOCK_HELP_STDERR"] = "1"
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.bin / "authorbot").exists())

    def test_long_help_does_not_trigger_pipefail(self):
        self.env["MOCK_LONG_HELP"] = "1"
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_help_exit_status_does_not_hide_supported_option(self):
        self.env["MOCK_HELP_STDERR"] = "1"
        self.env["MOCK_HELP_STATUS"] = "1"
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_package_failure_stops_before_guest_and_profile_changes(self):
        self.env["MOCK_FAIL_PKG"] = "1"
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("package failure", result.stdout + result.stderr)
        self.assertIn("Журнал:", result.stderr)
        self.assertIn("package failure", Path(self.env["AUTHORBOT_LOG_FILE"]).read_text())
        self.assertEqual(self.profile.read_text(), "export KEEP_ME=yes\n")
        self.assertFalse((self.bin / "authorbot").exists())
        self.assertFalse(any(call[0] == "proot-distro" for call in self.recorded()))

    def test_guest_dependency_failure_does_not_enable_autostart(self):
        self.env["MOCK_FAIL_GUEST"] = "1"
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("dependency failure", result.stdout + result.stderr)
        self.assertIn("dependency failure", Path(self.env["AUTHORBOT_LOG_FILE"]).read_text())
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

    def test_progress_finishes_only_after_checks_without_package_noise(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("MOCK PACKAGE NOISE", result.stdout + result.stderr)
        self.assertIn("MOCK PACKAGE NOISE", Path(self.env["AUTHORBOT_LOG_FILE"]).read_text())
        for stage in range(1, 9):
            self.assertIn(f"{stage}/8", result.stdout)
        self.assertIn("100%", result.stdout)
        self.assertFalse((self.app / ".install-progress").exists())

    def test_bootstrap_does_not_discard_earlier_log_or_terminal_input(self):
        (self.app / ".git").mkdir()
        self.env["AUTHORBOT_APP_DIR"] = str(self.app)
        self.env.pop("AUTHORBOT_INSTALL_ONLY")
        self.env["MOCK_AUTH"] = "1"
        result = subprocess.run(["bash", str(ROOT / "bootstrap-termux.sh")],
                                env=self.env, input="12345\n", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AUTH_OK=12345", result.stdout)
        self.assertEqual(sum(call[0] == "pkg" for call in self.recorded()), 2)

    def test_failed_install_never_reports_one_hundred_percent(self):
        self.env["MOCK_FAIL_GUEST"] = "1"
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("100%", result.stdout)

    def test_terminal_ui_keeps_keyboard_and_restores_cursor(self):
        from startupcheck import terminal_process
        self.env["TERM"] = "xterm-256color"
        self.env.pop("AUTHORBOT_INSTALL_ONLY")
        self.env["MOCK_AUTH"] = "1"
        code, output, sent = terminal_process(["bash", str(self.app / "termux.sh")],
            cwd=self.app, env=self.env, prompt="API INPUT:", answer="24680\n", columns=28)
        self.assertEqual(code, 0, output)
        self.assertTrue(sent, output)
        self.assertIn("AUTH_OK=24680", output)
        self.assertIn("AuthorBot", output)
        self.assertIn("by AuthorChe", output)
        self.assertIn("100%", output)
        self.assertIn("\033[?25h", output)
        self.assertNotIn("MOCK PACKAGE NOISE", output)

    def downloaded_installer(self):
        script = self.app.parent / "downloaded-termux.sh"
        shutil.copy(ROOT / "termux.sh", script)
        destination = self.app.parent / "standalone checkout"
        self.env["AUTHORBOT_APP_DIR"] = str(destination)
        self.env["MOCK_BOOTSTRAP_SOURCE"] = str(self.app)
        self.env["MOCK_BOOTSTRAP_SCRIPT"] = str(ROOT / "bootstrap-termux.sh")
        return script, destination

    def test_standalone_download_builds_full_checkout(self):
        script, destination = self.downloaded_installer()
        result = subprocess.run(["bash", str(script)], env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((destination / "bootstrap-termux.sh").is_file())
        self.assertTrue((self.bin / "authorbot").exists())
        self.assertEqual(list((self.prefix / "tmp").iterdir()), [])
        download = next(call for call in self.recorded() if call[0] == "curl")
        self.assertIn("https://raw.githubusercontent.com/VadymYem/AuthorBot/main/bootstrap-termux.sh", download)

    def test_website_source_preserves_parent_shell_and_keyboard(self):
        script, _ = self.downloaded_installer()
        self.env.pop("AUTHORBOT_INSTALL_ONLY")
        self.env["MOCK_AUTH"] = "1"
        result = subprocess.run(["bash", "-c", 'source "$1"; printf "PARENT_SHELL_ALIVE\\n"',
                                 "authorbot-test", str(script)], env=self.env, input="13579\n",
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AUTH_OK=13579", result.stdout)
        self.assertIn("PARENT_SHELL_ALIVE", result.stdout)
        self.assertEqual(list((self.prefix / "tmp").iterdir()), [])

    def test_standalone_download_failure_stops_before_clone(self):
        script, _ = self.downloaded_installer()
        self.env["MOCK_FAIL_CURL"] = "1"
        result = subprocess.run(["bash", str(script)], env=self.env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("download failure", result.stdout + result.stderr)
        self.assertIn("Журнал:", result.stderr)
        self.assertFalse(any(call[0] == "git" for call in self.recorded()))
        self.assertFalse((self.bin / "authorbot").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
