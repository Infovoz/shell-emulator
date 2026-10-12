"""Unit tests for virtual file system and basic shell commands."""

import unittest
from src.vfs import VirtualFileSystem


class TestVfsCommands(unittest.TestCase):
    """Test suite for VFS logic operations."""

    def setUp(self) -> None:
        """Set up in-memory virtual filesystem for each test."""
        self.vfs = VirtualFileSystem()

    def test_default_structure(self) -> None:
        """Check initial root directory presence."""
        items = self.vfs.list_dir("/")
        self.assertIn("home/", items)
        self.assertIn("etc/", items)

    def test_cd_and_pwd(self) -> None:
        """Check directory traversal with relative and absolute paths."""
        self.vfs.change_dir("/home/user")
        self.assertEqual(self.vfs.current_dir, "/home/user")
        self.vfs.change_dir("..")
        self.assertEqual(self.vfs.current_dir, "/home")

    def test_cd_invalid_dir(self) -> None:
        """Verify error raising for non-existing directory."""
        with self.assertRaises(FileNotFoundError):
            self.vfs.change_dir("/nonexistent")

    def test_cat_command(self) -> None:
        """Verify reading file contents."""
        content = self.vfs.read_file("/home/user/readme.txt")
        self.assertIn("Welcome to in-memory VFS", content)

    def test_tac_command(self) -> None:
        """Verify reading file contents with reversed lines."""
        content = self.vfs.read_file_reversed("/home/user/readme.txt")
        lines = content.splitlines()
        self.assertTrue(lines[0].startswith("Line 2:"))


if __name__ == "__main__":
    unittest.main()