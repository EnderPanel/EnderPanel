import unittest

from pydantic import ValidationError

from routes.users import UserUpdate


class UserUpdateValidationTests(unittest.TestCase):
    def test_short_password_is_rejected(self):
        with self.assertRaises(ValidationError):
            UserUpdate(password="short")

    def test_invalid_username_is_rejected(self):
        with self.assertRaises(ValidationError):
            UserUpdate(username="invalid user")

    def test_email_is_normalized_and_validated(self):
        self.assertEqual(UserUpdate(email=" USER@Example.COM ").email, "user@example.com")
        with self.assertRaises(ValidationError):
            UserUpdate(email="not-an-email")


if __name__ == "__main__":
    unittest.main()
