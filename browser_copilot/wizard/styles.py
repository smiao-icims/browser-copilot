"""Custom styling for the configuration wizard."""

from prompt_toolkit.styles import Style

# Browser Copilot branded color scheme
BROWSER_PILOT_STYLE = Style(
    [
        ("qmark", "fg:#0084ff bold"),  # Question mark (blue)
        ("question", "bold"),  # Question text
        ("answer", "fg:#44ff44 bold"),  # Selected answer (green)
        ("pointer", "fg:#0084ff bold"),  # Selection pointer (blue)
        ("highlighted", "fg:#0084ff bold"),  # Highlighted choice (blue)
        ("selected", "fg:#44ff44"),  # Selected item (green)
        ("separator", "fg:#808080"),  # Separators (gray)
        ("instruction", "fg:#808080"),  # Instructions (gray)
        ("text", ""),  # Normal text
        ("disabled", "fg:#808080 italic"),  # Disabled choices (gray italic)
        ("error", "fg:#ff0000 bold"),  # Error messages (red)
        ("warning", "fg:#ffaa00"),  # Warning messages (orange)
        ("success", "fg:#44ff44 bold"),  # Success messages (green)
        ("info", "fg:#0084ff"),  # Info messages (blue)
    ]
)
