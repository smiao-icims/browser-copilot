"""
Pre-model hooks for ReAct agents to manage message history

This module provides the no-op hook for baseline comparison.
"""

from typing import Any, Dict


def create_no_op_hook() -> callable:
    """
    Create a no-op pre-model hook that doesn't modify messages
    
    Returns:
        Pre-model hook function that returns state unchanged
    """
    def no_op_pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """No-op hook that doesn't modify messages"""
        # Return empty dict to keep messages unchanged
        return {}
    
    return no_op_pre_model_hook