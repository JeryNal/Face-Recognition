from app import app
import unittest

class RouteTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_home_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_protected_routes(self):
        protected_routes = [
            '/admin/dashboard',
            '/admin/reports',
            '/admin/users'
        ]
        for route in protected_routes:
            response = self.app.get(route)
            self.assertEqual(response.status_code, 302)  # Should redirect to login

if __name__ == '__main__':
    unittest.main() 