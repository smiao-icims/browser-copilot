# Evaluation Framework Design Document

## Overview

This document outlines the technical design for Browser Copilot's evaluation framework, providing detailed architecture, implementation patterns, and integration strategies.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Interface                         │
│  browser-copilot eval --suite basic --compare gpt-4 claude  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                    Evaluation Runner                         │
├─────────────────────────────────────────────────────────────┤
│ • Suite Loader        • Model Manager    • Metric Collector │
│ • Test Executor       • Comparison Engine • Report Generator │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬─────────────────┐
        │               │               │                 │
┌───────┴──────┐ ┌─────┴──────┐ ┌─────┴──────┐ ┌───────┴──────┐
│Test Suites   │ │   Models   │ │  Storage   │ │   Reports    │
├──────────────┤ ├────────────┤ ├────────────┤ ├──────────────┤
│• Basic       │ │• GPT-4     │ │• SQLite    │ │• Summary     │
│• Intermediate│ │• Claude    │ │• History   │ │• Detailed    │
│• Advanced    │ │• Gemini    │ │• Baselines │ │• Comparison  │
│• Stress      │ │• Local     │ │• Metrics   │ │• Trends      │
└──────────────┘ └────────────┘ └────────────┘ └──────────────┘
```

### Component Design

#### 1. Evaluation Runner

```python
class EvalRunner:
    """Orchestrates evaluation execution."""

    def __init__(self):
        self.suite_loader = SuiteLoader()
        self.model_manager = ModelManager()
        self.metric_collector = MetricCollector()
        self.executor = TestExecutor()
        self.storage = EvalStorage()

    async def run_evaluation(
        self,
        suite_name: str,
        provider: str,
        model: str,
        config: Optional[EvalConfig] = None
    ) -> EvalRun:
        """Execute evaluation suite."""
        # Load suite
        suite = self.suite_loader.load(suite_name)

        # Initialize model
        llm = self.model_manager.create_model(provider, model)

        # Execute tests
        results = []
        for test in suite.tests:
            result = await self.executor.run_test(test, llm, config)
            results.append(result)

        # Collect metrics
        metrics = self.metric_collector.aggregate(results)

        # Store results
        eval_run = EvalRun(
            suite=suite_name,
            provider=provider,
            model=model,
            results=results,
            metrics=metrics
        )
        self.storage.save(eval_run)

        return eval_run
```

#### 2. Metric Collection

```python
class MetricCollector:
    """Collects and aggregates evaluation metrics."""

    def __init__(self):
        self.collectors = [
            SuccessMetricCollector(),
            TokenMetricCollector(),
            TimeMetricCollector(),
            ContextMetricCollector(),
            QualityMetricCollector()
        ]

    def collect_from_result(self, result: TestResult) -> Dict[str, Any]:
        """Extract metrics from single test result."""
        metrics = {}
        for collector in self.collectors:
            metrics.update(collector.collect(result))
        return metrics

    def aggregate(self, results: List[TestResult]) -> EvalMetrics:
        """Aggregate metrics across all test results."""
        all_metrics = [self.collect_from_result(r) for r in results]

        return EvalMetrics(
            success_rate=self._calculate_success_rate(results),
            total_tokens=sum(m['tokens'] for m in all_metrics),
            total_time=sum(m['execution_time'] for m in all_metrics),
            avg_time_per_step=self._calculate_avg_time(all_metrics),
            errors_encountered=sum(m['errors'] for m in all_metrics),
            retries_needed=sum(m['retries'] for m in all_metrics),
            context_metrics=self._aggregate_context_metrics(all_metrics)
        )
```

#### 3. Test Suites

```python
@dataclass
class TestSuite:
    """Defines a collection of tests for evaluation."""
    name: str
    description: str
    tests: List[TestCase]
    timeout: int = 300
    retry_limit: int = 2
    tags: List[str] = field(default_factory=list)

@dataclass
class TestCase:
    """Individual test case in a suite."""
    name: str
    path: str
    expected_outcomes: List[str]
    complexity: str  # basic, intermediate, advanced
    timeout: int = 60

class SuiteLoader:
    """Loads test suites from configuration."""

    def __init__(self, suite_dir: str = "evaluation/suites"):
        self.suite_dir = Path(suite_dir)
        self._suites = self._load_all_suites()

    def load(self, name: str) -> TestSuite:
        """Load a specific test suite."""
        if name not in self._suites:
            raise ValueError(f"Suite '{name}' not found")
        return self._suites[name]

    def _load_all_suites(self) -> Dict[str, TestSuite]:
        """Load all suite definitions."""
        suites = {}
        for suite_file in self.suite_dir.glob("*.yaml"):
            suite = self._parse_suite_file(suite_file)
            suites[suite.name] = suite
        return suites
```

#### 4. Model Comparison

```python
class ComparisonEngine:
    """Compares evaluation results across models."""

    def compare(
        self,
        runs: List[EvalRun],
        metrics: List[str] = None
    ) -> ComparisonResult:
        """Compare multiple evaluation runs."""
        if metrics is None:
            metrics = ['success_rate', 'total_tokens', 'total_time']

        comparison = ComparisonResult()

        for metric in metrics:
            values = {run.model: getattr(run.metrics, metric) for run in runs}
            comparison.add_metric_comparison(metric, values)

        # Statistical analysis
        comparison.calculate_significance()
        comparison.identify_best_performer()

        return comparison

    def compare_to_baseline(
        self,
        run: EvalRun,
        baseline: Baseline
    ) -> RegressionResult:
        """Check for regression against baseline."""
        regression = RegressionResult()

        for metric, baseline_value in baseline.metrics.items():
            current_value = getattr(run.metrics, metric)
            regression.check_metric(metric, current_value, baseline_value)

        return regression
```

### Data Models

```python
@dataclass
class EvalRun:
    """Complete evaluation run data."""
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    suite: str
    provider: str
    model: str
    config: Dict[str, Any]
    results: List[TestResult]
    metrics: EvalMetrics

@dataclass
class EvalMetrics:
    """Aggregated metrics for evaluation run."""
    # Success metrics
    success_rate: float
    steps_completed: int
    steps_total: int

    # Performance metrics
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_time: float
    avg_time_per_step: float

    # Quality metrics
    errors_encountered: int
    retries_needed: int
    human_in_loop_count: int

    # Context metrics
    context_metrics: ContextMetrics

    # Cost metrics
    estimated_cost: float

@dataclass
class ContextMetrics:
    """Context management specific metrics."""
    max_context_size: int
    avg_context_size: float
    trimming_events: int
    token_reduction_rate: float
    messages_preserved_rate: float
    strategy_used: str
```

### Storage Design

```python
class EvalStorage:
    """Manages evaluation data persistence."""

    def __init__(self, db_path: str = "evaluation.db"):
        self.db_path = db_path
        self._init_database()

    def save(self, run: EvalRun) -> None:
        """Save evaluation run to storage."""
        with self._get_connection() as conn:
            # Save run metadata
            conn.execute("""
                INSERT INTO eval_runs
                (id, timestamp, suite, provider, model, config)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                run.id,
                run.timestamp,
                run.suite,
                run.provider,
                run.model,
                json.dumps(run.config)
            ))

            # Save metrics
            self._save_metrics(conn, run.id, run.metrics)

            # Save detailed results
            self._save_results(conn, run.id, run.results)

    def query_runs(
        self,
        suite: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        start_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[EvalRun]:
        """Query historical runs with filters."""
        # Build dynamic query based on filters
        # Return list of EvalRun objects
```

### Reporting System

```python
class ReportGenerator:
    """Generates evaluation reports in multiple formats."""

    def __init__(self):
        self.formatters = {
            'markdown': MarkdownFormatter(),
            'json': JsonFormatter(),
            'html': HtmlFormatter()
        }

    def generate_summary_report(
        self,
        run: EvalRun,
        format: str = 'markdown'
    ) -> str:
        """Generate summary report for single run."""
        formatter = self.formatters[format]

        sections = [
            self._create_overview_section(run),
            self._create_metrics_section(run),
            self._create_performance_section(run),
            self._create_recommendations_section(run)
        ]

        return formatter.format_report(sections)

    def generate_comparison_report(
        self,
        comparison: ComparisonResult,
        format: str = 'markdown'
    ) -> str:
        """Generate comparison report across models."""
        formatter = self.formatters[format]

        sections = [
            self._create_comparison_overview(comparison),
            self._create_metric_tables(comparison),
            self._create_winner_analysis(comparison),
            self._create_recommendation(comparison)
        ]

        return formatter.format_report(sections)
```

## Integration Patterns

### 1. CLI Integration

```python
# In cli.py
@click.group()
def eval():
    """Evaluation framework commands."""
    pass

@eval.command()
@click.option('--suite', required=True, help='Test suite to run')
@click.option('--provider', required=True, help='LLM provider')
@click.option('--model', required=True, help='Model name')
@click.option('--compare', multiple=True, help='Additional models to compare')
@click.option('--output', default='summary', help='Report type')
def run(suite, provider, model, compare, output):
    """Run evaluation suite."""
    runner = EvalRunner()

    # Run primary evaluation
    primary_run = runner.run_evaluation(suite, provider, model)

    # Run comparisons if requested
    comparison_runs = []
    for comp_model in compare:
        comp_provider, comp_name = comp_model.split('/')
        comp_run = runner.run_evaluation(suite, comp_provider, comp_name)
        comparison_runs.append(comp_run)

    # Generate report
    reporter = ReportGenerator()
    if comparison_runs:
        comparison = ComparisonEngine().compare([primary_run] + comparison_runs)
        report = reporter.generate_comparison_report(comparison)
    else:
        report = reporter.generate_summary_report(primary_run)

    click.echo(report)
```

### 2. Telemetry Integration

```python
class EvalTelemetryCallback(BaseTelemetryCallback):
    """Telemetry callback for evaluation metrics."""

    def __init__(self, collector: MetricCollector):
        self.collector = collector
        self.events = []

    def on_llm_start(self, **kwargs):
        self.start_time = time.time()

    def on_llm_end(self, response, **kwargs):
        self.events.append({
            'type': 'llm_call',
            'duration': time.time() - self.start_time,
            'tokens': response.usage_metadata
        })

    def get_metrics(self) -> Dict[str, Any]:
        return self.collector.extract_from_events(self.events)
```

### 3. Context Management Integration

```python
class ContextAwareEvaluator:
    """Evaluates context management effectiveness."""

    def evaluate_context_strategy(
        self,
        suite: TestSuite,
        strategies: List[str]
    ) -> ContextComparisonResult:
        """Compare different context strategies."""
        results = {}

        for strategy in strategies:
            config = ContextConfig(strategy=strategy)
            run = self.runner.run_evaluation(
                suite.name,
                provider='openai',
                model='gpt-4',
                context_config=config
            )
            results[strategy] = run

        return self._analyze_context_impact(results)
```

## Testing Strategy

### Unit Tests
```python
def test_metric_collection():
    """Test metric collection accuracy."""
    collector = MetricCollector()
    result = create_mock_test_result(
        success=True,
        tokens=1500,
        time=45.2
    )

    metrics = collector.collect_from_result(result)

    assert metrics['success'] == True
    assert metrics['tokens'] == 1500
    assert metrics['execution_time'] == 45.2

def test_comparison_significance():
    """Test statistical significance calculation."""
    engine = ComparisonEngine()
    runs = [
        create_mock_run('gpt-4', success_rate=0.95),
        create_mock_run('gpt-3.5', success_rate=0.85)
    ]

    comparison = engine.compare(runs)

    assert comparison.is_significant('success_rate')
    assert comparison.best_performer('success_rate') == 'gpt-4'
```

### Integration Tests
```python
async def test_full_evaluation_flow():
    """Test complete evaluation workflow."""
    runner = EvalRunner()

    # Run evaluation
    run = await runner.run_evaluation(
        suite='basic',
        provider='openai',
        model='gpt-3.5-turbo'
    )

    # Verify results
    assert run.metrics.success_rate > 0.8
    assert run.metrics.total_tokens > 0
    assert len(run.results) == 5  # basic suite has 5 tests

    # Check storage
    stored = runner.storage.get_run(run.id)
    assert stored == run
```

## Performance Considerations

1. **Parallel Execution**: Run independent tests concurrently
2. **Metric Collection**: Use streaming aggregation to avoid memory issues
3. **Storage Optimization**: Index frequently queried fields
4. **Caching**: Cache model instances and test suites
5. **Resource Limits**: Implement timeouts and memory limits

## Security Considerations

1. **API Key Management**: Secure storage of provider credentials
2. **Test Isolation**: Sandboxed execution environment
3. **Data Privacy**: No sensitive data in test cases
4. **Access Control**: Role-based access to evaluation data

## Future Enhancements

1. **Distributed Evaluation**: Run on multiple machines
2. **Real-time Monitoring**: Live evaluation dashboards
3. **ML-based Analysis**: Predictive performance modeling
4. **Community Benchmarks**: Shared evaluation sets
5. **Visual Testing**: Screenshot comparison capabilities
