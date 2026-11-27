import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))


class PersistentActivityTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_directory.name) / "activities.json"
        os.environ["ACTIVITIES_DATA_FILE"] = str(self.data_file)
        self.app_module = importlib.import_module("app")
        self.app_module = importlib.reload(self.app_module)

    def tearDown(self):
        os.environ.pop("ACTIVITIES_DATA_FILE", None)
        self.temp_directory.cleanup()

    def test_registration_survives_module_reload(self):
        email = "student@mergington.edu"

        self.app_module.signup_for_activity("Chess Club", email)
        reloaded_module = importlib.reload(self.app_module)

        self.assertIn(
            email,
            reloaded_module.activities["Chess Club"]["participants"],
        )

    def test_unregister_persists(self):
        email = "michael@mergington.edu"

        self.app_module.unregister_from_activity("Chess Club", email)

        reloaded_module = importlib.reload(self.app_module)
        self.assertNotIn(
            email,
            reloaded_module.activities["Chess Club"]["participants"],
        )

    def test_duplicate_registration_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            self.app_module.signup_for_activity(
                "Chess Club",
                "michael@mergington.edu",
            )

        self.assertEqual(context.exception.status_code, 400)

    def test_missing_registration_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            self.app_module.unregister_from_activity(
                "Chess Club",
                "missing@mergington.edu",
            )

        self.assertEqual(context.exception.status_code, 400)

    def test_unknown_activity_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            self.app_module.signup_for_activity(
                "Unknown Club",
                "student@mergington.edu",
            )

        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
