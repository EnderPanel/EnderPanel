import io
import os
import tarfile
import tempfile
import unittest

from fastapi import HTTPException
from routes.update import is_newer_version, safe_extract_tar


class UpdateTests(unittest.TestCase):
    def test_version_comparison(self):
        self.assertTrue(is_newer_version("4.2.1", "4.2.0"))
        self.assertFalse(is_newer_version("4.2", "4.2.0"))
        self.assertFalse(is_newer_version("invalid", "4.2.0"))

    def test_tar_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_path = os.path.join(directory, "update.tar.gz")
            with tarfile.open(archive_path, "w:gz") as archive:
                info = tarfile.TarInfo("../outside.txt")
                payload = b"unsafe"
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
            with tarfile.open(archive_path, "r:gz") as archive:
                with self.assertRaises(HTTPException):
                    safe_extract_tar(archive, os.path.join(directory, "extract"))

    def test_tar_special_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_path = os.path.join(directory, "update.tar.gz")
            with tarfile.open(archive_path, "w:gz") as archive:
                info = tarfile.TarInfo("unsafe-fifo")
                info.type = tarfile.FIFOTYPE
                archive.addfile(info)
            with tarfile.open(archive_path, "r:gz") as archive:
                with self.assertRaises(HTTPException):
                    safe_extract_tar(archive, os.path.join(directory, "extract"))


if __name__ == "__main__":
    unittest.main()
