"""
Integration tests for Flask app validation layer.

Tests the validation framework integrated into Flask routes.
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
from validators import ValidationError


class TestAppValidation(unittest.TestCase):
    """Test validation in Flask app routes."""

    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key'

    def setUp(self):
        """Set up test client and database before each test."""
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up after each test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # --- Registration Tests ---

    def test_register_valid_user(self):
        """Test registration with valid credentials."""
        response = self.app.post('/register', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=False)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)

        # User should exist in database
        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)

    def test_register_short_username(self):
        """Test registration with username < 3 characters."""
        response = self.app.post('/register', data={
            'username': 'ab',
            'password': 'password123'
        })

        # Should stay on registration page with error
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'at least 3', response.data)

    def test_register_short_password(self):
        """Test registration with password < 6 characters."""
        response = self.app.post('/register', data={
            'username': 'testuser',
            'password': '12345'
        })

        # Should stay on registration page with error
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'6 characters', response.data)

    def test_register_missing_username(self):
        """Test registration with missing username."""
        response = self.app.post('/register', data={
            'password': 'password123'
        })

        # Should stay on registration page with error
        self.assertEqual(response.status_code, 200)

    def test_register_duplicate_username(self):
        """Test registration with existing username."""
        # Create first user
        self.app.post('/register', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Try to register again with same username
        response = self.app.post('/register', data={
            'username': 'testuser',
            'password': 'different123'
        })

        # Should show error
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'already exists', response.data)

    # --- Login Tests ---

    def test_login_valid_credentials(self):
        """Test login with valid credentials."""
        # Register user first
        self.app.post('/register', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Login
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=False)

        # Should redirect to inventory
        self.assertEqual(response.status_code, 302)

    def test_login_invalid_credentials(self):
        """Test login with invalid password."""
        # Register user first
        self.app.post('/register', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Login with wrong password
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })

        # Should show error
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid', response.data)

    def test_login_missing_fields(self):
        """Test login with missing fields."""
        response = self.app.post('/login', data={
            'username': 'testuser'
            # password missing
        })

        # Should show error
        self.assertEqual(response.status_code, 200)

    # --- Inventory Validation Tests ---

    def test_inventory_negative_stock(self):
        """Test that negative stock is rejected."""
        # Login first
        self.app.post('/register', data={
            'username': 'testuser',
            'password': 'password123'
        })
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Try to add product with negative stock
        response = self.app.post('/inventory', data={
            'id': 'PROD001',
            'name': 'Test Product',
            'category': 'Test',
            'stock': '-10',
            'price': '99.99',
            'supplier': 'Test Supplier',
            'expiry_date': ''
        })

        # Should show error
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'at least 0', response.data)

    def test_inventory_negative_price(self):
        """Test that negative price is rejected."""
        # Login first
        self.app.post('/register', data={
            'username': 'testuser',
            'password': 'password123'
        })
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Try to add product with negative price
        response = self.app.post('/inventory', data={
            'id': 'PROD001',
            'name': 'Test Product',
            'category': 'Test',
            'stock': '100',
            'price': '-99.99',
            'supplier': 'Test Supplier',
            'expiry_date': ''
        })

        # Should show error
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'at least 0', response.data)

    def test_inventory_invalid_stock_format(self):
        """Test that non-numeric stock is rejected."""
        # Login first
        self.app.post('/register', data={
            'username': 'testuser',
            'password': 'password123'
        })
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Try to add product with invalid stock
        response = self.app.post('/inventory', data={
            'id': 'PROD001',
            'name': 'Test Product',
            'category': 'Test',
            'stock': 'abc',
            'price': '99.99',
            'supplier': 'Test Supplier',
            'expiry_date': ''
        })

        # Should show error
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'valid integer', response.data)

    def test_inventory_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        # Login first
        self.app.post('/register', data={
            'username': 'testuser',
            'password': 'password123'
        })
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Try to add product without name
        response = self.app.post('/inventory', data={
            'id': 'PROD001',
            # 'name' is missing
            'category': 'Test',
            'stock': '100',
            'price': '99.99',
            'supplier': 'Test Supplier'
        })

        # Should show error
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)

