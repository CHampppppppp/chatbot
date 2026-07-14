import importlib
import os
import unittest
from unittest.mock import patch


class DeploymentConfigTest(unittest.TestCase):
    def test_http_deployment_configuration_is_read_from_environment(self):
        environment = {
            "ENV": "production",
            "CORS_ALLOWED_ORIGINS": "http://47.114.56.194:28069, http://localhost:3005",
            "COOKIE_SECURE": "false",
            "COOKIE_SAMESITE": "lax",
        }

        with patch.dict(os.environ, environment, clear=False):
            config = importlib.import_module("common.config")
            config = importlib.reload(config)

        self.assertEqual(
            config.CORS_ALLOWED_ORIGINS,
            ["http://47.114.56.194:28069", "http://localhost:3005"],
        )
        self.assertFalse(config.COOKIE_SECURE)
        self.assertEqual(config.COOKIE_SAMESITE, "lax")


if __name__ == "__main__":
    unittest.main()
