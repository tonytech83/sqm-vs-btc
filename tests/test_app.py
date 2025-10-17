import unittest

from app import app

SUCCESS_CODE = 200


class TestIndexView(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app.test_client()
        self.app.testing = True

    def test_index_view(self) -> None:
        response = self.app.get("/")
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertIn(b"BTC Price", response.data)  # note: bytes


class TestDataView(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app.test_client()
        self.app.testing = True

    def test_data_view(self) -> None:
        response = self.app.get("/data")
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertIsInstance(response.json, list)


class TestUpdateDBView(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app.test_client()
        self.app.testing = True

    def test_update_db(self) -> None:
        response = self.app.get("/update-db")
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertEqual(response.json["status"], "Database updated")
