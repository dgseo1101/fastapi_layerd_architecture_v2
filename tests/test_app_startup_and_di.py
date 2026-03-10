import importlib
import os
import unittest


def _set_test_env() -> None:
    os.environ.setdefault("DATABASE_USER", "test_user")
    os.environ.setdefault("DATABASE_PASSWORD", "test_password")
    os.environ.setdefault("DATABASE_HOST", "127.0.0.1")
    os.environ.setdefault("DATABASE_PORT", "5432")
    os.environ.setdefault("DATABASE_NAME", "test_db")


def _load_server_app_module():
    _set_test_env()
    mod = importlib.import_module("server.app")
    return importlib.reload(mod)


class AppStartupAndDiSmokeTest(unittest.TestCase):
    def test_create_app_and_di_container_are_wired(self) -> None:
        server_app = _load_server_app_module()

        app = server_app.create_app()

        self.assertIsNotNone(server_app.container)
        self.assertTrue(hasattr(server_app.container, "user_service"))

        user_service = server_app.container.user_service()
        self.assertIsNotNone(user_service)

        paths = {route.path for route in app.routes}
        self.assertIn("/users/", paths)
        self.assertIn("/users/activate-user", paths)
