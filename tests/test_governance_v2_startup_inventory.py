"""Diagnostic manifest parsing only; no native startup qualification."""

import unittest
from unittest.mock import patch

from scripts.inspect_governance_v2_startup import ImageReader, manifest_summary


class ManifestInventoryTests(unittest.TestCase):
    def test_common_controls_dependency_and_execution_level(self):
        result = manifest_summary(b'''<assembly xmlns="urn:schemas-microsoft-com:asm.v1">
          <dependency><dependentAssembly><assemblyIdentity
            name="Microsoft.Windows.Common-Controls" version="6.0.0.0"/>
          </dependentAssembly></dependency>
          <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3"><security>
          <requestedPrivileges><requestedExecutionLevel level="asInvoker" uiAccess="false"/>
          </requestedPrivileges></security></trustInfo></assembly>''')
        self.assertEqual(result["dependencies"][0]["name"], "Microsoft.Windows.Common-Controls")
        self.assertEqual(result["execution_levels"], [{"level": "asInvoker", "uiAccess": "false"}])

    def test_no_dependencies_are_not_invented(self):
        self.assertEqual(manifest_summary(b'<assembly/>'),
                         {"dependencies": [], "execution_levels": []})

    def test_doctype_and_entities_refused(self):
        for xml in (b'<!DOCTYPE assembly><assembly/>',
                    b'<!ENTITY x "synthetic"><assembly/>'):
            with self.subTest(xml=xml), self.assertRaisesRegex(ValueError, "unsupported_xml"):
                manifest_summary(xml)

    def test_native_mapping_requires_windows(self):
        with patch("scripts.inspect_governance_v2_startup.os.name", "posix"):
            with self.assertRaisesRegex(ValueError, "windows_required"):
                ImageReader()
