#!/usr/bin/env python3
"""Regression checks for foreground restart, first authentication and EOF."""
from __future__ import annotations

import importlib.util
import fcntl
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import sys
import struct
import tempfile
import time
import termios
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def terminal_process(command, *, cwd, env, prompt, answer, timeout=45, columns=40):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 32, columns, 0, 0))
    process = subprocess.Popen(command, cwd=cwd, env=env, stdin=slave, stdout=slave,
                               stderr=slave, start_new_session=True)
    os.close(slave)
    output = bytearray()
    sent = False
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    process.wait(timeout=5)
                    break
                if not chunk:
                    break
                output.extend(chunk)
                if not sent and prompt.encode() in output:
                    os.write(master, answer.encode())
                    sent = True
            if process.poll() is not None and not ready:
                break
        if process.poll() is None:
            raise AssertionError("Terminal process timed out: " + output.decode(errors="replace"))
        return process.returncode, output.decode(errors="replace"), sent
    finally:
        if process.poll() is None:
            # This is an isolated test session, never the real Termux group.
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        os.close(master)


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.env = dict(os.environ)
        for key in ("api_id", "api_hash", "DOCKER", "LAVHOST", "AUTHORBOT_DO_NOT_RESTART",
                    "AUTHORBOT_DO_NOT_RESTART2"):
            self.env.pop(key, None)
        self.env["AUTHORBOT_TERMUX"] = "1"

    def test_restart_preserves_parent_shell_arguments_and_keyboard(self):
        package = self.root / "acbot"
        package.mkdir()
        (package / "__init__.py").write_text("")
        (package / "__main__.py").write_text(
            "import os,sys\nprint('RESTART_PID=' + str(os.getpid()), flush=True)\n"
            "print('ARG=' + sys.argv[1], flush=True)\n"
            "print('AUTH_OK=' + input('API INPUT: '), flush=True)\n")
        worker = self.root / "worker.py"
        worker.write_text(
            "import importlib.util, pathlib, sys, os\n"
            f"spec=importlib.util.spec_from_file_location('internal', {str(ROOT / 'acbot/_internal.py')!r})\n"
            "internal=importlib.util.module_from_spec(spec); spec.loader.exec_module(internal)\n"
            f"internal.ROOT=pathlib.Path({str(self.root)!r})\n"
            "sys.argv=['worker', 'two words']\n"
            "print('ORIGINAL_PID=' + str(os.getpid()), flush=True)\n"
            "internal.restart()\n")
        controller = self.root / "controller.py"
        controller.write_text(
            "import subprocess,sys\n"
            f"p=subprocess.run([sys.executable, {str(worker)!r}])\n"
            "print('PARENT_SHELL_ALIVE', flush=True)\nsys.exit(p.returncode)\n")
        code, output, sent = terminal_process([sys.executable, str(controller)],
            cwd=self.root, env=self.env, prompt="API INPUT:", answer="12345\n")
        self.assertTrue(sent, output)
        self.assertEqual(code, 0, output)
        self.assertIn("PARENT_SHELL_ALIVE", output)
        self.assertIn("AUTH_OK=12345", output)
        self.assertIn("ARG=two words", output)
        original = output.split("ORIGINAL_PID=", 1)[1].split()[0]
        restarted = output.split("RESTART_PID=", 1)[1].split()[0]
        self.assertEqual(original, restarted, output)

    def test_dependency_stamp_tracks_interpreter_and_requirements(self):
        from acbot import runtime_state
        app = self.root / "app"
        app.mkdir()
        requirements = app / "requirements.txt"
        requirements.write_text("one==1\n")
        environment = self.root / "venv"
        environment.mkdir()
        other = self.root / "other-venv"
        other.mkdir()
        with patch.object(runtime_state, "ROOT", app), patch.object(sys, "prefix", str(environment)):
            self.assertFalse(runtime_state.dependencies_ready())
            runtime_state.mark_dependencies_ready()
            self.assertTrue(runtime_state.dependencies_ready())
            requirements.write_text("one==2\n")
            self.assertFalse(runtime_state.dependencies_ready())
            runtime_state.mark_dependencies_ready()
            with patch.object(sys, "prefix", str(other)):
                self.assertFalse(runtime_state.dependencies_ready())
        self.assertFalse((app / ".requirements_hash").exists())

    def test_closed_configuration_input_has_recovery_message_without_traceback(self):
        code = "from acbot.configurator import tty_input; tty_input('API ID: ', False)"
        process = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=self.env,
                                 input="", capture_output=True, text=True)
        self.assertEqual(process.returncode, 2, process.stdout + process.stderr)
        self.assertIn("authorbot", process.stdout)
        self.assertNotIn("Traceback", process.stderr)
        self.assertNotIn("EOFError", process.stderr)

    def test_installed_first_launch_reaches_auth_without_reinstall_or_restart(self):
        from acbot.runtime_state import mark_dependencies_ready
        mark_dependencies_ready()
        command = [sys.executable, "-m", "acbot", "--root", "--no-web", "--data-root", str(self.root)]
        code, output, sent = terminal_process(command, cwd=ROOT, env=self.env,
                                             prompt="Введи API ID:", answer="\n")
        self.assertTrue(sent, output)
        self.assertEqual(code, 0, output)
        self.assertIn("Вхід скасовано", output)
        self.assertNotIn("requirements.txt changed", output)
        self.assertNotIn("Restarting", output)
        self.assertNotIn("Traceback", output)

    def test_closed_first_launch_input_exits_cleanly(self):
        from acbot.runtime_state import mark_dependencies_ready
        mark_dependencies_ready()
        process = subprocess.run([sys.executable, "-m", "acbot", "--root", "--no-web", "--data-root", str(self.root)],
                                 cwd=ROOT, env=self.env, input="", capture_output=True, text=True, timeout=45)
        self.assertEqual(process.returncode, 2, process.stdout + process.stderr)
        self.assertIn("authorbot", process.stdout)
        self.assertNotIn("Traceback", process.stderr)
        self.assertNotIn("EOFError", process.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
