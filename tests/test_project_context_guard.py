import tempfile
import unittest
from pathlib import Path

from scripts.validate_project_maya_context import REQUIRED_FILES, validate


class TestProjectContextGuard(unittest.TestCase):
    def test_current_repository_context_is_valid(self):
        self.assertEqual(validate(Path.cwd()), [])

    def test_missing_product_spec_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for required in REQUIRED_FILES:
                path = root / required.path
                path.parent.mkdir(parents=True, exist_ok=True)
                if required.path.endswith("project-maya-product-specification-v2.md"):
                    continue
                path.write_text("\n".join(required.anchors), encoding="utf-8")

            errors = validate(root)

        self.assertIn(
            "missing required product-context file: "
            "docs/product/project-maya-product-specification-v2.md",
            errors,
        )

    def test_stale_agent_guidance_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for required in REQUIRED_FILES:
                path = root / required.path
                path.parent.mkdir(parents=True, exist_ok=True)
                content = "\n".join(required.anchors)
                if required.path == "AGENTS.md":
                    content = "# Old guidance\nRead PROJECT_MAYA.md\n"
                path.write_text(content, encoding="utf-8")

            errors = validate(root)

        self.assertTrue(
            any(
                error.startswith(
                    "AGENTS.md is missing required V2 anchor:"
                )
                for error in errors
            )
        )


if __name__ == "__main__":
    unittest.main()
