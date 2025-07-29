# Browser Copilot Evaluation Implementation Specification

## Quick Start Evaluation Example

```python
# Example: Evaluating context management strategies
async def evaluate_context_strategies():
    """Compare different context management strategies"""
    
    test_suite = "examples/icims_job_search.md"
    strategies = ["no-op", "sliding-window", "smart-trim", "langchain-trim"]
    window_sizes = [10000, 25000, 50000]
    
    results = []
    for strategy in strategies:
        for window_size in window_sizes:
            result = await run_evaluation(
                test_suite=test_suite,
                strategy=strategy,
                window_size=window_size,
                runs=3  # Multiple runs for consistency
            )
            results.append(result)
    
    return generate_comparison_report(results)
```

## 1. Evaluation Data Model

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class RunMetrics:
    """Metrics from a single test run"""
    # Identifiers
    run_id: str
    timestamp: datetime
    test_suite: str
    
    # Configuration
    context_strategy: str
    window_size: int
    model: str
    provider: str
    
    # Performance metrics
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    execution_time_seconds: float
    steps_executed: int
    
    # Quality metrics
    test_passed: bool
    errors_encountered: List[str]
    retries_needed: int
    
    # Context management metrics
    messages_trimmed: int
    tokens_saved: int
    trim_percentage: float
    large_messages_excluded: List[Dict[str, Any]]
    
    # Cost metrics
    estimated_cost_usd: float
    cost_per_step: float

@dataclass
class EvaluationReport:
    """Aggregated evaluation results"""
    # Summary
    total_runs: int
    success_rate: float
    avg_token_usage: float
    avg_execution_time: float
    
    # By strategy
    strategy_comparison: Dict[str, Dict[str, float]]
    
    # By window size
    window_size_analysis: Dict[int, Dict[str, float]]
    
    # Recommendations
    optimal_configuration: Dict[str, Any]
    insights: List[str]
```

## 2. Evaluation Scenarios

### 2.1 Scenario Definitions

```yaml
# evaluation-scenarios.yaml
scenarios:
  simple_navigation:
    description: "Basic page navigation and content verification"
    complexity: low
    expected_tokens: 5000-10000
    expected_steps: 5-10
    test_files:
      - examples/simple-navigation.md
      - examples/google-search.md
  
  form_interaction:
    description: "Form filling with validation"
    complexity: medium
    expected_tokens: 10000-25000
    expected_steps: 10-20
    test_files:
      - examples/saucedemo-shopping.md
      - examples/form-submission.md
  
  complex_workflow:
    description: "Multi-step workflows with authentication"
    complexity: high
    expected_tokens: 20000-50000
    expected_steps: 20-50
    test_files:
      - examples/icims_job_search.md
      - examples/enterprise-app-flow.md
  
  data_extraction:
    description: "Scraping and data collection"
    complexity: medium
    expected_tokens: 15000-30000
    expected_steps: 15-25
    test_files:
      - examples/weather-forecast.md
      - examples/product-catalog.md
```

### 2.2 Scenario-Based Evaluation

```python
class ScenarioEvaluator:
    """Evaluate agents across different scenario types"""
    
    def __init__(self, scenarios_config: str):
        self.scenarios = self.load_scenarios(scenarios_config)
        self.results = {}
    
    async def evaluate_scenario(
        self, 
        scenario_name: str,
        configurations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run evaluation for a specific scenario"""
        
        scenario = self.scenarios[scenario_name]
        scenario_results = []
        
        for test_file in scenario['test_files']:
            for config in configurations:
                result = await self.run_single_test(
                    test_file=test_file,
                    config=config,
                    expected_bounds=scenario
                )
                scenario_results.append(result)
        
        return self.analyze_scenario_results(scenario_results)
```

## 3. Metrics Collection Implementation

```python
import time
import psutil
import tracemalloc
from contextlib import contextmanager

class MetricsCollector:
    """Comprehensive metrics collection for evaluation"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = None
        self.memory_tracker = None
    
    @contextmanager
    def collect_metrics(self, run_id: str):
        """Context manager for metrics collection"""
        # Start collection
        self.start_time = time.time()
        tracemalloc.start()
        process = psutil.Process()
        start_memory = process.memory_info().rss
        
        try:
            yield self
        finally:
            # End collection
            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            end_memory = process.memory_info().rss
            
            self.metrics[run_id] = {
                'duration_seconds': end_time - self.start_time,
                'peak_memory_mb': peak / 1024 / 1024,
                'memory_delta_mb': (end_memory - start_memory) / 1024 / 1024,
                'cpu_percent': process.cpu_percent(interval=0.1)
            }
    
    def add_llm_metrics(self, run_id: str, token_usage: Dict[str, int]):
        """Add LLM-specific metrics"""
        if run_id not in self.metrics:
            self.metrics[run_id] = {}
        
        self.metrics[run_id].update({
            'total_tokens': token_usage.get('total', 0),
            'prompt_tokens': token_usage.get('prompt', 0),
            'completion_tokens': token_usage.get('completion', 0),
            'cost_estimate': self.calculate_cost(token_usage)
        })
    
    def add_context_metrics(self, run_id: str, context_stats: Dict[str, Any]):
        """Add context management metrics"""
        if run_id not in self.metrics:
            self.metrics[run_id] = {}
        
        self.metrics[run_id].update({
            'messages_processed': context_stats.get('total_messages', 0),
            'messages_trimmed': context_stats.get('trimmed_messages', 0),
            'trim_percentage': context_stats.get('trim_percentage', 0),
            'largest_message_tokens': context_stats.get('largest_message', 0)
        })
```

## 4. Evaluation Execution Framework

```python
class EvaluationFramework:
    """Main evaluation execution framework"""
    
    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.metrics_collector = MetricsCollector()
        self.scenario_evaluator = ScenarioEvaluator(config.scenarios_file)
        self.report_generator = ReportGenerator()
    
    async def run_full_evaluation(self) -> EvaluationReport:
        """Run complete evaluation suite"""
        
        all_results = []
        
        # Test different strategies
        for strategy in self.config.strategies:
            # Test different window sizes
            for window_size in self.config.window_sizes:
                # Test different scenarios
                for scenario in self.config.scenarios:
                    results = await self.evaluate_configuration(
                        strategy=strategy,
                        window_size=window_size,
                        scenario=scenario
                    )
                    all_results.extend(results)
        
        # Generate comprehensive report
        return self.report_generator.generate_report(all_results)
    
    async def evaluate_configuration(
        self,
        strategy: str,
        window_size: int,
        scenario: str
    ) -> List[RunMetrics]:
        """Evaluate a specific configuration"""
        
        results = []
        test_files = self.scenario_evaluator.scenarios[scenario]['test_files']
        
        for test_file in test_files:
            # Run multiple times for consistency
            for run in range(self.config.runs_per_config):
                run_id = f"{strategy}_{window_size}_{scenario}_{run}"
                
                with self.metrics_collector.collect_metrics(run_id):
                    result = await self.run_single_test(
                        test_file=test_file,
                        strategy=strategy,
                        window_size=window_size
                    )
                    
                    # Collect all metrics
                    metrics = RunMetrics(
                        run_id=run_id,
                        timestamp=datetime.now(),
                        test_suite=test_file,
                        context_strategy=strategy,
                        window_size=window_size,
                        **result
                    )
                    results.append(metrics)
        
        return results
```

## 5. Comparison and Analysis

```python
class EvaluationAnalyzer:
    """Analyze and compare evaluation results"""
    
    @staticmethod
    def compare_strategies(results: List[RunMetrics]) -> Dict[str, Any]:
        """Compare different context management strategies"""
        
        strategy_stats = defaultdict(lambda: {
            'runs': 0,
            'success_rate': 0,
            'avg_tokens': 0,
            'avg_time': 0,
            'token_savings': 0
        })
        
        # Group by strategy
        for result in results:
            strategy = result.context_strategy
            stats = strategy_stats[strategy]
            
            stats['runs'] += 1
            stats['success_rate'] += 1 if result.test_passed else 0
            stats['avg_tokens'] += result.total_tokens
            stats['avg_time'] += result.execution_time_seconds
            stats['token_savings'] += result.tokens_saved
        
        # Calculate averages
        for strategy, stats in strategy_stats.items():
            runs = stats['runs']
            if runs > 0:
                stats['success_rate'] = (stats['success_rate'] / runs) * 100
                stats['avg_tokens'] = stats['avg_tokens'] / runs
                stats['avg_time'] = stats['avg_time'] / runs
                stats['token_savings'] = stats['token_savings'] / runs
        
        return dict(strategy_stats)
    
    @staticmethod
    def find_optimal_configuration(
        results: List[RunMetrics],
        weights: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """Find optimal configuration based on weighted criteria"""
        
        if weights is None:
            weights = {
                'success_rate': 0.4,
                'token_efficiency': 0.3,
                'execution_time': 0.2,
                'cost': 0.1
            }
        
        configurations = defaultdict(list)
        
        # Group results by configuration
        for result in results:
            key = (result.context_strategy, result.window_size)
            configurations[key].append(result)
        
        # Score each configuration
        scored_configs = []
        for (strategy, window_size), runs in configurations.items():
            # Calculate metrics
            success_rate = sum(1 for r in runs if r.test_passed) / len(runs)
            avg_tokens = sum(r.total_tokens for r in runs) / len(runs)
            avg_time = sum(r.execution_time_seconds for r in runs) / len(runs)
            avg_cost = sum(r.estimated_cost_usd for r in runs) / len(runs)
            
            # Normalize and score (higher is better)
            score = (
                weights['success_rate'] * success_rate +
                weights['token_efficiency'] * (1 - avg_tokens / 100000) +
                weights['execution_time'] * (1 - avg_time / 300) +
                weights['cost'] * (1 - avg_cost / 1.0)
            )
            
            scored_configs.append({
                'strategy': strategy,
                'window_size': window_size,
                'score': score,
                'metrics': {
                    'success_rate': success_rate * 100,
                    'avg_tokens': avg_tokens,
                    'avg_time': avg_time,
                    'avg_cost': avg_cost
                }
            })
        
        # Return best configuration
        return max(scored_configs, key=lambda x: x['score'])
```

## 6. Visualization and Reporting

```python
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

class EvaluationVisualizer:
    """Create visualizations for evaluation results"""
    
    @staticmethod
    def create_strategy_comparison_chart(results: Dict[str, Any]) -> str:
        """Create bar chart comparing strategies"""
        
        df = pd.DataFrame(results).T
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Success rate
        axes[0, 0].bar(df.index, df['success_rate'])
        axes[0, 0].set_title('Success Rate by Strategy')
        axes[0, 0].set_ylabel('Success Rate (%)')
        
        # Token usage
        axes[0, 1].bar(df.index, df['avg_tokens'])
        axes[0, 1].set_title('Average Token Usage')
        axes[0, 1].set_ylabel('Tokens')
        
        # Execution time
        axes[1, 0].bar(df.index, df['avg_time'])
        axes[1, 0].set_title('Average Execution Time')
        axes[1, 0].set_ylabel('Time (seconds)')
        
        # Token savings
        axes[1, 1].bar(df.index, df['token_savings'])
        axes[1, 1].set_title('Average Token Savings')
        axes[1, 1].set_ylabel('Tokens Saved')
        
        plt.tight_layout()
        filepath = 'evaluation_results/strategy_comparison.png'
        plt.savefig(filepath)
        return filepath
    
    @staticmethod
    def create_heatmap(results: List[RunMetrics]) -> str:
        """Create heatmap of strategy vs window size performance"""
        
        # Prepare data
        pivot_data = {}
        for result in results:
            key = (result.context_strategy, result.window_size)
            if key not in pivot_data:
                pivot_data[key] = []
            pivot_data[key].append(result.total_tokens)
        
        # Calculate averages
        heatmap_data = {}
        for (strategy, window_size), tokens_list in pivot_data.items():
            if strategy not in heatmap_data:
                heatmap_data[strategy] = {}
            heatmap_data[strategy][window_size] = sum(tokens_list) / len(tokens_list)
        
        # Create DataFrame
        df = pd.DataFrame(heatmap_data).T
        
        # Create heatmap
        plt.figure(figsize=(10, 6))
        sns.heatmap(df, annot=True, fmt='.0f', cmap='YlOrRd_r')
        plt.title('Average Token Usage: Strategy vs Window Size')
        plt.xlabel('Window Size')
        plt.ylabel('Strategy')
        
        filepath = 'evaluation_results/token_heatmap.png'
        plt.savefig(filepath)
        return filepath
```

## 7. CI/CD Integration

```yaml
# .github/workflows/evaluation.yml
name: Context Strategy Evaluation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  evaluate:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        test-suite: [simple, medium, complex]
        strategy: [no-op, sliding-window, smart-trim]
        window-size: [10000, 25000, 50000]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e .
          playwright install chromium
      
      - name: Run evaluation
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python -m browser_copilot.evaluate \
            --test-suite ${{ matrix.test-suite }} \
            --strategy ${{ matrix.strategy }} \
            --window-size ${{ matrix.window-size }} \
            --output-format json \
            --output-file results/${{ matrix.test-suite }}_${{ matrix.strategy }}_${{ matrix.window-size }}.json
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: evaluation-results
          path: results/
  
  analyze:
    needs: evaluate
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Download results
        uses: actions/download-artifact@v3
        with:
          name: evaluation-results
          path: results/
      
      - name: Generate report
        run: |
          python -m browser_copilot.analyze_results \
            --input-dir results/ \
            --output-file evaluation_report.html
      
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('evaluation_report.html', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## Evaluation Results\n\n' + report
            });
```

## 8. Usage Examples

### Running a Quick Evaluation
```bash
# Compare strategies on a specific test
python -m browser_copilot.evaluate \
  --test-suite examples/icims_job_search.md \
  --strategies all \
  --window-sizes 10000,25000,50000 \
  --runs 3 \
  --output evaluation_report.html
```

### Custom Evaluation Script
```python
# custom_evaluation.py
from browser_copilot.evaluation import EvaluationFramework, EvaluationConfig

async def main():
    config = EvaluationConfig(
        strategies=['smart-trim', 'sliding-window', 'no-op'],
        window_sizes=[25000],  # Focus on optimal size
        scenarios=['complex_workflow'],
        runs_per_config=5
    )
    
    framework = EvaluationFramework(config)
    report = await framework.run_full_evaluation()
    
    print(f"Optimal configuration: {report.optimal_configuration}")
    print(f"Key insights: {report.insights}")

if __name__ == "__main__":
    asyncio.run(main())
```

This implementation specification provides the concrete details needed to build the evaluation framework for Browser Copilot and similar agentic applications in enterprise environments.