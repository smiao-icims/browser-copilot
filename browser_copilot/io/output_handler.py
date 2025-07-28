"""
Output handler for Browser Copilot

Handles formatting and writing test results in various formats.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.dom import minidom
from xml.etree import ElementTree as ET

import yaml


class OutputHandler:
    """Handles formatting and writing test results"""

    @staticmethod
    def format_output(
        results: dict[str, Any],
        format_type: str = "json",
        include_metadata: bool = True,
    ) -> str:
        """
        Format test results based on specified format

        Args:
            results: Test results dictionary
            format_type: Output format (json, yaml, xml, junit, html, markdown)
            include_metadata: Whether to include metadata in output

        Returns:
            Formatted output string
        """
        # Add metadata if requested
        if include_metadata:
            results = OutputHandler._add_metadata(results)

        formatters = {
            "json": OutputHandler._format_json,
            "yaml": OutputHandler._format_yaml,
            "xml": OutputHandler._format_xml,
            "junit": OutputHandler._format_junit,
            "html": OutputHandler._format_html,
            "markdown": OutputHandler._format_markdown,
        }

        formatter = formatters.get(format_type, OutputHandler._format_json)
        return formatter(results)

    @staticmethod
    def write_output(
        content: str, file_path: Path | None = None, append: bool = False
    ) -> None:
        """
        Write formatted output to file or stdout

        Args:
            content: Formatted content to write
            file_path: Optional file path. If None, writes to stdout
            append: Whether to append to existing file
        """
        if file_path:
            mode = "a" if append else "w"
            with open(file_path, mode, encoding="utf-8") as f:
                f.write(content)
                if append:
                    f.write("\n")
        else:
            print(content)

    @staticmethod
    def _add_metadata(results: dict[str, Any]) -> dict[str, Any]:
        """Add metadata to results"""
        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "framework": "browser-copilot",
            },
            "results": results,
        }

    @staticmethod
    def _format_json(results: dict[str, Any]) -> str:
        """Format as JSON"""
        return json.dumps(results, indent=2, ensure_ascii=False)

    @staticmethod
    def _format_yaml(results: dict[str, Any]) -> str:
        """Format as YAML"""
        return yaml.dump(results, default_flow_style=False, allow_unicode=True)

    @staticmethod
    def _format_xml(results: dict[str, Any]) -> str:
        """Format as XML"""
        root = ET.Element("testResults")
        OutputHandler._dict_to_xml(results, root)

        # Pretty print
        rough_string = ET.tostring(root, encoding="unicode")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    @staticmethod
    def _dict_to_xml(data: Any, parent: ET.Element, name: str = None) -> None:
        """Convert dictionary to XML elements"""
        if isinstance(data, dict):
            for key, value in data.items():
                child = ET.SubElement(parent, key)
                OutputHandler._dict_to_xml(value, child)
        elif isinstance(data, list):
            for item in data:
                item_elem = ET.SubElement(parent, name or "item")
                OutputHandler._dict_to_xml(item, item_elem)
        else:
            parent.text = str(data)

    @staticmethod
    def _format_junit(results: dict[str, Any]) -> str:
        """Format as JUnit XML"""
        # Extract test information
        test_name = results.get("test_name", "Browser Test")
        status = results.get("status", "unknown")
        duration = results.get("duration", 0)

        # Create JUnit structure
        testsuites = ET.Element("testsuites")
        testsuite = ET.SubElement(
            testsuites,
            "testsuite",
            {
                "name": "Browser Copilot Tests",
                "tests": "1",
                "failures": "1" if status == "failed" else "0",
                "errors": "1" if status == "error" else "0",
                "time": str(duration),
            },
        )

        testcase = ET.SubElement(
            testsuite,
            "testcase",
            {"name": test_name, "classname": "BrowserPilot", "time": str(duration)},
        )

        # Add failure/error information if applicable
        if status == "failed":
            failure = ET.SubElement(
                testcase, "failure", {"message": results.get("error", "Test failed")}
            )
            failure.text = results.get("error_details", "")
        elif status == "error":
            error = ET.SubElement(
                testcase, "error", {"message": results.get("error", "Test error")}
            )
            error.text = results.get("error_details", "")

        # Add system output
        if "logs" in results:
            system_out = ET.SubElement(testcase, "system-out")
            system_out.text = "\n".join(results["logs"])

        # Pretty print
        rough_string = ET.tostring(testsuites, encoding="unicode")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    @staticmethod
    def _format_html(results: dict[str, Any]) -> str:
        """Format as HTML report"""
        status = results.get("status", "unknown")
        status_color = {
            "passed": "#28a745",
            "failed": "#dc3545",
            "error": "#ffc107",
            "unknown": "#6c757d",
        }.get(status, "#6c757d")

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Browser Copilot Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .status {{ color: white; padding: 5px 10px; border-radius: 3px; background-color: {status_color}; }}
        .section {{ margin: 20px 0; }}
        .steps {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
        .metrics {{ display: flex; gap: 20px; }}
        .metric {{ background-color: #e9ecef; padding: 10px; border-radius: 5px; }}
        pre {{ background-color: #f5f5f5; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Browser Copilot Test Report</h1>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    
    <div class="section">
        <h2>Test Summary</h2>
        <p><strong>Test Name:</strong> {results.get("test_name", "Browser Test")}</p>
        <p><strong>Status:</strong> <span class="status">{status.upper()}</span></p>
        <p><strong>Duration:</strong> {results.get("duration", 0):.2f} seconds</p>
    </div>
"""

        # Add metrics if available
        if "metrics" in results:
            html += """
    <div class="section">
        <h2>Metrics</h2>
        <div class="metrics">
"""
            for key, value in results["metrics"].items():
                html += f'            <div class="metric"><strong>{key}:</strong> {value}</div>\n'
            html += """        </div>
    </div>
"""

        # Add steps if available
        if "steps" in results:
            html += """
    <div class="section">
        <h2>Test Steps</h2>
        <div class="steps">
"""
            for i, step in enumerate(results["steps"], 1):
                html += f"            <p>{i}. {step}</p>\n"
            html += """        </div>
    </div>
"""

        # Add error details if failed
        if status in ["failed", "error"] and "error_details" in results:
            html += f"""
    <div class="section">
        <h2>Error Details</h2>
        <pre>{results["error_details"]}</pre>
    </div>
"""

        html += """
</body>
</html>"""

        return html

    @staticmethod
    def _format_markdown(results: dict[str, Any]) -> str:
        """Format as Markdown report"""
        # Handle wrapped results (when include_metadata=True)
        if "metadata" in results and "results" in results:
            actual_results = results["results"]
        else:
            actual_results = results

        # Determine status from success field or status field
        if "success" in actual_results:
            status = "passed" if actual_results["success"] else "failed"
        else:
            status = actual_results.get("status", "unknown")

        status_emoji = {
            "passed": "✅",
            "failed": "❌",
            "error": "⚠️",
            "unknown": "❓",
        }.get(status, "❓")

        # Format execution time information
        execution_time_info = ""
        if "execution_time" in actual_results:
            exec_time = actual_results["execution_time"]
            start_time = exec_time.get("start", "N/A")
            end_time = exec_time.get("end", "N/A")
            timezone = exec_time.get("timezone", "UTC")
            duration = exec_time.get(
                "duration_seconds", actual_results.get("duration_seconds", 0)
            )
            execution_time_info = f"""- **Start Time:** {start_time} ({timezone})
- **End Time:** {end_time} ({timezone})
- **Duration:** {duration:.2f} seconds"""
        else:
            # Fallback to simple duration
            duration = actual_results.get(
                "duration_seconds", actual_results.get("duration", 0)
            )
            execution_time_info = f"- **Duration:** {duration:.2f} seconds"

        md = f"""# Browser Copilot Test Report

## Test Summary

- **Test Name:** {actual_results.get("test_name", "Browser Test")}
- **Status:** {status_emoji} {status.upper()}
{execution_time_info}
- **Browser:** {actual_results.get("browser", "Unknown")}
- **Provider:** {actual_results.get("provider", "Unknown")}
- **Model:** {actual_results.get("model", "Unknown")}

"""

        # Add token usage if available
        if "token_usage" in actual_results and actual_results["token_usage"]:
            usage = actual_results["token_usage"]
            md += "## Token Usage\n\n"
            if "total_tokens" in usage:
                md += f"- **Total Tokens:** {usage.get('total_tokens', 0):,}\n"
            if "prompt_tokens" in usage:
                md += f"- **Prompt Tokens:** {usage.get('prompt_tokens', 0):,}\n"
            if "completion_tokens" in usage:
                md += (
                    f"- **Completion Tokens:** {usage.get('completion_tokens', 0):,}\n"
                )
            if "estimated_cost" in usage:
                md += f"- **Estimated Cost:** ${usage.get('estimated_cost', 0):.4f}\n"

            # Add context length information
            if "context_length" in usage:
                md += "\n### Context Length\n\n"
                md += f"- **Context Used:** {usage.get('context_length', 0):,} tokens\n"
                if "max_context_length" in usage:
                    md += f"- **Model Limit:** {usage.get('max_context_length', 0):,} tokens\n"
                    if "context_usage_percentage" in usage:
                        percentage = usage.get("context_usage_percentage", 0)
                        # Add warning if context usage is high
                        if percentage >= 80:
                            md += f"- **Usage:** {percentage}% ⚠️ (approaching limit)\n"
                        elif percentage >= 60:
                            md += f"- **Usage:** {percentage}% ⚡ (moderate usage)\n"
                        else:
                            md += f"- **Usage:** {percentage}% ✅\n"
                else:
                    md += "- **Model Limit:** Unknown\n"

            # Add disclaimer for GitHub Copilot
            if actual_results.get("provider") == "github_copilot":
                md += "\n> **Note:** Cost estimates for GitHub Copilot are approximate. Actual costs depend on your GitHub Copilot subscription plan.\n"

            # Add optimization info if available
            if "optimization" in usage:
                opt = usage["optimization"]
                md += "\n### Token Optimization\n\n"
                md += f"- **Reduction:** {opt.get('reduction_percentage', 0):.1f}%\n"
                if "estimated_savings" in opt:
                    md += f"- **Estimated Savings:** ${opt['estimated_savings']:.4f}\n"
            md += "\n"

        # Add metrics if available
        if "metrics" in actual_results:
            md += "## Performance Metrics\n\n"
            for key, value in actual_results["metrics"].items():
                # Format key nicely
                formatted_key = key.replace("_", " ").title()
                md += f"- **{formatted_key}:** {value}\n"
            md += "\n"

        # Add steps if available
        if "steps" in actual_results:
            md += "## Test Steps\n\n"
            for i, step in enumerate(actual_results["steps"], 1):
                if isinstance(step, dict):
                    step_type = step.get("type", "unknown")
                    if step_type == "tool_call":
                        md += f"{i}. **Tool Call:** {step.get('name', 'Unknown')}\n"
                        if "content" in step:
                            content = step["content"]
                            # Extract meaningful first line or snippet
                            lines = content.split("\n")
                            first_line = lines[0].strip()

                            # If it's a code block, try to get the actual code
                            if "```" in content:
                                # Extract code between triple backticks
                                code_start = content.find("```")
                                code_end = content.find("```", code_start + 3)
                                if code_start != -1 and code_end != -1:
                                    # Extract just the code content, not the backticks
                                    code_content = content[
                                        code_start + 3 : code_end
                                    ].strip()
                                    # Find language identifier if present
                                    first_newline = code_content.find("\n")
                                    if (
                                        first_newline > 0 and first_newline < 20
                                    ):  # Likely a language identifier
                                        lang = code_content[:first_newline].strip()
                                        code_body = code_content[
                                            first_newline + 1 :
                                        ].strip()
                                    else:
                                        lang = (
                                            "js"  # Default to JavaScript for Playwright
                                        )
                                        code_body = code_content

                                    # Truncate if too long
                                    if len(code_body) > 200:
                                        code_body = code_body[:200] + "..."

                                    md += f"\n   ```{lang}\n   {code_body}\n   ```\n"
                                else:
                                    # Fallback to first line
                                    if len(first_line) > 200:
                                        first_line = first_line[:200] + "..."
                                    md += f"   - {first_line}\n"
                            else:
                                # For non-code content, show more context
                                if len(content) > 300:
                                    md += f"   - {content[:300]}...\n"
                                else:
                                    md += f"   - {content}\n"
                    elif step_type == "agent_message":
                        content = step.get("content", "")
                        if len(content) > 200:
                            md += f"{i}. **Agent:** {content[:200]}...\n"
                        else:
                            md += f"{i}. **Agent:** {content}\n"
                else:
                    md += f"{i}. {step}\n"
            md += "\n"

        # Add error details if failed
        if status in ["failed", "error"]:
            if "error" in actual_results:
                md += f"""## Error Details

{actual_results["error"]}

"""
            elif "error_details" in actual_results:
                md += f"""## Error Details

```
{actual_results["error_details"]}
```
"""

        # Add report content if available
        if "report" in actual_results and actual_results["report"]:
            md += "## Test Execution Report\n\n"
            md += actual_results["report"]
            md += "\n\n"

        # Add logs if available
        if "logs" in actual_results and actual_results["logs"]:
            md += "## Execution Logs\n\n```\n"
            md += "\n".join(actual_results["logs"][-10:])  # Last 10 log entries
            md += "\n```\n"

        return md
