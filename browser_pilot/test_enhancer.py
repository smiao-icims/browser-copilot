"""
Test Suite Enhancement Module

This module provides both static optimization and dynamic learning capabilities
for browser test suites. It learns from successful patterns and reuses them
to reduce token usage and improve test reliability.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from hashlib import sha256

try:
    from .config_manager import ConfigManager
    from .token_optimizer import TokenOptimizer, OptimizationLevel
    from .storage_manager import StorageManager
except ImportError:
    # For standalone testing
    try:
        from browser_pilot.config_manager import ConfigManager
        from browser_pilot.token_optimizer import TokenOptimizer, OptimizationLevel
        from browser_pilot.storage_manager import StorageManager
    except ImportError:
        # For unit testing
        from config_manager import ConfigManager
        from token_optimizer import TokenOptimizer, OptimizationLevel
        from storage_manager import StorageManager


class ExecutionMemory:
    """Manages execution history and successful patterns"""
    
    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager
        self.memory_dir = self.storage.base_dir / "memory" / "test_patterns"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.patterns_file = self.memory_dir / "successful_patterns.json"
        self.failures_file = self.memory_dir / "failure_patterns.json"
        self._load_patterns()
    
    def _load_patterns(self):
        """Load existing patterns from storage"""
        self.successful_patterns = {}
        self.failure_patterns = {}
        
        if self.patterns_file.exists():
            try:
                data = json.loads(self.patterns_file.read_text())
                self.successful_patterns = data
            except:
                self.successful_patterns = {}
        
        if self.failures_file.exists():
            try:
                data = json.loads(self.failures_file.read_text())
                self.failure_patterns = data
            except:
                self.failure_patterns = {}
    
    def record_success(self, test_id: str, action_type: str, code_snippet: str, 
                      context: Dict[str, Any], success_rate: float = 1.0):
        """Record a successful pattern"""
        pattern_key = self._generate_pattern_key(action_type, context)
        
        if pattern_key not in self.successful_patterns:
            self.successful_patterns[pattern_key] = {
                "action_type": action_type,
                "snippets": [],
                "context_features": self._extract_context_features(context),
                "first_seen": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "usage_count": 0,
                "success_rate": 0.0
            }
        
        pattern = self.successful_patterns[pattern_key]
        
        # Update snippet if it's new or better
        snippet_exists = False
        for snippet in pattern["snippets"]:
            if snippet["code"] == code_snippet:
                snippet["usage_count"] += 1
                snippet["last_success"] = datetime.now().isoformat()
                snippet_exists = True
                break
        
        if not snippet_exists:
            pattern["snippets"].append({
                "code": code_snippet,
                "usage_count": 1,
                "first_success": datetime.now().isoformat(),
                "last_success": datetime.now().isoformat(),
                "test_ids": [test_id]
            })
        
        # Update pattern statistics
        pattern["usage_count"] += 1
        pattern["last_used"] = datetime.now().isoformat()
        
        # Update success rate with exponential moving average
        alpha = 0.1  # Weight for new observations
        pattern["success_rate"] = (1 - alpha) * pattern["success_rate"] + alpha * success_rate
        
        self._save_patterns()
    
    def record_failure(self, test_id: str, action_type: str, error: str, context: Dict[str, Any]):
        """Record a failure pattern"""
        pattern_key = self._generate_pattern_key(action_type, context)
        
        if pattern_key not in self.failure_patterns:
            self.failure_patterns[pattern_key] = {
                "action_type": action_type,
                "errors": [],
                "context_features": self._extract_context_features(context),
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "occurrence_count": 0
            }
        
        pattern = self.failure_patterns[pattern_key]
        
        # Record error
        error_found = False
        for err in pattern["errors"]:
            if err["message"] == error:
                err["count"] += 1
                err["last_seen"] = datetime.now().isoformat()
                error_found = True
                break
        
        if not error_found:
            pattern["errors"].append({
                "message": error,
                "count": 1,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "test_ids": [test_id]
            })
        
        pattern["occurrence_count"] += 1
        pattern["last_seen"] = datetime.now().isoformat()
        
        self._save_patterns()
    
    def get_relevant_patterns(self, action_type: str, context: Dict[str, Any], 
                            min_success_rate: float = 0.7) -> List[Dict[str, Any]]:
        """Get relevant successful patterns for given context"""
        relevant = []
        context_features = self._extract_context_features(context)
        
        for pattern_key, pattern in self.successful_patterns.items():
            if pattern["action_type"] != action_type:
                continue
            
            if pattern["success_rate"] < min_success_rate:
                continue
            
            # Calculate similarity score
            similarity = self._calculate_similarity(context_features, pattern["context_features"])
            
            if similarity > 0.7:  # Threshold for relevance
                relevant.append({
                    "pattern": pattern,
                    "similarity": similarity,
                    "key": pattern_key
                })
        
        # Sort by similarity and success rate
        relevant.sort(key=lambda x: (x["similarity"], x["pattern"]["success_rate"]), reverse=True)
        
        return relevant[:5]  # Return top 5 most relevant patterns
    
    def _generate_pattern_key(self, action_type: str, context: Dict[str, Any]) -> str:
        """Generate unique key for pattern"""
        features = self._extract_context_features(context)
        feature_str = json.dumps(features, sort_keys=True)
        return f"{action_type}:{sha256(feature_str.encode()).hexdigest()[:16]}"
    
    def _extract_context_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant features from context"""
        features = {
            "url_pattern": self._extract_url_pattern(context.get("url", "")),
            "element_type": context.get("element_type", ""),
            "element_role": context.get("element_role", ""),
            "has_iframe": context.get("has_iframe", False),
            "page_type": context.get("page_type", ""),
            "action_sequence": context.get("action_sequence", [])[-3:]  # Last 3 actions
        }
        return features
    
    def _extract_url_pattern(self, url: str) -> str:
        """Extract pattern from URL"""
        if not url:
            return ""
        
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        
        # Extract domain and first path segment
        parts = url.split('/')
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
        return parts[0]
    
    def _calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between two feature sets"""
        score = 0.0
        weights = {
            "url_pattern": 0.3,
            "element_type": 0.2,
            "element_role": 0.2,
            "page_type": 0.2,
            "action_sequence": 0.1
        }
        
        for key, weight in weights.items():
            if key in features1 and key in features2:
                if features1[key] == features2[key]:
                    score += weight
                elif isinstance(features1[key], list) and isinstance(features2[key], list):
                    # For sequences, calculate overlap
                    overlap = len(set(features1[key]) & set(features2[key]))
                    max_len = max(len(features1[key]), len(features2[key]))
                    if max_len > 0:
                        score += weight * (overlap / max_len)
        
        return score
    
    def _save_patterns(self):
        """Save patterns to storage"""
        self.patterns_file.write_text(json.dumps(self.successful_patterns, indent=2))
        self.failures_file.write_text(json.dumps(self.failure_patterns, indent=2))
    
    def generate_summary(self) -> str:
        """Generate summary of learned patterns"""
        summary = []
        summary.append("# Learned Patterns Summary\n")
        summary.append(f"Generated: {datetime.now().isoformat()}\n")
        
        # Successful patterns
        summary.append("## Successful Patterns\n")
        for key, pattern in sorted(self.successful_patterns.items(), 
                                 key=lambda x: x[1]["success_rate"], reverse=True)[:10]:
            summary.append(f"### {pattern['action_type']} (Success Rate: {pattern['success_rate']:.2%})")
            summary.append(f"- Usage Count: {pattern['usage_count']}")
            summary.append(f"- Context: {json.dumps(pattern['context_features'], indent=2)}")
            summary.append(f"- Top Snippets:")
            
            for snippet in sorted(pattern["snippets"], key=lambda x: x["usage_count"], reverse=True)[:3]:
                summary.append(f"  ```javascript")
                summary.append(f"  {snippet['code']}")
                summary.append(f"  ```")
                summary.append(f"  - Used {snippet['usage_count']} times\n")
        
        # Failure patterns
        summary.append("\n## Common Failure Patterns\n")
        for key, pattern in sorted(self.failure_patterns.items(), 
                                 key=lambda x: x[1]["occurrence_count"], reverse=True)[:5]:
            summary.append(f"### {pattern['action_type']} (Occurrences: {pattern['occurrence_count']})")
            summary.append(f"- Context: {json.dumps(pattern['context_features'], indent=2)}")
            summary.append(f"- Common Errors:")
            
            for error in sorted(pattern["errors"], key=lambda x: x["count"], reverse=True)[:3]:
                summary.append(f"  - {error['message']} ({error['count']} times)")
        
        return "\n".join(summary)


class TestEnhancer:
    """Enhanced test suite optimizer with learning capabilities"""
    
    def __init__(self, llm, storage_manager: StorageManager, mode: str = "dynamic", level: str = "balanced"):
        self.llm = llm
        self.storage = storage_manager
        self.mode = mode  # "static" or "dynamic"
        self.level = level  # "conservative", "balanced", or "aggressive"
        self.memory = ExecutionMemory(storage_manager) if mode == "dynamic" else None
        
        # Enhancement prompt templates based on level
        self.conservative_prompt = """
Optimize this test suite CONSERVATIVELY for AI agents (20-30% token reduction):

REQUIREMENTS:
1. Remove only obvious redundancies ("please", "carefully", "make sure")
2. KEEP ALL waits, snapshots, and verification steps
3. KEEP detailed conditional logic
4. Preserve all functional steps
5. Focus on wording efficiency only
6. PRESERVE ALL CREDENTIALS, URLS, AND DATA VALUES

CONSERVATIVE RULES:
- Change "Click on the X button" to "Click X button"
- Keep "Wait 3 seconds" as is
- Keep all "Take snapshot" steps
- Keep detailed "If X visible, then Y" logic
- Never combine steps that might need separate timing

Original test suite:
{test_suite}

Conservatively enhanced test suite:
"""

        self.balanced_prompt = """
Optimize this test suite with BALANCED approach (30-40% token reduction):

REQUIREMENTS:
1. Remove redundant words and phrases
2. KEEP critical waits for dynamic content
3. KEEP snapshots before complex interactions
4. Simplify selectors where safe
5. Combine only truly sequential steps
6. PRESERVE ALL CREDENTIALS, URLS, AND DATA VALUES

BALANCED RULES:
- "Click on the button" to "Click"
- Keep "Wait 3 seconds" for dynamic content
- Keep snapshots before conditionals
- "If X is visible" to "If X visible"
- Combine: "Type text" + "Press Enter" to "Type text + Enter"
- Use shorter selectors when unambiguous

Original test suite:
{test_suite}

Balanced enhanced test suite:
"""

        self.aggressive_prompt = """
Optimize this test suite AGGRESSIVELY for minimum tokens (50%+ reduction):

REQUIREMENTS:
1. Maximum brevity while preserving core functionality
2. Remove most waits (AI handles timing)
3. Minimal snapshots (only when essential)
4. Ultra-concise selectors
5. Aggressive step combination
6. STILL PRESERVE CREDENTIALS, URLS, AND DATA VALUES

AGGRESSIVE RULES:
- Use shortest possible commands
- Remove explicit waits unless critical
- Combine multi-step sequences
- Use CSS/ID selectors over text
- Assume AI handles most timing
- Single line per action when possible

Original test suite:
{test_suite}

Aggressively enhanced test suite:
"""

        # Set the appropriate prompt based on level
        if self.level == "conservative":
            self.static_enhancement_prompt = self.conservative_prompt
        elif self.level == "aggressive":
            self.static_enhancement_prompt = self.aggressive_prompt
        else:  # balanced is default
            self.static_enhancement_prompt = self.balanced_prompt
        
        # Dynamic prompts also vary by level
        self.dynamic_conservative_prompt = """
Optimize using patterns with CONSERVATIVE approach (20-30% reduction):

AVAILABLE PATTERNS:
{patterns}

CONSERVATIVE REQUIREMENTS:
1. Apply only highly reliable patterns
2. Keep all timing and verification steps
3. Preserve detailed error handling
4. Maintain explicit waits and snapshots
5. PRESERVE ALL CREDENTIALS AND VALUES

Original test suite:
{test_suite}

Conservatively enhanced with patterns:
"""

        self.dynamic_balanced_prompt = """
Optimize using patterns with BALANCED approach (30-40% reduction):

AVAILABLE PATTERNS:
{patterns}

BALANCED REQUIREMENTS:
1. Use proven patterns from history
2. Keep critical waits and snapshots
3. Simplify where patterns show success
4. Combine steps proven to work together
5. PRESERVE ALL CREDENTIALS AND VALUES

Original test suite:
{test_suite}

Balanced enhancement with patterns:
"""

        self.dynamic_aggressive_prompt = """
Optimize using patterns AGGRESSIVELY (50%+ reduction):

AVAILABLE PATTERNS:
{patterns}

AGGRESSIVE REQUIREMENTS:
1. Maximum pattern application
2. Minimal waits and snapshots
3. Shortest proven selectors
4. Aggressive step combination
5. STILL PRESERVE CREDENTIALS AND VALUES

Original test suite:
{test_suite}

Aggressively enhanced with patterns:
"""

        # Set dynamic prompt based on level
        if self.level == "conservative":
            self.dynamic_enhancement_prompt = self.dynamic_conservative_prompt
        elif self.level == "aggressive":
            self.dynamic_enhancement_prompt = self.dynamic_aggressive_prompt
        else:
            self.dynamic_enhancement_prompt = self.dynamic_balanced_prompt
    
    async def enhance(self, test_suite_content: str, test_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate enhanced version of test suite"""
        if self.mode == "static":
            return await self._static_enhance(test_suite_content)
        else:
            return await self._dynamic_enhance(test_suite_content, test_context or {})
    
    async def _static_enhance(self, test_suite_content: str) -> Dict[str, Any]:
        """Static enhancement without learning"""
        prompt = self.static_enhancement_prompt.format(test_suite=test_suite_content)
        
        response = await self.llm.ainvoke(prompt)
        enhanced_content = response.content
        
        # Apply additional token optimization
        enhanced_content = self._apply_token_optimization(enhanced_content)
        
        # Calculate token reduction
        original_tokens = self._estimate_tokens(test_suite_content)
        enhanced_tokens = self._estimate_tokens(enhanced_content)
        reduction = (original_tokens - enhanced_tokens) / original_tokens * 100
        
        # If enhancement increased tokens, return original
        if enhanced_tokens > original_tokens:
            return {
                "content": test_suite_content,
                "mode": "static",
                "original_tokens": original_tokens,
                "enhanced_tokens": original_tokens,
                "reduction_percentage": 0,
                "enhancements": ["Token optimization failed - keeping original"],
                "optimization_note": "Enhanced version was longer, reverted to original"
            }
        
        return {
            "content": enhanced_content,
            "mode": "static",
            "original_tokens": original_tokens,
            "enhanced_tokens": enhanced_tokens,
            "reduction_percentage": reduction,
            "enhancements": self._identify_enhancements(test_suite_content, enhanced_content)
        }
    
    async def _dynamic_enhance(self, test_suite_content: str, test_context: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamic enhancement with learned patterns"""
        # Extract test steps to find relevant patterns
        test_steps = self._extract_test_steps(test_suite_content)
        relevant_patterns = []
        
        for step in test_steps:
            action_type = self._identify_action_type(step)
            if action_type:
                patterns = self.memory.get_relevant_patterns(action_type, test_context)
                if patterns:
                    relevant_patterns.extend(patterns)
        
        # Format patterns for prompt
        patterns_text = self._format_patterns_for_prompt(relevant_patterns)
        
        prompt = self.dynamic_enhancement_prompt.format(
            patterns=patterns_text,
            test_suite=test_suite_content
        )
        
        response = await self.llm.ainvoke(prompt)
        enhanced_content = response.content
        
        # Apply additional token optimization
        enhanced_content = self._apply_token_optimization(enhanced_content)
        
        # Calculate metrics
        original_tokens = self._estimate_tokens(test_suite_content)
        enhanced_tokens = self._estimate_tokens(enhanced_content)
        reduction = (original_tokens - enhanced_tokens) / original_tokens * 100
        
        # If enhancement increased tokens, return original
        if enhanced_tokens > original_tokens:
            return {
                "content": test_suite_content,
                "mode": "dynamic",
                "original_tokens": original_tokens,
                "enhanced_tokens": original_tokens,
                "reduction_percentage": 0,
                "patterns_applied": 0,
                "enhancements": ["Token optimization failed - keeping original"],
                "optimization_note": "Enhanced version was longer, reverted to original"
            }
        
        # Save enhancement record for future learning
        enhancement_record = {
            "timestamp": datetime.now().isoformat(),
            "original": test_suite_content,
            "enhanced": enhanced_content,
            "patterns_used": [p["key"] for p in relevant_patterns],
            "token_reduction": reduction
        }
        
        self._save_enhancement_record(enhancement_record)
        
        return {
            "content": enhanced_content,
            "mode": "dynamic",
            "original_tokens": original_tokens,
            "enhanced_tokens": enhanced_tokens,
            "reduction_percentage": reduction,
            "patterns_applied": len(relevant_patterns),
            "enhancements": self._identify_enhancements(test_suite_content, enhanced_content),
            "learning_summary": self.memory.generate_summary() if self.memory else None
        }
    
    def record_execution_result(self, test_id: str, execution_log: List[Dict[str, Any]], 
                              success: bool, duration: float):
        """Record execution results for learning"""
        if not self.memory:
            return
        
        # Analyze execution log
        for i, step in enumerate(execution_log):
            if "tool_name" in step and step["tool_name"].startswith("browser_"):
                action_type = step["tool_name"]
                
                # Build context
                context = {
                    "url": step.get("url", ""),
                    "element_type": step.get("element_type", ""),
                    "element_role": step.get("element_role", ""),
                    "has_iframe": step.get("has_iframe", False),
                    "page_type": step.get("page_type", ""),
                    "action_sequence": [s.get("tool_name", "") for s in execution_log[max(0, i-3):i]]
                }
                
                if step.get("success", True) and success:
                    # Record successful pattern
                    code_snippet = step.get("code_snippet", "")
                    if code_snippet:
                        self.memory.record_success(
                            test_id, action_type, code_snippet, context,
                            success_rate=1.0 if step.get("retry_count", 0) == 0 else 0.8
                        )
                elif "error" in step:
                    # Record failure pattern
                    self.memory.record_failure(
                        test_id, action_type, step["error"], context
                    )
    
    def _extract_test_steps(self, test_suite: str) -> List[str]:
        """Extract individual test steps from suite"""
        steps = []
        
        # Common patterns for test steps
        patterns = [
            r'^\d+\.\s+(.+)$',  # Numbered lists
            r'^-\s+(.+)$',      # Bullet points
            r'^>\s+(.+)$',      # Quoted steps
            r'^\*\s+(.+)$',     # Asterisk lists
        ]
        
        lines = test_suite.split('\n')
        for line in lines:
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    steps.append(match.group(1))
                    break
        
        return steps
    
    def _identify_action_type(self, step: str) -> Optional[str]:
        """Identify browser action type from step description"""
        action_keywords = {
            "browser_navigate": ["navigate", "go to", "open", "visit"],
            "browser_click": ["click", "press", "tap", "select"],
            "browser_type": ["type", "enter", "fill", "input"],
            "browser_wait_for": ["wait", "verify", "check", "ensure"],
            "browser_take_screenshot": ["screenshot", "capture", "snap"],
            "browser_hover": ["hover", "mouse over"],
            "browser_select_option": ["select", "choose", "pick"],
            "browser_drag": ["drag", "drop", "move"]
        }
        
        step_lower = step.lower()
        for action, keywords in action_keywords.items():
            if any(keyword in step_lower for keyword in keywords):
                return action
        
        return None
    
    def _format_patterns_for_prompt(self, patterns: List[Dict[str, Any]]) -> str:
        """Format patterns for inclusion in prompt"""
        if not patterns:
            return "No relevant patterns found in memory."
        
        formatted = []
        for i, pattern_data in enumerate(patterns[:5], 1):
            pattern = pattern_data["pattern"]
            formatted.append(f"{i}. {pattern['action_type']} (Success: {pattern['success_rate']:.0%})")
            
            # Include top snippet
            if pattern["snippets"]:
                top_snippet = sorted(pattern["snippets"], 
                                   key=lambda x: x["usage_count"], reverse=True)[0]
                formatted.append(f"   Code: {top_snippet['code']}")
                formatted.append(f"   Used successfully {top_snippet['usage_count']} times")
            
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation"""
        # Simple estimation: ~1.3 tokens per word for English
        words = len(text.split())
        return int(words * 1.3)
    
    def _apply_token_optimization(self, content: str) -> str:
        """Apply additional token optimization rules"""
        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r' {2,}', ' ', content)
        
        # Common verbose patterns to concise forms
        replacements = {
            # Verbose actions to concise
            r'Click on the (.+?) button': r'Click \1',
            r'Navigate to the URL (.+)': r'Go to \1',
            r'Enter (.+?) in the (.+?) field': r'Type \1 in \2',
            r'Wait for (.+?) to be visible': r'Wait for \1',
            r'Verify that (.+)': r'Verify \1',
            r'Check that (.+)': r'Check \1',
            
            # Remove filler words
            r'\bplease\b': '',
            r'\bmake sure to\b': '',
            r'\byou should\b': '',
            r'\bcarefully\b': '',
            r'\bsuccessfully\b': '',
            
            # Shorten common patterns
            r'data-testid=["\'](.*?)["\']': r'[testid=\1]',
            r'aria-label=["\'](.*?)["\']': r'[aria=\1]',
            r'class=["\'](.*?)["\']': r'.\1',
            r'id=["\'](.*?)["\']': r'#\1',
            
            # Combine common sequences
            r'Type (.+?)\nPress Enter': r'Type \1 + Enter',
            r'Click (.+?)\nWait for navigation': r'Click \1 (wait)',
        }
        
        for pattern, replacement in replacements.items():
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        # Remove empty lines
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        content = '\n'.join(lines)
        
        return content
    
    def _identify_enhancements(self, original: str, enhanced: str) -> List[str]:
        """Identify what enhancements were made"""
        enhancements = []
        
        # Check for common enhancement patterns
        if "wait" in enhanced.lower() and "wait" not in original.lower():
            enhancements.append("Added wait conditions")
        
        if enhanced.count("role=") > original.count("role="):
            enhancements.append("Added ARIA role selectors")
        
        if enhanced.count("data-testid") > original.count("data-testid"):
            enhancements.append("Added test ID selectors")
        
        if "verify" in enhanced.lower() or "check" in enhanced.lower():
            if "verify" not in original.lower() and "check" not in original.lower():
                enhancements.append("Added verification steps")
        
        if "error" in enhanced.lower() or "fallback" in enhanced.lower():
            if "error" not in original.lower() and "fallback" not in original.lower():
                enhancements.append("Added error handling")
        
        # Check for structure improvements
        if enhanced.count("\n") > original.count("\n") * 1.2:
            enhancements.append("Improved formatting and structure")
        
        return enhancements
    
    def _save_enhancement_record(self, record: Dict[str, Any]):
        """Save enhancement record for analysis"""
        records_file = self.storage.base_dir / "memory" / "enhancement_records.jsonl"
        records_file.parent.mkdir(parents=True, exist_ok=True)
        
        with records_file.open("a") as f:
            f.write(json.dumps(record) + "\n")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get statistics about optimizations"""
        if not self.memory:
            return {"mode": "static", "message": "No learning data available in static mode"}
        
        stats = {
            "mode": "dynamic",
            "total_patterns": len(self.memory.successful_patterns),
            "total_failures": len(self.memory.failure_patterns),
            "top_actions": [],
            "average_success_rate": 0.0,
            "most_used_snippets": []
        }
        
        # Calculate top actions
        action_counts = {}
        total_success_rate = 0.0
        
        for pattern in self.memory.successful_patterns.values():
            action = pattern["action_type"]
            action_counts[action] = action_counts.get(action, 0) + pattern["usage_count"]
            total_success_rate += pattern["success_rate"]
        
        if self.memory.successful_patterns:
            stats["average_success_rate"] = total_success_rate / len(self.memory.successful_patterns)
        
        stats["top_actions"] = sorted(
            [(action, count) for action, count in action_counts.items()],
            key=lambda x: x[1], reverse=True
        )[:5]
        
        # Find most used snippets
        all_snippets = []
        for pattern in self.memory.successful_patterns.values():
            for snippet in pattern["snippets"]:
                all_snippets.append({
                    "code": snippet["code"],
                    "usage_count": snippet["usage_count"],
                    "action": pattern["action_type"]
                })
        
        stats["most_used_snippets"] = sorted(
            all_snippets, key=lambda x: x["usage_count"], reverse=True
        )[:10]
        
        return stats


# Keep backward compatibility
TestSuiteEnhancer = TestEnhancer


class TestSuiteValidator:
    """Validates test suites for common issues"""
    
    @staticmethod
    def validate(test_suite_content: str) -> dict:
        """
        Validate a test suite
        
        Args:
            test_suite_content: Test suite content
            
        Returns:
            Validation result with warnings and errors
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {
                "lines": 0,
                "steps": 0,
                "assertions": 0
            }
        }
        
        if not test_suite_content.strip():
            result["valid"] = False
            result["errors"].append("Test suite is empty")
            return result
        
        lines = test_suite_content.split('\n')
        result["stats"]["lines"] = len(lines)
        
        # Count steps and assertions
        step_keywords = ['navigate', 'click', 'type', 'enter', 'select', 'hover', 'wait']
        assertion_keywords = ['verify', 'assert', 'check', 'ensure', 'confirm']
        
        for line in lines:
            lower_line = line.lower()
            if any(keyword in lower_line for keyword in step_keywords):
                result["stats"]["steps"] += 1
            if any(keyword in lower_line for keyword in assertion_keywords):
                result["stats"]["assertions"] += 1
        
        # Validate structure
        if result["stats"]["steps"] == 0:
            result["errors"].append("No test steps found")
            result["valid"] = False
        
        if result["stats"]["assertions"] == 0:
            result["warnings"].append("No assertions found - consider adding verification steps")
        
        # Check for common issues
        if len(lines) > 100:
            result["warnings"].append("Test suite is very long - consider breaking into smaller tests")
        
        if any('todo' in line.lower() or 'fixme' in line.lower() for line in lines):
            result["warnings"].append("Test suite contains TODO/FIXME comments")
        
        # Check for hardcoded values
        if any('localhost' in line or '127.0.0.1' in line for line in lines):
            result["warnings"].append("Test suite contains hardcoded localhost URLs")
        
        return result