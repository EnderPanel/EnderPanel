import unittest

from routes.servers import image_for_mc, java_version_for_mc


class JavaRuntimeSelectionTests(unittest.TestCase):
    def test_java_8_versions_use_java_8(self):
        self.assertEqual(java_version_for_mc("1.12.2", "forge"), 8)
        self.assertEqual(image_for_mc("1.12.2", "forge"), "mc-panel-server:java8")

    def test_legacy_paper_uses_supported_newer_java(self):
        self.assertEqual(java_version_for_mc("1.12.2", "paper"), 11)
        self.assertEqual(java_version_for_mc("1.16.5", "paper"), 17)

    def test_legacy_versions_use_java_11(self):
        self.assertEqual(java_version_for_mc("1.16.4", "paper"), 11)
        self.assertEqual(image_for_mc("1.16.4", "paper"), "mc-panel-server:java11")

    def test_modern_versions_use_java_17_or_21(self):
        self.assertEqual(java_version_for_mc("1.19.4"), 17)
        self.assertEqual(image_for_mc("1.19.4"), "mc-panel-server:java17")
        self.assertEqual(java_version_for_mc("1.20.5"), 21)
        self.assertEqual(image_for_mc("1.20.5"), "mc-panel-server:latest")
        self.assertEqual(java_version_for_mc("1.20.4", "paper"), 21)

    def test_future_versions_use_java_25(self):
        self.assertEqual(java_version_for_mc("1.26.0"), 25)
        self.assertEqual(image_for_mc("1.26.0"), "mc-panel-server:java25")


if __name__ == "__main__":
    unittest.main()
