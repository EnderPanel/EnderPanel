import unittest

from utils.security import hash_password, is_legacy_password_hash, verify_password


class PasswordSecurityTests(unittest.TestCase):
    def test_password_hash_round_trip(self):
        encoded = hash_password("a correct horse battery staple")
        self.assertTrue(verify_password("a correct horse battery staple", encoded))
        self.assertFalse(verify_password("wrong password", encoded))
        self.assertFalse(is_legacy_password_hash(encoded))

    def test_legacy_sha256_hash_is_supported(self):
        import hashlib

        encoded = hashlib.sha256(b"legacy password").hexdigest()
        self.assertTrue(is_legacy_password_hash(encoded))
        self.assertTrue(verify_password("legacy password", encoded))


if __name__ == "__main__":
    unittest.main()
