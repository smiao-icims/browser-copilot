"""
Integration tests for Browser Copilot

These tests verify that different components work together correctly.
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path to import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent / "browser_copilot"))
import reporter
from config_manager import ConfigManager
from storage_manager import StorageManager
from token_optimizer import OptimizationLevel, TokenOptimizer
from verbose_logger import VerboseLogger

from browser_copilot.io import InputHandler, OutputHandler


@pytest.mark.integration
class TestIntegration:
    """Integration tests for Browser Copilot components"""

    def test_storage_and_config_integration(self, temp_dir):
        """Test StorageManager and ConfigManager work together"""
        # Create storage manager
        storage = StorageManager(base_dir=temp_dir)

        # Create config manager with storage
        config = ConfigManager(storage_manager=storage)

        # Set some configuration
        config.set("test_key", "test_value")
        config.set("browser", "firefox")

        # Create new instances to verify persistence
        storage2 = StorageManager(base_dir=temp_dir)
        config2 = ConfigManager(storage_manager=storage2)

        # Verify values persist
        assert config2.get("test_key") == "test_value"
        assert config2.get("browser") == "firefox"

    def test_verbose_logger_with_storage(self, temp_dir):
        """Test VerboseLogger integrates with StorageManager"""
        # Create storage
        storage = StorageManager(base_dir=temp_dir)
        log_dir = storage.get_logs_dir()

        # Create logger with storage manager
        logger = VerboseLogger(storage_manager=storage)

        try:
            # Log some test messages
            logger.log_step("test", "Test message")  # Using correct method signature
            logger.log_step("step", "Test step", level="INFO")
            logger.log_error("test_error", "Test error")

            # Verify log file was created in storage location
            log_files = list(log_dir.glob("*.log"))
            assert len(log_files) > 0

            # Verify content
            log_content = log_files[0].read_text()
            assert "Test message" in log_content
            assert "Test step" in log_content
            assert "Test error" in log_content
        finally:
            # Close logger to release file handles
            logger.close()

    def test_token_optimizer_with_config(self, temp_dir):
        """Test TokenOptimizer respects ConfigManager settings"""
        # Create storage and config
        storage = StorageManager(base_dir=temp_dir)
        config = ConfigManager(storage_manager=storage)

        # Set optimization settings
        config.set("token_optimization", True)
        config.set("compression_level", "high")

        # Create optimizer based on config
        if config.get("token_optimization"):
            level_map = {
                "none": OptimizationLevel.NONE,
                "low": OptimizationLevel.LOW,
                "medium": OptimizationLevel.MEDIUM,
                "high": OptimizationLevel.HIGH,
            }
            level = level_map.get(
                config.get("compression_level"), OptimizationLevel.MEDIUM
            )
            optimizer = TokenOptimizer(level)

            # Test optimization
            result = optimizer.optimize_prompt("Please navigate to the website")
            assert len(result) < len("Please navigate to the website")

    def test_io_handlers_with_reporter(self, temp_dir, capsys):
        """Test IO handlers work with reporter"""
        # Create test result
        test_result = {
            "success": True,
            "duration_seconds": 10,
            "steps_executed": 5,
            "report": "Test completed successfully",
        }

        # Use output handler to format
        output_handler = OutputHandler()

        # Test different formats
        json_output = output_handler.format_output(test_result, "json")
        parsed = json.loads(json_output)
        assert parsed["results"]["success"] is True

        # Test reporter can display the result
        reporter.print_results(test_result)
        captured = capsys.readouterr()
        assert "✅ PASSED" in captured.out

    def test_full_pipeline(self, temp_dir, capsys):
        """Test complete pipeline from input to output"""
        # Create test input file
        test_file = temp_dir / "test_scenario.md"
        test_content = """# Integration Test
1. Navigate to example.com
2. Click button
3. Verify success"""
        test_file.write_text(test_content)

        # 1. Read input
        input_handler = InputHandler()
        scenario = input_handler.read_from_file(test_file)
        assert scenario == test_content

        # 2. Create configuration
        storage = StorageManager(base_dir=temp_dir)
        config = ConfigManager(storage_manager=storage)
        config.set("output_format", "json")

        # 3. Create logger
        logger = VerboseLogger(storage_manager=storage)
        try:
            # 4. Simulate test execution with token optimization
            optimizer = TokenOptimizer(OptimizationLevel.MEDIUM)
            optimized_scenario = optimizer.optimize_prompt(scenario)

            logger.log_step("optimization", f"Original length: {len(scenario)}")
            logger.log_step(
                "optimization", f"Optimized length: {len(optimized_scenario)}"
            )

            # 5. Create result
            test_result = {
                "success": True,
                "test_name": "pipeline_test",
                "duration_seconds": 5.5,
                "steps_executed": 3,
                "report": "All steps completed",
                "token_usage": {
                    "total_tokens": 100,
                    "estimated_cost": 0.002,
                    "optimization": optimizer.get_metrics(),
                },
            }

            # 6. Save results
            saved_files = reporter.save_results(
                test_result, str(storage.get_reports_dir())
            )

            # 7. Verify files created
            assert saved_files["report"].exists()
            assert saved_files["results"].exists()

            # 8. Display results
            reporter.print_results(test_result)

            # 9. Use output handler for final output
            output_handler = OutputHandler()
            formatted_output = output_handler.format_output(
                test_result, config.get("output_format")
            )
            output_handler.write_output(formatted_output)

            captured = capsys.readouterr()
            assert "✅ PASSED" in captured.out
        finally:
            # Close logger to release file handles
            logger.close()

    def test_error_handling_integration(self, temp_dir, capsys):
        """Test error handling across components"""
        # Create components
        storage = StorageManager(base_dir=temp_dir)
        _ = ConfigManager(storage_manager=storage)
        logger = VerboseLogger(storage_manager=storage)

        try:
            # Test error scenario
            error = Exception("Integration test error")
            logger.log_error(
                "integration_error", str(error), {"context": "During integration test"}
            )

            # Create failed result
            failed_result = {
                "success": False,
                "error": str(error),
                "duration_seconds": 2.0,
                "steps_executed": 1,
            }

            # Display and save
            reporter.print_results(failed_result)
            reporter.save_results(failed_result, str(storage.get_reports_dir()))

            # Verify error handling
            captured = capsys.readouterr()
            assert "❌ FAILED" in captured.out
            assert "Integration test error" in captured.out
        finally:
            # Close logger to release file handles
            logger.close()

        # Verify error logged
        log_files = list(storage.get_logs_dir().glob("*.log"))
        assert len(log_files) > 0
        log_content = log_files[0].read_text()
        assert "WARNING" in log_content
        assert "Integration test error" in log_content

    def test_config_priority_integration(self, temp_dir, monkeypatch):
        """Test configuration priority system works correctly"""
        # Create storage and config
        storage = StorageManager(base_dir=temp_dir)
        config = ConfigManager(storage_manager=storage)

        # Set config file value
        config.set("test_value", "from_file")

        # Set environment variable (higher priority)
        monkeypatch.setenv("BROWSER_PILOT_TEST_VALUE", "from_env")

        # Verify env var takes precedence
        assert config.get("test_value") == "from_env"

        # Set CLI args (highest priority)
        config.set_cli_args({"test_value": "from_cli"})

        # Verify CLI takes precedence
        assert config.get("test_value") == "from_cli"

    def test_cleanup_integration(self, temp_dir):
        """Test cleanup functionality across components"""
        # Create storage
        storage = StorageManager(base_dir=temp_dir)

        # Create old files in different directories
        from datetime import datetime, timedelta

        # Create old log
        old_log = storage.get_logs_dir() / "old.log"
        old_log.write_text("old log content")
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_log, (old_time, old_time))

        # Create recent log
        recent_log = storage.get_logs_dir() / "recent.log"
        recent_log.write_text("recent log")

        # Run cleanup
        deleted = storage.cleanup_old_logs(days=7)

        # Verify cleanup
        assert deleted == 1
        assert not old_log.exists()
        assert recent_log.exists()

    @pytest.mark.parametrize("output_format", ["json", "yaml", "xml", "markdown"])
    def test_output_formats_integration(self, temp_dir, output_format):
        """Test different output formats work correctly"""
        # Create test result
        test_result = {
            "success": True,
            "format_test": output_format,
            "data": {"key": "value"},
            "duration_seconds": 1.0,
        }

        # Format output
        handler = OutputHandler()
        formatted = handler.format_output(test_result, output_format)

        # Verify format
        assert len(formatted) > 0

        # Save to file
        output_file = temp_dir / f"output.{output_format}"
        handler.write_output(formatted, output_file)

        # Verify file created
        assert output_file.exists()
        assert output_file.stat().st_size > 0
