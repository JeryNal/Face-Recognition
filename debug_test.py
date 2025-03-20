import unittest
from app import app
from database import DatabaseManager
from debug_config import log_info

class DebugTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.db = DatabaseManager(app.config['SQLALCHEMY_DATABASE_URI'])

    def test_database_connection(self):
        """Test database connection"""
        self.assertTrue(self.db.test_connection())

    def test_routes(self):
        """Test main application routes"""
        routes_to_test = [
            ('/', 200),
            ('/admin/dashboard', 302),  # Should redirect if not logged in
            ('/login', 200),
            ('/nonexistent', 404)
        ]
        
        for route, expected_status in routes_to_test:
            response = self.client.get(route)
            self.assertEqual(response.status_code, expected_status)

    def test_analytics(self):
        """Test analytics functionality"""
        try:
            analytics = EnhancedAnalytics()
            metrics = analytics.get_advanced_metrics()
            self.assertIsNotNone(metrics)
        except Exception as e:
            log_error(e, "Analytics test failed")
            raise

if __name__ == '__main__':
    unittest.main() 