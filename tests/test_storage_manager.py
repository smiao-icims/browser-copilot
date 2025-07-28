"""
Unit tests for StorageManager

Tests cross-platform storage functionality including Windows and macOS paths.
"""

import os
import platform
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path to import storage_manager directly
sys.path.insert(0, str(Path(__file__).parent.parent / "browser_copilot"))
from storage_manager import StorageManager


@pytest.mark.unit
class TestStorageManager:
    """Test cases for StorageManager"""

    def test_directory_structure_creation(self, temp_dir):
        """Test that all required directories are created"""
        storage = StorageManager(base_dir=temp_dir)

        # Check all directories exist
        assert storage.get_logs_dir().exists()
        assert storage.get_settings_dir().exists()
        assert storage.get_memory_dir().exists()
        assert storage.get_reports_dir().exists()
        assert storage.get_screenshots_dir().exists()
        assert storage.get_cache_dir().exists()

    @patch("platform.system")
    def test_windows_default_path(self, mock_system):
        """Test Windows default storage path"""
        mock_system.return_value = "Windows"

        with patch.dict(
            os.environ, {"LOCALAPPDATA": "C:\\Users\\Test\\AppData\\Local"}
        ):
            storage = StorageManager()
            # Implementation uses ~/.browser_copilot for all platforms for consistency
            expected = Path.home() / ".browser_copilot"
            assert storage.base_dir == expected

    @patch("platform.system")
    def test_macos_default_path(self, mock_system):
        """Test macOS default storage path"""
        mock_system.return_value = "Darwin"

        with patch("pathlib.Path.home", return_value=Path("/Users/test")):
            storage = StorageManager()
            # Implementation uses ~/.browser_copilot for all platforms for consistency
            expected = Path("/Users/test/.browser_copilot")
            assert storage.base_dir == expected

    @patch("platform.system")
    def test_linux_default_path(self, mock_system):
        """Test Linux default storage path"""
        mock_system.return_value = "Linux"

        with patch("pathlib.Path.home", return_value=Path("/home/test")):
            storage = StorageManager()
            expected = Path("/home/test/.browser_copilot")
            assert storage.base_dir == expected

    def test_save_and_get_setting(self, temp_dir):
        """Test saving and retrieving settings"""
        storage = StorageManager(base_dir=temp_dir)

        # Save a setting
        storage.save_setting("test_key", "test_value")

        # Retrieve the setting
        value = storage.get_setting("test_key")
        assert value == "test_value"

        # Test default value for non-existent key
        default = storage.get_setting("non_existent", "default")
        assert default == "default"

    def test_save_complex_setting(self, temp_dir):
        """Test saving complex data types"""
        storage = StorageManager(base_dir=temp_dir)

        complex_data = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }

        storage.save_setting("complex", complex_data)
        retrieved = storage.get_setting("complex")

        assert retrieved == complex_data

    def test_multiple_settings_files(self, temp_dir):
        """Test using multiple settings files"""
        storage = StorageManager(base_dir=temp_dir)

        # Save to different files
        storage.save_setting("key1", "value1", "file1")
        storage.save_setting("key2", "value2", "file2")

        # Retrieve from specific files
        assert storage.get_setting("key1", settings_file="file1") == "value1"
        assert storage.get_setting("key2", settings_file="file2") == "value2"

        # Check isolation between files
        assert storage.get_setting("key1", settings_file="file2") is None
        assert storage.get_setting("key2", settings_file="file1") is None

    def test_get_all_settings(self, temp_dir):
        """Test retrieving all settings from a file"""
        storage = StorageManager(base_dir=temp_dir)

        settings = {"key1": "value1", "key2": 42, "key3": [1, 2, 3]}

        for key, value in settings.items():
            storage.save_setting(key, value)

        all_settings = storage.get_all_settings()
        assert all_settings == settings

    def test_cleanup_old_logs(self, temp_dir):
        """Test log cleanup functionality"""
        storage = StorageManager(base_dir=temp_dir)
        logs_dir = storage.get_logs_dir()

        # Create test log files with different ages
        old_file = logs_dir / "old.log"
        recent_file = logs_dir / "recent.log"

        # Create files
        old_file.write_text("old log")
        recent_file.write_text("recent log")

        # Modify timestamps
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        recent_time = (datetime.now() - timedelta(days=2)).timestamp()

        os.utime(old_file, (old_time, old_time))
        os.utime(recent_file, (recent_time, recent_time))

        # Run cleanup
        deleted = storage.cleanup_old_logs(days=7)

        # Check results
        assert deleted == 1
        assert not old_file.exists()
        assert recent_file.exists()

    def test_cleanup_old_files_generic(self, temp_dir):
        """Test generic file cleanup"""
        storage = StorageManager(base_dir=temp_dir)
        screenshots_dir = storage.get_screenshots_dir()

        # Create test files
        old_png = screenshots_dir / "old.png"
        old_jpg = screenshots_dir / "old.jpg"
        recent_png = screenshots_dir / "recent.png"

        for f in [old_png, old_jpg, recent_png]:
            f.write_text("test")

        # Set old timestamps
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_png, (old_time, old_time))
        os.utime(old_jpg, (old_time, old_time))

        # Cleanup only PNG files
        deleted = storage.cleanup_old_files("screenshots", "*.png", days=7)

        assert deleted == 1
        assert not old_png.exists()
        assert old_jpg.exists()  # JPG not matched by pattern
        assert recent_png.exists()

    def test_storage_info(self, temp_dir):
        """Test storage information retrieval"""
        storage = StorageManager(base_dir=temp_dir)

        # Create some test files
        logs_dir = storage.get_logs_dir()
        reports_dir = storage.get_reports_dir()

        (logs_dir / "test1.log").write_text("A" * 1000)
        (logs_dir / "test2.log").write_text("B" * 2000)
        (reports_dir / "report.md").write_text("C" * 1500)

        info = storage.get_storage_info()

        # Check structure
        assert "base_directory" in info
        assert "platform" in info
        assert "directories" in info
        assert "total_size_bytes" in info
        assert "total_files" in info

        # Check calculations
        assert info["total_files"] == 3
        assert info["total_size_bytes"] == 4500
        assert info["directories"]["logs"]["file_count"] == 2
        assert info["directories"]["logs"]["size_bytes"] == 3000

    def test_format_bytes(self, temp_dir):
        """Test byte formatting"""
        storage = StorageManager(base_dir=temp_dir)

        assert storage._format_bytes(0) == "0.00 B"
        assert storage._format_bytes(1023) == "1023.00 B"
        assert storage._format_bytes(1024) == "1.00 KB"
        assert storage._format_bytes(1024 * 1024) == "1.00 MB"
        assert storage._format_bytes(1024 * 1024 * 1024) == "1.00 GB"

    def test_clear_cache(self, temp_dir):
        """Test cache clearing"""
        storage = StorageManager(base_dir=temp_dir)
        cache_dir = storage.get_cache_dir()

        # Create test files and directories
        (cache_dir / "file1.tmp").write_text("test")
        (cache_dir / "file2.tmp").write_text("test")
        subdir = cache_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.tmp").write_text("test")

        # Clear cache
        deleted = storage.clear_cache()

        # Check all cleared
        assert deleted >= 2  # At least files, may count directory
        assert len(list(cache_dir.iterdir())) == 0

    def test_export_import_settings(self, temp_dir):
        """Test settings export and import"""
        storage = StorageManager(base_dir=temp_dir)

        # Create settings in multiple files
        storage.save_setting("key1", "value1", "config")
        storage.save_setting("key2", "value2", "config")
        storage.save_setting("key3", "value3", "preferences")

        # Export settings
        export_path = temp_dir / "export.json"
        storage.export_settings(export_path)

        # Create new storage instance
        new_temp = temp_dir / "new_storage"
        new_temp.mkdir()
        new_storage = StorageManager(base_dir=new_temp)

        # Import settings
        new_storage.import_settings(export_path)

        # Verify imported settings
        assert new_storage.get_setting("key1", settings_file="config") == "value1"
        assert new_storage.get_setting("key2", settings_file="config") == "value2"
        assert new_storage.get_setting("key3", settings_file="preferences") == "value3"

    def test_atomic_write(self, temp_dir):
        """Test atomic write prevents corruption"""
        storage = StorageManager(base_dir=temp_dir)

        # This test simulates a write failure
        _ = storage.get_settings_file("test")

        # Pre-populate with data
        storage.save_setting("existing", "data", "test")

        # Mock a write failure
        with patch("builtins.open", side_effect=OSError("Write failed")):
            with pytest.raises(IOError):
                storage.save_setting("new", "data", "test")

        # Original data should still be intact
        assert storage.get_setting("existing", settings_file="test") == "data"

    def test_permission_error_handling(self, temp_dir):
        """Test handling of permission errors"""
        # Create a storage manager with a read-only directory
        if platform.system() != "Windows":
            read_only_dir = temp_dir / "readonly"
            read_only_dir.mkdir()
            os.chmod(read_only_dir, 0o444)

            # Should not raise an exception, just warn
            _ = StorageManager(base_dir=read_only_dir)

            # Restore permissions for cleanup
            os.chmod(read_only_dir, 0o755)

    def test_corrupted_settings_file(self, temp_dir):
        """Test handling of corrupted JSON files"""
        storage = StorageManager(base_dir=temp_dir)
        settings_path = storage.get_settings_file("corrupted")

        # Write invalid JSON
        settings_path.write_text("{ invalid json ]")

        # Should return default value, not raise
        value = storage.get_setting("key", "default", "corrupted")
        assert value == "default"

        # Should return empty dict for all settings
        all_settings = storage.get_all_settings("corrupted")
        assert all_settings == {}

        # Should be able to save new settings (overwriting corrupted file)
        storage.save_setting("new_key", "new_value", "corrupted")
        assert storage.get_setting("new_key", settings_file="corrupted") == "new_value"
