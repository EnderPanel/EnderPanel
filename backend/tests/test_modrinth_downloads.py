import hashlib
import os
import tempfile
import unittest

import httpx
from fastapi import HTTPException

from routes.plugins import _download_modrinth_file


class StubClient:
    def __init__(self, response: httpx.Response):
        self.response = response

    async def get(self, _url: str) -> httpx.Response:
        return self.response


class ModrinthDownloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_verified_file_is_installed(self):
        content = b"valid jar bytes"
        response = httpx.Response(
            200,
            content=content,
            request=httpx.Request("GET", "https://cdn.example/mod.jar"),
        )
        file_info = {
            "url": "https://cdn.example/mod.jar",
            "filename": "mod.jar",
            "size": len(content),
            "hashes": {"sha512": hashlib.sha512(content).hexdigest()},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = await _download_modrinth_file(StubClient(response), file_info, directory)
            with open(path, "rb") as installed:
                self.assertEqual(installed.read(), content)

    async def test_bad_checksum_is_rejected_without_writing_target(self):
        response = httpx.Response(
            200,
            content=b"corrupt",
            request=httpx.Request("GET", "https://cdn.example/mod.jar"),
        )
        file_info = {
            "url": "https://cdn.example/mod.jar",
            "filename": "mod.jar",
            "hashes": {"sha512": "0" * 128},
        }
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(HTTPException):
                await _download_modrinth_file(StubClient(response), file_info, directory)
            self.assertFalse(os.path.exists(os.path.join(directory, "mod.jar")))


if __name__ == "__main__":
    unittest.main()
