"""
Debug output formatter for context management

Provides structured, readable debug output for context management operations.
"""

from typing import List, Dict, Any, Tuple
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box
import json


class ContextDebugFormatter:
    """Formats context management debug output in a structured way"""
    
    def __init__(self, use_rich: bool = True):
        """
        Initialize formatter
        
        Args:
            use_rich: Whether to use rich formatting (colored terminal output)
        """
        self.use_rich = use_rich
        self.console = Console() if use_rich else None
    
    def format_hook_header(self, hook_name: str, message_count: int, max_tokens: int) -> str:
        """Format the hook processing header"""
        if self.use_rich:
            panel = Panel(
                f"Processing {message_count} messages\nMax tokens: {max_tokens:,}",
                title=f"[bold blue]{hook_name}[/bold blue]",
                border_style="blue"
            )
            self.console.print(panel)
            return ""
        else:
            return f"\n[{hook_name}] Processing {message_count} messages (max tokens: {max_tokens:,})"
    
    def format_message_analysis(self, messages: List[BaseMessage]) -> str:
        """Format message analysis with size distribution"""
        # Calculate sizes
        size_buckets = {
            "<100": 0,
            "100-500": 0,
            "500-1K": 0,
            "1K-5K": 0,
            ">5K": 0
        }
        
        message_sizes = []
        for i, msg in enumerate(messages):
            tokens = self._count_tokens(msg)
            message_sizes.append((i, msg, tokens))
            
            if tokens < 100:
                size_buckets["<100"] += 1
            elif tokens < 500:
                size_buckets["100-500"] += 1
            elif tokens < 1000:
                size_buckets["500-1K"] += 1
            elif tokens < 5000:
                size_buckets["1K-5K"] += 1
            else:
                size_buckets[">5K"] += 1
        
        # Sort by size for largest messages
        message_sizes.sort(key=lambda x: x[2], reverse=True)
        
        if self.use_rich:
            # Create size distribution table
            table = Table(title="Message Size Distribution", box=box.ROUNDED)
            table.add_column("Size Range", style="cyan")
            table.add_column("Count", justify="right", style="green")
            table.add_column("Visual", style="blue")
            
            max_count = max(size_buckets.values()) if size_buckets.values() else 1
            for size_range, count in size_buckets.items():
                bar_length = int((count / max_count) * 20) if max_count > 0 else 0
                bar = "█" * bar_length
                table.add_row(size_range, str(count), bar)
            
            self.console.print(table)
            
            # Show largest messages
            if message_sizes:
                large_table = Table(title="Largest Messages (Top 5)", box=box.ROUNDED)
                large_table.add_column("Idx", style="cyan")
                large_table.add_column("Type", style="yellow")
                large_table.add_column("Tokens", justify="right", style="red")
                large_table.add_column("Preview", style="dim")
                
                for idx, msg, tokens in message_sizes[:5]:
                    msg_type = type(msg).__name__
                    preview = str(msg.content)[:60] + "..." if msg.content else ""
                    large_table.add_row(
                        str(idx), 
                        msg_type, 
                        f"{tokens:,}", 
                        preview
                    )
                
                self.console.print(large_table)
            
            return ""
        else:
            # Plain text output
            lines = ["\n[Message Analysis]"]
            lines.append(f"Total messages: {len(messages)}")
            lines.append("Size distribution:")
            for size_range, count in size_buckets.items():
                if count > 0:
                    lines.append(f"  {size_range} tokens: {count} messages")
            
            lines.append("\nLargest messages:")
            for idx, msg, tokens in message_sizes[:5]:
                msg_type = type(msg).__name__
                preview = str(msg.content)[:60] if msg.content else ""
                lines.append(f"  Message {idx}: {msg_type} - {tokens} tokens")
                lines.append(f"    Preview: {preview}...")
            
            return "\n".join(lines)
    
    def format_results(
        self, 
        original_count: int,
        trimmed_count: int,
        original_tokens: int,
        trimmed_tokens: int,
        excluded_messages: List[Tuple[int, BaseMessage, int]] = None
    ) -> str:
        """Format the trimming results"""
        msg_reduction = ((original_count - trimmed_count) / original_count * 100) if original_count else 0
        token_reduction = ((original_tokens - trimmed_tokens) / original_tokens * 100) if original_tokens else 0
        
        if self.use_rich:
            # Create results panel
            results_text = Text()
            results_text.append("Messages: ", style="bold")
            results_text.append(f"{original_count} → {trimmed_count} ", style="cyan")
            results_text.append(f"({msg_reduction:.1f}% reduction)\n", style="dim")
            
            results_text.append("Tokens: ", style="bold")
            results_text.append(f"{original_tokens:,} → {trimmed_tokens:,} ", style="green")
            results_text.append(f"({token_reduction:.1f}% reduction)\n", style="dim")
            
            results_text.append("Budget usage: ", style="bold")
            budget_percent = (trimmed_tokens / original_tokens * 100) if original_tokens else 0
            results_text.append(f"{budget_percent:.1f}%", style="yellow")
            
            panel = Panel(results_text, title="[bold green]Results[/bold green]", border_style="green")
            self.console.print(panel)
            
            # Show excluded large messages if any
            if excluded_messages:
                large_excluded = [
                    (idx, msg, tokens) for idx, msg, tokens in excluded_messages 
                    if tokens > 1000
                ]
                if large_excluded:
                    exc_table = Table(
                        title="Large Excluded Messages", 
                        box=box.SIMPLE,
                        title_style="red"
                    )
                    exc_table.add_column("Idx", style="cyan")
                    exc_table.add_column("Type", style="yellow")
                    exc_table.add_column("Tokens", justify="right", style="red")
                    
                    for idx, msg, tokens in large_excluded[:5]:
                        exc_table.add_row(
                            str(idx),
                            type(msg).__name__,
                            f"{tokens:,}"
                        )
                    
                    self.console.print(exc_table)
            
            return ""
        else:
            # Plain text output
            lines = ["\n[Results]"]
            lines.append(f"Messages: {original_count} → {trimmed_count} ({msg_reduction:.1f}% reduction)")
            lines.append(f"Tokens: {original_tokens:,} → {trimmed_tokens:,} ({token_reduction:.1f}% reduction)")
            lines.append(f"Excluded: {original_count - trimmed_count} messages")
            
            if excluded_messages:
                large_excluded = [
                    (idx, msg, tokens) for idx, msg, tokens in excluded_messages 
                    if tokens > 1000
                ]
                if large_excluded:
                    lines.append("\nLarge excluded messages:")
                    for idx, msg, tokens in large_excluded[:5]:
                        lines.append(f"  Message {idx}: {type(msg).__name__} - {tokens} tokens")
            
            return "\n".join(lines)
    
    def format_warning(self, message: str) -> str:
        """Format a warning message"""
        if self.use_rich:
            self.console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")
            return ""
        else:
            return f"\n[WARNING] {message}"
    
    def format_error(self, message: str) -> str:
        """Format an error message"""
        if self.use_rich:
            self.console.print(f"[bold red]❌ {message}[/bold red]")
            return ""
        else:
            return f"\n[ERROR] {message}"
    
    def format_info(self, message: str) -> str:
        """Format an info message"""
        if self.use_rich:
            self.console.print(f"[dim]{message}[/dim]")
            return ""
        else:
            return f"\n[INFO] {message}"
    
    def format_tool_pair_validation(self, is_valid: bool, details: str = None) -> str:
        """Format tool pair validation results"""
        if self.use_rich:
            if is_valid:
                self.console.print("[green]✓ Tool pairs valid[/green]")
            else:
                self.console.print(f"[red]✗ Tool pairs invalid[/red]")
                if details:
                    self.console.print(f"  [dim]{details}[/dim]")
            return ""
        else:
            if is_valid:
                return "\n[VALIDATION] Tool pairs valid"
            else:
                lines = ["\n[VALIDATION] Tool pairs invalid"]
                if details:
                    lines.append(f"  {details}")
                return "\n".join(lines)
    
    def _count_tokens(self, msg: BaseMessage) -> int:
        """Count tokens in a message (simple approximation)"""
        if msg.content:
            return len(str(msg.content)) // 4
        return 0
    
    @staticmethod
    def create_json_summary(
        hook_name: str,
        original_count: int,
        trimmed_count: int,
        original_tokens: int,
        trimmed_tokens: int,
        window_size: int,
        strategy: str
    ) -> Dict[str, Any]:
        """Create a JSON summary for logging/metrics"""
        return {
            "hook": hook_name,
            "strategy": strategy,
            "window_size": window_size,
            "messages": {
                "original": original_count,
                "trimmed": trimmed_count,
                "reduction_percent": ((original_count - trimmed_count) / original_count * 100) if original_count else 0
            },
            "tokens": {
                "original": original_tokens,
                "trimmed": trimmed_tokens,
                "reduction_percent": ((original_tokens - trimmed_tokens) / original_tokens * 100) if original_tokens else 0,
                "budget_usage_percent": (trimmed_tokens / window_size * 100) if window_size else 0
            }
        }