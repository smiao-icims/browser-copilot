"""
Storage Manager for Browser Copilot

Manages local storage for logs, settings, memory, and other persistent data.
Cross-platform compatible (Windows, macOS, Linux).
"""

import json
import os
import platform
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class StorageManager:
    """Manages local storage for Browser Copilot with cross-platform support"""

    def __init__(self, base_dir: Path | None = None):
        """
        Initialize StorageManager with platform-appropriate paths

        Args:
            base_dir: Optional custom base directory. If not provided,
                     uses platform-specific default location.
        """
        self.base_dir = base_dir or self._get_default_base_dir()
        self._ensure_directory_structure()

    def _get_default_base_dir(self) -> Path:
        """
        Get default storage directory - using ~/.browser_copilot for all platforms

        This provides:
        - Consistency across all platforms
        - Easy access for CLI users
        - Follows Unix convention for CLI tools
        - Simple to remember and type

        Returns:
            Path to ~/.browser_copilot directory
        """
        return Path.home() / ".browser_copilot"

    def _ensure_directory_structure(self) -> None:
        """Create necessary directories with proper permissions"""
        directories = [
            self.base_dir,
            self.get_logs_dir(),
            self.get_settings_dir(),
            self.get_memory_dir(),
            self.get_reports_dir(),
            self.get_screenshots_dir(),
            self.get_cache_dir(),
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)

                # Set appropriate permissions (Unix-like systems)
                if platform.system() != "Windows":
                    os.chmod(directory, 0o755)

            except Exception as e:
                # Handle permission errors gracefully
                print(f"Warning: Could not create directory {directory}: {e}")

    def get_logs_dir(self) -> Path:
        """Get logs directory path"""
        return self.base_dir / "logs"

    def get_settings_dir(self) -> Path:
        """Get settings directory path"""
        return self.base_dir / "settings"

    def get_memory_dir(self) -> Path:
        """Get memory directory path (for future features)"""
        return self.base_dir / "memory"

    def get_reports_dir(self) -> Path:
        """Get reports directory path"""
        return self.base_dir / "reports"

    def get_screenshots_dir(self) -> Path:
        """Get screenshots directory path"""
        return self.base_dir / "screenshots"

    def get_cache_dir(self) -> Path:
        """Get cache directory path"""
        return self.base_dir / "cache"

    def get_settings_file(self, name: str = "config") -> Path:
        """
        Get settings file path

        Args:
            name: Settings file name (without extension)

        Returns:
            Path to settings file
        """
        return self.get_settings_dir() / f"{name}.json"

    def save_setting(self, key: str, value: Any, settings_file: str = "config") -> None:
        """
        Save a setting to local storage

        Args:
            key: Setting key
            value: Setting value (must be JSON serializable)
            settings_file: Name of settings file (without extension)
        """
        settings_path = self.get_settings_file(settings_file)
        settings = {}

        # Load existing settings
        if settings_path.exists():
            try:
                with open(settings_path, encoding="utf-8") as f:
                    settings = json.load(f)
            except (OSError, json.JSONDecodeError):
                # If file is corrupted, start fresh
                settings = {}

        # Update setting
        settings[key] = value

        # Save with atomic write (write to temp file then rename)
        temp_path = settings_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)

            # Atomic rename (works on both Unix and Windows)
            temp_path.replace(settings_path)

        except Exception as e:
            # Clean up temp file if something went wrong
            if temp_path.exists():
                temp_path.unlink()
            raise e

    def get_setting(
        self, key: str, default: Any = None, settings_file: str = "config"
    ) -> Any:
        """
        Get a setting from local storage

        Args:
            key: Setting key
            default: Default value if key not found
            settings_file: Name of settings file (without extension)

        Returns:
            Setting value or default
        """
        settings_path = self.get_settings_file(settings_file)

        if not settings_path.exists():
            return default

        try:
            with open(settings_path, encoding="utf-8") as f:
                settings = json.load(f)
                return settings.get(key, default)
        except (OSError, json.JSONDecodeError):
            return default

    def get_all_settings(self, settings_file: str = "config") -> dict[str, Any]:
        """
        Get all settings from a settings file

        Args:
            settings_file: Name of settings file (without extension)

        Returns:
            Dictionary of all settings
        """
        settings_path = self.get_settings_file(settings_file)

        if not settings_path.exists():
            return {}

        try:
            with open(settings_path, encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def cleanup_old_logs(self, days: int = 7) -> int:
        """
        Remove logs older than specified days

        Args:
            days: Number of days to keep logs

        Returns:
            Number of files deleted
        """
        if days <= 0:
            return 0

        cutoff_time = datetime.now() - timedelta(days=days)
        logs_dir = self.get_logs_dir()
        deleted_count = 0

        if not logs_dir.exists():
            return 0

        for log_file in logs_dir.glob("*.log"):
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

                if mtime < cutoff_time:
                    log_file.unlink()
                    deleted_count += 1

            except Exception as e:
                # Skip files that can't be accessed
                print(f"Warning: Could not process {log_file}: {e}")
                continue

        return deleted_count

    def cleanup_old_files(
        self, directory: str | Path, pattern: str = "*", days: int = 7
    ) -> int:
        """
        Generic cleanup for any directory

        Args:
            directory: Directory name or path
            pattern: File pattern to match (default: all files)
            days: Number of days to keep files

        Returns:
            Number of files deleted
        """
        if isinstance(directory, str):
            # Convert string directory names to paths
            dir_map = {
                "logs": self.get_logs_dir(),
                "reports": self.get_reports_dir(),
                "screenshots": self.get_screenshots_dir(),
                "cache": self.get_cache_dir(),
            }
            dir_path = dir_map.get(directory, Path(directory))
        else:
            dir_path = Path(directory)

        if not dir_path.exists():
            return 0

        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for file_path in dir_path.glob(pattern):
            if not file_path.is_file():
                continue

            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                if mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1

            except Exception:
                continue

        return deleted_count

    def get_storage_info(self) -> dict[str, Any]:
        """
        Get information about storage usage

        Returns:
            Dictionary with storage statistics
        """
        info: dict[str, Any] = {
            "base_directory": str(self.base_dir),
            "platform": platform.system(),
            "directories": {},
            "total_size_bytes": 0,
            "total_files": 0,
        }

        # Calculate size for each directory
        for name, directory in [
            ("logs", self.get_logs_dir()),
            ("settings", self.get_settings_dir()),
            ("memory", self.get_memory_dir()),
            ("reports", self.get_reports_dir()),
            ("screenshots", self.get_screenshots_dir()),
            ("cache", self.get_cache_dir()),
        ]:
            if directory.exists():
                size = 0
                count = 0

                for file_path in directory.rglob("*"):
                    if file_path.is_file():
                        try:
                            size += file_path.stat().st_size
                            count += 1
                        except Exception:
                            continue

                info["directories"][name] = {
                    "path": str(directory),
                    "size_bytes": size,
                    "file_count": count,
                    "size_human": self._format_bytes(size),
                }
                info["total_size_bytes"] += size
                info["total_files"] += count

        info["total_size_human"] = self._format_bytes(info["total_size_bytes"])
        return info

    def _format_bytes(self, bytes_size: int) -> str:
        """Format bytes to human readable string"""
        size_float = float(bytes_size)
        for unit in ["B", "KB", "MB", "GB"]:
            if size_float < 1024.0:
                return f"{size_float:.2f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.2f} TB"

    def clear_cache(self) -> int:
        """
        Clear all cache files

        Returns:
            Number of files deleted
        """
        cache_dir = self.get_cache_dir()
        if not cache_dir.exists():
            return 0

        deleted_count = 0
        for file_path in cache_dir.glob("*"):
            try:
                if file_path.is_file():
                    file_path.unlink()
                    deleted_count += 1
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    deleted_count += 1
            except Exception:
                continue

        return deleted_count

    def export_settings(self, export_path: Path) -> None:
        """Export all settings to a file"""
        settings_dir = self.get_settings_dir()
        all_settings = {}

        if settings_dir.exists():
            for settings_file in settings_dir.glob("*.json"):
                try:
                    with open(settings_file, encoding="utf-8") as f:
                        settings_name = settings_file.stem
                        all_settings[settings_name] = json.load(f)
                except Exception:
                    continue

        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(all_settings, f, indent=2)

    def import_settings(self, import_path: Path) -> None:
        """Import settings from a file"""
        with open(import_path, encoding="utf-8") as f:
            all_settings = json.load(f)

        for settings_name, settings_data in all_settings.items():
            settings_path = self.get_settings_file(settings_name)
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, indent=2)
