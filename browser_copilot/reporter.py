"""
Report generation and output utilities for Browser Copilot

This module handles test result formatting, saving, and display.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def print_header() -> None:
    """Print the Browser Copilot ASCII header"""
    print("╔═══════════════════════════════════════════╗")
    print("║      Browser Copilot v1.0                 ║")
    print("║   Simple • Reliable • Token Efficient     ║")
    print("╚═══════════════════════════════════════════╝")


def print_results(result: dict[str, Any], no_color: bool = False) -> None:
    """
    Print test execution results to console

    Args:
        result: Test execution results dictionary
        no_color: Disable colored output
    """
    print("\n" + "-" * 50)

    # Status
    if result.get("success"):
        status = "✅ PASSED" if not no_color else "PASSED"
    else:
        status = "❌ FAILED" if not no_color else "FAILED"

    print(f"Status: {status}")

    # Basic metrics
    print(f"Duration: {result.get('duration_seconds', 0):.1f}s")
    print(f"Steps: {result.get('steps_executed', 0)}")

    # Token usage
    if result.get("token_usage"):
        usage = result["token_usage"]
        print("\n📊 Token Usage:" if not no_color else "\nToken Usage:")
        print(f"   Total: {usage.get('total_tokens', 0):,}")
        print(f"   Prompt: {usage.get('prompt_tokens', 0):,}")
        print(f"   Completion: {usage.get('completion_tokens', 0):,}")
        if usage.get("estimated_cost", 0) > 0:
            print(f"   Cost: ${usage['estimated_cost']:.4f}")

        # Token optimization metrics
        if usage.get("optimization"):
            opt = usage["optimization"]
            print(
                "\n💡 Token Optimization:" if not no_color else "\nToken Optimization:"
            )
            print(f"   Reduction: {opt['reduction_percentage']:.1f}%")
            print(
                f"   Tokens Saved: {opt['original_tokens'] - opt['optimized_tokens']:,}"
            )
            if opt.get("estimated_savings"):
                print(f"   Cost Savings: ${opt['estimated_savings']:.4f}")
            print(f"   Strategies: {', '.join(opt['strategies_applied'])}")

    # Error if present
    if result.get("error"):
        print(f"\n{'❌' if not no_color else ''} Error: {result['error']}")


def save_results(
    result: dict[str, Any], output_dir: str = "reports"
) -> dict[str, Path]:
    """
    Save test results to disk in multiple formats

    Args:
        result: Test execution results
        output_dir: Directory to save results

    Returns:
        Dictionary mapping file types to their paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save markdown report
    report_path = output_path / f"report_{timestamp}.md"
    report_content = result.get("report", "No report generated")

    # Add metadata header to report
    metadata = f"""<!-- Browser Copilot Test Report
Generated: {result.get("timestamp", datetime.now().isoformat())}
Provider: {result.get("provider", "Unknown")}
Model: {result.get("model", "Unknown")}
Browser: {result.get("browser", "Unknown")}
Status: {"PASSED" if result.get("success") else "FAILED"}
Duration: {result.get("duration_seconds", 0):.1f}s
Steps: {result.get("steps_executed", 0)}
Token Usage: {result.get("token_usage", {}).get("total_tokens", 0):,}
-->

"""

    report_path.write_text(metadata + report_content, encoding="utf-8")

    # Save JSON results
    json_path = output_path / f"results_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str, ensure_ascii=False)

    # Save summary file if test passed
    if result.get("success"):
        summary_path = output_path / f"summary_{timestamp}.txt"
        summary = generate_summary(result)
        summary_path.write_text(summary, encoding="utf-8")

        return {"report": report_path, "results": json_path, "summary": summary_path}

    return {"report": report_path, "results": json_path}


def generate_summary(result: dict[str, Any]) -> str:
    """
    Generate a brief summary of test execution

    Args:
        result: Test execution results

    Returns:
        Summary text
    """
    summary_lines = [
        "Browser Copilot Test Summary",
        "=" * 50,
        f"Status: {'PASSED' if result.get('success') else 'FAILED'}",
        f"Duration: {result.get('duration_seconds', 0):.1f} seconds",
        f"Steps Executed: {result.get('steps_executed', 0)}",
        f"Browser: {result.get('browser', 'Unknown')}",
        f"Provider: {result.get('provider', 'Unknown')}",
        f"Model: {result.get('model', 'Unknown')}",
    ]

    if result.get("token_usage"):
        usage = result["token_usage"]
        summary_lines.extend(
            [
                "",
                "Token Usage:",
                f"  Total: {usage.get('total_tokens', 0):,}",
                f"  Prompt: {usage.get('prompt_tokens', 0):,}",
                f"  Completion: {usage.get('completion_tokens', 0):,}",
                f"  Cost: ${usage.get('estimated_cost', 0):.4f}",
            ]
        )

        # Add optimization info if available
        if usage.get("optimization"):
            opt = usage["optimization"]
            summary_lines.extend(
                [
                    "",
                    "Token Optimization:",
                    f"  Reduction: {opt['reduction_percentage']:.1f}%",
                    f"  Savings: ${opt.get('estimated_savings', 0):.4f}",
                ]
            )

    if result.get("error"):
        summary_lines.extend(["", f"Error: {result['error']}"])

    return "\n".join(summary_lines)


def generate_markdown_report(result: dict[str, Any]) -> str:
    """
    Generate a markdown report from test results

    Args:
        result: Test execution results

    Returns:
        Markdown formatted report
    """
    lines = ["# Browser Copilot Test Report", ""]

    # Status
    status = "✅ **PASSED**" if result.get("success") else "❌ **FAILED**"
    lines.append(f"Status: {status}")
    lines.append("")

    # Basic info
    if result.get("timestamp"):
        lines.append(f"Generated: {result['timestamp']}")
    if result.get("duration_seconds"):
        lines.append(f"Duration: {result['duration_seconds']} seconds")
    if result.get("steps_executed"):
        lines.append(f"Steps Executed: {result['steps_executed']}")
    if result.get("provider"):
        lines.append(f"Provider: {result['provider']}")
    if result.get("model"):
        lines.append(f"Model: {result['model']}")
    if result.get("browser"):
        lines.append(f"Browser: {result['browser']}")
    if result.get("headless") is not None:
        lines.append(f"Headless: {'Yes' if result['headless'] else 'No'}")
    lines.append("")

    # Token usage
    token_usage = result.get("token_usage", {})
    if token_usage:
        lines.append("## Token Usage")
        if token_usage.get("total_tokens"):
            lines.append(f"Total Tokens: {token_usage['total_tokens']:,}")
        if token_usage.get("prompt_tokens"):
            lines.append(f"Prompt Tokens: {token_usage['prompt_tokens']:,}")
        if token_usage.get("completion_tokens"):
            lines.append(f"Completion Tokens: {token_usage['completion_tokens']:,}")
        if token_usage.get("estimated_cost"):
            lines.append(f"Estimated Cost: ${token_usage['estimated_cost']:.4f}")
        lines.append("")

        # Token optimization
        opt = token_usage.get("optimization", {})
        if opt and opt.get("enabled"):
            lines.append("## Token Optimization")
            if opt.get("reduction_percentage"):
                lines.append(f"Reduction: {opt['reduction_percentage']:.1f}%")
            if opt.get("strategies_applied"):
                lines.append(
                    f"Strategies Applied: {', '.join(opt['strategies_applied'])}"
                )
            lines.append("")

    # Screenshots
    screenshots = result.get("screenshots", [])
    if screenshots:
        lines.append("## Screenshots")
        for screenshot in screenshots:
            lines.append(f"- {screenshot}")
        lines.append("")

    # Report content
    if result.get("report"):
        lines.append("## Test Report")
        lines.append(result["report"])
        lines.append("")

    # Error
    if result.get("error"):
        lines.append("## Error Details")
        lines.append(result["error"])
        lines.append("")

    return "\n".join(lines)


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60

    if minutes < 60:
        return f"{minutes}m {remaining_seconds:.0f}s"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    return f"{hours}h {remaining_minutes}m"


def create_html_report(result: dict[str, Any], output_path: Path) -> Path:
    """
    Create an HTML version of the test report

    Args:
        result: Test execution results
        output_path: Directory to save the report

    Returns:
        Path to the created HTML file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = output_path / f"report_{timestamp}.html"

    # Convert markdown report to HTML (simplified)
    report_content = result.get("report", "No report generated")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Browser Copilot Test Report - {timestamp}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .status-passed {{ color: #27ae60; }}
        .status-failed {{ color: #e74c3c; }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .report-content {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        pre {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Browser Copilot Test Report</h1>
        <p>Generated: {result.get("timestamp", datetime.now().isoformat())}</p>
    </div>
    
    <div class="metrics">
        <div class="metric-card">
            <h3>Status</h3>
            <p class="{"status-passed" if result.get("success") else "status-failed"}">
                {"✅ PASSED" if result.get("success") else "❌ FAILED"}
            </p>
        </div>
        <div class="metric-card">
            <h3>Duration</h3>
            <p>{format_duration(result.get("duration_seconds", 0))}</p>
        </div>
        <div class="metric-card">
            <h3>Steps</h3>
            <p>{result.get("steps_executed", 0)}</p>
        </div>
        <div class="metric-card">
            <h3>Browser</h3>
            <p>{result.get("browser", "Unknown")}</p>
        </div>
        <div class="metric-card">
            <h3>Total Tokens</h3>
            <p>{result.get("token_usage", {}).get("total_tokens", 0):,}</p>
        </div>
        <div class="metric-card">
            <h3>Cost</h3>
            <p>${result.get("token_usage", {}).get("estimated_cost", 0):.4f}</p>
        </div>
    </div>
    
    <div class="report-content">
        <h2>Test Report</h2>
        <pre>{report_content}</pre>
    </div>
</body>
</html>"""

    html_path.write_text(html_content, encoding="utf-8")
    return html_path
