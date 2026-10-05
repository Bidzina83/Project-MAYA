"""Actual Git checkout preservation with Windows automatic line conversion."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = (
    ".gitattributes", "AGENTS.md", "PROJECT_MAYA.md",
    "docs/product/project-maya-product-specification-v2.md",
    "docs/architecture/governance_g2_existing_session_recognition.md",
    "docs/architecture/governance-g2-recognition.json",
    "patches/hermes/0030-existing-session-recognition.patch",
    "scripts/prepare_governance_g2_recognition.py",
    "tests/hermes_g2_recognition_native.py",
    "tests/hermes_g2_recognition_ordinary.py",
    "tests/test_governance_g2_recognition.py",
    "tests/test_governance_g2_create_loop.py",
    "tests/test_governance_line_endings.py",
    "patches/hermes/0031-prompt-cache-mode.patch",
    "docs/architecture/governance-g2-prompt-cache.json",
    "scripts/prepare_governance_g2_prompt_cache.py",
    "tests/hermes_g2_prompt_cache_native.py",
    "tests/hermes_g2_prompt_cache_ordinary.py",
    "tests/test_governance_g2_prompt_cache.py",
    "docs/architecture/governance-g2-restart-loop.json",
    "scripts/verify_governance_g2_restart.py",
    "tests/hermes_g2_restart_loop_native.py",
    "tests/test_governance_g2_restart.py",
    "docs/architecture/governance-g2-final-create.json",
    "scripts/verify_governance_g2_final_create.py",
    "tests/hermes_g2_final_create_native.py",
    "tests/test_governance_g2_final_create.py",
)


def git(directory, *args):
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    return subprocess.run(["git", "-C", str(directory), *args], env=env,
                          capture_output=True, check=True, timeout=30).stdout


class TestGovernanceLineEndings(unittest.TestCase):
    def test_windows_checkout_preserves_protected_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git(root, "init", "--quiet")
            git(root, "config", "core.autocrlf", "true")
            expected = {}
            for name in PROTECTED:
                # Mixed working-tree context files are already LF in Git's index.
                raw = (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                expected[name] = hashlib.sha256(raw).hexdigest()
            git(root, "add", "--", *PROTECTED)
            checkout = root / "checkout"
            checkout.mkdir()
            git(root, "checkout-index", "--all", "--prefix=" + checkout.as_posix() + "/")
            for name, sha in expected.items():
                with self.subTest(path=name):
                    raw = (checkout / name).read_bytes()
                    self.assertNotIn(b"\r\n", raw)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), sha)
                    self.assertEqual(git(root, "check-attr", "eol", "--", name).decode().strip(),
                                     name + ": eol: lf")

    def test_unrelated_binary_and_windows_text_are_not_reconfigured(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git(root, "init", "--quiet")
            git(root, "config", "core.autocrlf", "true")
            (root / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
            binary = b"\x89PNG\r\n\x1a\n\x00synthetic-binary-fixture"
            (root / "fixture.png").write_bytes(binary)
            (root / "launcher.cmd").write_bytes(b"@echo off\necho synthetic fixture\n")
            git(root, "add", ".gitattributes", "fixture.png", "launcher.cmd")
            checkout = root / "checkout"
            checkout.mkdir()
            git(root, "checkout-index", "--all", "--prefix=" + checkout.as_posix() + "/")
            self.assertEqual((checkout / "fixture.png").read_bytes(), binary)
            self.assertEqual((checkout / "launcher.cmd").read_bytes(),
                             b"@echo off\r\necho synthetic fixture\r\n")
