"""Hosted CI maintenance contracts, separate from product qualification."""
from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
ACTION_VERSIONS = {
    "actions/checkout": "v5",
    "actions/setup-python": "v6",
    "actions/upload-artifact": "v6",
    "actions/github-script": "v8",
    "peter-evans/create-pull-request": "v8",
}


class TestCIWorkflows(unittest.TestCase):
    def test_yaml_and_reusable_workflow_placement(self):
        for path in (ROOT / ".github/workflows").glob("*.yml"):
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIsInstance(yaml.safe_load(text), dict)
                self.assertIsNone(re.search(r"uses:\s*\.\/.github/workflows", text))
                self.assertIsNone(re.search(r"^\s*if:\s*.*secrets\.", text, re.M))

    def test_hosted_runner_version_is_explicit(self):
        jobs_checked = 0
        for path in (ROOT / ".github/workflows").glob("*.yml"):
            workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
            for name, job in workflow["jobs"].items():
                if "uses" in job:
                    continue
                with self.subTest(workflow=path.name, job=name):
                    self.assertEqual(job["runs-on"], "ubuntu-24.04")
                    jobs_checked += 1
        self.assertGreater(jobs_checked, 0)

    def test_managed_actions_use_reviewed_node24_versions(self):
        seen = set()
        for path in (ROOT / ".github/workflows").glob("*.yml"):
            workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
            for job in workflow["jobs"].values():
                for step in job.get("steps", []):
                    reference = step.get("uses", "")
                    action, _, version = reference.partition("@")
                    if action in ACTION_VERSIONS:
                        with self.subTest(workflow=path.name, action=action):
                            self.assertEqual(version, ACTION_VERSIONS[action])
                            seen.add(action)
        self.assertEqual(seen, set(ACTION_VERSIONS))
