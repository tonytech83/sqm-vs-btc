import unittest
from app import app


class TestIndexView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_view(self):
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"BTC Price", response.data)


class TestDataView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_data_view(self):
        response = self.app.get("/data")
        assert response.status_code == 200
        assert isinstance(response.json, list)


class TestUpdateDBView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_update_db(self):
        """Test the update-db endpoint."""
        response = self.app.get("/update-db")
        assert response.status_code == 200
        assert response.json["status"] == "Database updated"
