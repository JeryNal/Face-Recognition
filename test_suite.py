# Error: Missing test database configuration
class TestConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Should use test database
    TESTING = True
    WTF_CSRF_ENABLED = False

# Fix: Add test configuration
def setUp(self):
    app.config.from_object(TestConfig)
    self.client = app.test_client()
    with app.app_context():
        db.create_all() 