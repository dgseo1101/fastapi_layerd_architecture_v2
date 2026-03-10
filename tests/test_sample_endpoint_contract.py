import importlib
import os
import unittest
from datetime import datetime, timezone

from dependency_injector import providers
from fastapi.testclient import TestClient


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


class _FakeUserService:
    async def get_active_users(self, page: int, page_size: int):
        now = datetime.now(timezone.utc)
        return [
            {
                "id": 1,
                "name": "demo",
                "email": "demo@example.com",
                "password_hash": "hashed",
                "role": "user",
                "created_at": now,
                "updated_at": now,
                "deleted_at": None,
            }
        ]


class SampleEndpointContractTest(unittest.TestCase):
    def test_active_users_endpoint_returns_200_and_expected_shape(self) -> None:
        server_app = _load_server_app_module()
        app = server_app.create_app()

        fake_service = _FakeUserService()
        with server_app.container.user_service.override(providers.Object(fake_service)):
            with TestClient(app) as client:
                response = client.get(
                    "/users/activate-user", params={"page": 1, "page_size": 10}
                )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

        expected_keys = {
            "id",
            "name",
            "email",
            "password_hash",
            "role",
            "created_at",
            "updated_at",
            "deleted_at",
        }
        self.assertEqual(set(data[0].keys()), expected_keys)
