import json
from pathlib import Path
import unittest


class PackageScriptsTest(unittest.TestCase):
    def test_dev_script_runs_fastapi_from_the_project_virtualenv(self):
        package_path = Path(__file__).parents[1] / "package.json"
        package = json.loads(package_path.read_text())

        self.assertEqual(
            package["scripts"]["dev"],
            "ENV=dev ./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload",
        )


if __name__ == "__main__":
    unittest.main()
