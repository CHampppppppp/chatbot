import json
import unittest
from pathlib import Path


class PackageScriptsTest(unittest.TestCase):
    def test_dev_script_listens_on_all_network_interfaces(self):
        package_json = Path(__file__).parents[1] / "package.json"
        package = json.loads(package_json.read_text())

        self.assertEqual(package["scripts"]["dev"], "nuxt dev --host 0.0.0.0")


if __name__ == "__main__":
    unittest.main()
