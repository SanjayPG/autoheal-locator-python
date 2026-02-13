"""
AutoHeal Reporter - Tracks and reports all selector usage and healing strategies.

This module provides comprehensive reporting capabilities for the AutoHeal framework,
including HTML, JSON, and text report generation with detailed metrics and AI usage statistics.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

from autoheal.config.ai_config import AIConfig


class SelectorStrategy(Enum):
    """Enumeration of selector resolution strategies."""

    ORIGINAL_SELECTOR = ("Original Selector", "[ORIG]")
    DOM_ANALYSIS = ("DOM Analysis (AI)", "[DOM]")
    VISUAL_ANALYSIS = ("Visual Analysis (AI)", "[VIS]")
    AI_DISAMBIGUATION = ("AI Disambiguation", "[DISAMB]")
    CACHED = ("Cached Result", "[CACHE]")
    FAILED = ("Failed", "[FAIL]")

    def __init__(self, display_name: str, icon: str):
        self._display_name = display_name
        self._icon = icon

    @property
    def display_name(self) -> str:
        """Get the human-readable display name."""
        return self._display_name

    @property
    def icon(self) -> str:
        """Get the icon/prefix for console output."""
        return self._icon


@dataclass
class SelectorReport:
    """Data class representing a single selector usage event."""

    original_selector: str
    actual_selector: Optional[str]
    description: str
    strategy: SelectorStrategy
    execution_time_ms: int
    success: bool
    element_details: Optional[str]
    reasoning: Optional[str]
    tokens_used: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    # AI Implementation Details
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    api_endpoint: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    retry_count: Optional[int] = None
    prompt_type: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0


class AutoHealReporter:
    """
    AutoHeal Reporter - Tracks and reports all selector usage and healing strategies.

    This class collects metrics about selector usage, healing strategies, and AI interactions,
    and generates comprehensive reports in HTML, JSON, and text formats.

    Attributes:
        reports: List of all selector usage events.
        test_run_id: Unique identifier for this test run.
        start_time: When reporting started.
        ai_provider: AI provider name.
        ai_model: AI model being used.
        api_endpoint: AI API endpoint URL.
        dom_temperature: Temperature for DOM analysis.
        visual_temperature: Temperature for visual analysis.
        dom_max_tokens: Max tokens for DOM analysis.
        visual_max_tokens: Max tokens for visual analysis.
        max_retries: Maximum retry attempts.

    Examples:
        >>> # Create reporter with defaults
        >>> reporter = AutoHealReporter()

        >>> # Create reporter with AI config
        >>> from autoheal.config.ai_config import AIConfig
        >>> ai_config = AIConfig(provider="openai", model="gpt-4o-mini")
        >>> reporter = AutoHealReporter(ai_config)

        >>> # Record selector usage
        >>> reporter.record_selector_usage(
        ...     original_selector="#login",
        ...     description="Login button",
        ...     strategy=SelectorStrategy.ORIGINAL_SELECTOR,
        ...     execution_time_ms=50,
        ...     success=True,
        ...     actual_selector="#login",
        ...     element_details="button#login.btn",
        ...     reasoning="Original selector worked"
        ... )

        >>> # Generate reports
        >>> reporter.generate_html_report()
        >>> reporter.generate_json_report()
        >>> reporter.generate_text_report()
    """

    def __init__(self, ai_config: Optional[AIConfig] = None):
        """
        Initialize the AutoHeal Reporter.

        Args:
            ai_config: Optional AI configuration for tracking AI usage details.
        """
        self.reports: List[SelectorReport] = []
        self.test_run_id = f"AutoHeal_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        self.start_time = datetime.now()

        # AI Configuration details
        if ai_config:
            # Convert AIProvider enum to string name for display
            self.ai_provider = ai_config.provider.name if hasattr(ai_config.provider, 'name') else str(ai_config.provider)
            self.ai_model = ai_config.model
            self.api_endpoint = ai_config.api_url
            self.dom_temperature = ai_config.temperature_dom
            self.visual_temperature = ai_config.temperature_visual
            self.dom_max_tokens = ai_config.max_tokens_dom
            self.visual_max_tokens = ai_config.max_tokens_visual
            self.max_retries = ai_config.max_retries
        else:
            # Default values when no configuration is provided
            self.ai_provider = "OpenAI"
            self.ai_model = "gpt-4o-mini"
            self.api_endpoint = "https://api.openai.com/v1/chat/completions"
            self.dom_temperature = 0.1
            self.visual_temperature = 0.0
            self.dom_max_tokens = 500
            self.visual_max_tokens = 1000
            self.max_retries = 3

    def record_selector_usage(
        self,
        original_selector: str,
        description: str,
        strategy: SelectorStrategy,
        execution_time_ms: int,
        success: bool,
        actual_selector: Optional[str],
        element_details: Optional[str],
        reasoning: Optional[str],
        tokens_used: int = 0
    ) -> None:
        """
        Record a selector usage event.

        Args:
            original_selector: The original selector string.
            description: Human-readable description of the element.
            strategy: The strategy used to locate the element.
            execution_time_ms: Execution time in milliseconds.
            success: Whether the operation was successful.
            actual_selector: The actual selector that was used (if healed).
            element_details: Details about the located element.
            reasoning: Explanation of why this strategy was used.
            tokens_used: Number of AI tokens consumed (if applicable).
        """
        report = SelectorReport(
            original_selector=original_selector,
            actual_selector=actual_selector,
            description=description,
            strategy=strategy,
            execution_time_ms=execution_time_ms,
            success=success,
            element_details=element_details,
            reasoning=reasoning,
            tokens_used=tokens_used,
            timestamp=datetime.now()
        )

        # Set AI implementation details for AI-based strategies
        if strategy in (SelectorStrategy.DOM_ANALYSIS, SelectorStrategy.VISUAL_ANALYSIS):
            report.ai_provider = self.ai_provider
            report.ai_model = self.ai_model
            report.api_endpoint = self.api_endpoint
            report.max_tokens = (
                self.dom_max_tokens
                if strategy == SelectorStrategy.DOM_ANALYSIS
                else self.visual_max_tokens
            )
            report.temperature = (
                self.dom_temperature
                if strategy == SelectorStrategy.DOM_ANALYSIS
                else self.visual_temperature
            )
            report.retry_count = self.max_retries
            report.prompt_type = (
                "DOM Analysis"
                if strategy == SelectorStrategy.DOM_ANALYSIS
                else "Visual Analysis"
            )
            # Token breakdown will be updated later if available
            report.prompt_tokens = 0
            report.completion_tokens = 0

        self.reports.append(report)

        # Also log to console for immediate visibility
        self._log_to_console(report)

    def _log_to_console(self, report: SelectorReport) -> None:
        """Log a selector report to console."""
        icon = report.strategy.icon
        status_icon = "[SUCCESS]" if report.success else "[FAILED]"

        # Include token usage if available and strategy uses AI
        token_info = ""
        if (report.tokens_used > 0 and
            report.strategy in (SelectorStrategy.DOM_ANALYSIS, SelectorStrategy.VISUAL_ANALYSIS)):
            token_info = f" [{report.tokens_used} tokens]"

        actual_selector_display = report.actual_selector if report.success else "FAILED"

        print(
            f"{status_icon} {icon} [{report.execution_time_ms}ms]{token_info} "
            f"{report.original_selector} -> {actual_selector_display}"
        )

        if (report.original_selector != report.actual_selector and
            report.success and report.reasoning):
            print(f"   [HEALED] {report.reasoning}")

    def generate_html_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate comprehensive HTML report.

        Args:
            output_path: Optional custom output path. If not provided, uses test_run_id.

        Returns:
            Path to the generated HTML file.

        Examples:
            >>> reporter = AutoHealReporter()
            >>> # ... record some usage ...
            >>> file_path = reporter.generate_html_report()
            >>> print(f"Report generated: {file_path}")
        """
        if output_path is None:
            output_path = f"{self.test_run_id}_AutoHeal_Report.html"

        html_content = self._generate_html_content()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML Report generated: {Path(output_path).absolute()}")
        return output_path

    def generate_json_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate JSON report for programmatic consumption.

        Args:
            output_path: Optional custom output path. If not provided, uses test_run_id.

        Returns:
            Path to the generated JSON file.

        Examples:
            >>> reporter = AutoHealReporter()
            >>> # ... record some usage ...
            >>> file_path = reporter.generate_json_report()
        """
        if output_path is None:
            output_path = f"{self.test_run_id}_AutoHeal_Report.json"

        # Calculate statistics
        successful = sum(1 for r in self.reports if r.success)
        original_strategy = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.ORIGINAL_SELECTOR
        )
        dom_healed = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.DOM_ANALYSIS
        )
        visual_healed = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.VISUAL_ANALYSIS
        )
        ai_disambiguated = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.AI_DISAMBIGUATION
        )
        cached = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.CACHED
        )

        report_data = {
            "testRunId": self.test_run_id,
            "startTime": self.start_time.isoformat(),
            "endTime": datetime.now().isoformat(),
            "totalSelectors": len(self.reports),
            "statistics": {
                "successful": successful,
                "failed": len(self.reports) - successful,
                "originalSelector": original_strategy,
                "domHealed": dom_healed,
                "visualHealed": visual_healed,
                "aiDisambiguated": ai_disambiguated,
                "cached": cached,
                "successRate": (successful / len(self.reports) * 100) if self.reports else 0
            }
        }

        # AI Implementation Details
        has_ai_strategies = any(
            r.strategy in (SelectorStrategy.DOM_ANALYSIS, SelectorStrategy.VISUAL_ANALYSIS, SelectorStrategy.AI_DISAMBIGUATION)
            for r in self.reports
        )

        if has_ai_strategies:
            total_tokens = sum(r.tokens_used for r in self.reports)
            dom_tokens = sum(
                r.tokens_used for r in self.reports
                if r.strategy == SelectorStrategy.DOM_ANALYSIS
            )
            visual_tokens = sum(
                r.tokens_used for r in self.reports
                if r.strategy == SelectorStrategy.VISUAL_ANALYSIS
            )

            ai_details = {
                "configuration": {
                    "provider": self.ai_provider,
                    "model": self.ai_model,
                    "apiEndpoint": self.api_endpoint,
                    "maxTokensDOM": self.dom_max_tokens,
                    "maxTokensVisual": self.visual_max_tokens,
                    "temperatureDOM": self.dom_temperature,
                    "temperatureVisual": self.visual_temperature,
                    "maxRetries": self.max_retries
                },
                "usage": {
                    "domAnalysisRequests": dom_healed,
                    "visualAnalysisRequests": visual_healed,
                    "totalTokens": total_tokens,
                    "domTokens": dom_tokens,
                    "visualTokens": visual_tokens
                }
            }

            if total_tokens > 0:
                estimated_cost = (total_tokens * 0.375) / 1000000.0
                ai_details["usage"]["estimatedCostUSD"] = round(estimated_cost, 4)

            report_data["aiImplementation"] = ai_details

        # Detailed reports
        selector_reports = []
        for report in self.reports:
            report_dict = {
                "originalSelector": report.original_selector,
                "actualSelector": report.actual_selector,
                "description": report.description,
                "strategy": report.strategy.name,
                "executionTimeMs": report.execution_time_ms,
                "success": report.success,
                "elementDetails": report.element_details,
                "tokensUsed": report.tokens_used,
                "reasoning": report.reasoning,
                "timestamp": report.timestamp.isoformat()
            }

            # Add AI implementation details for AI-based strategies
            if report.strategy in (SelectorStrategy.DOM_ANALYSIS, SelectorStrategy.VISUAL_ANALYSIS):
                report_dict["aiImplementation"] = {
                    "provider": report.ai_provider,
                    "model": report.ai_model,
                    "promptType": report.prompt_type,
                    "temperature": report.temperature,
                    "maxTokens": report.max_tokens
                }

            selector_reports.append(report_dict)

        report_data["selectorReports"] = selector_reports

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)

        print(f"JSON Report generated: {Path(output_path).absolute()}")
        return output_path

    def generate_text_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate text report for easy reading.

        Args:
            output_path: Optional custom output path. If not provided, uses test_run_id.

        Returns:
            Path to the generated text file.

        Examples:
            >>> reporter = AutoHealReporter()
            >>> # ... record some usage ...
            >>> file_path = reporter.generate_text_report()
        """
        if output_path is None:
            output_path = f"{self.test_run_id}_AutoHeal_Report.txt"

        text_content = self._generate_text_content()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_content)

        print(f"Text Report generated: {Path(output_path).absolute()}")
        return output_path

    def print_summary(self) -> None:
        """Print summary statistics to console."""
        successful = sum(1 for r in self.reports if r.success)
        original_strategy = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.ORIGINAL_SELECTOR
        )
        dom_healed = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.DOM_ANALYSIS
        )
        visual_healed = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.VISUAL_ANALYSIS
        )
        ai_disambiguated = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.AI_DISAMBIGUATION
        )
        cached = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.CACHED
        )

        total_tokens = sum(r.tokens_used for r in self.reports)
        dom_tokens = sum(
            r.tokens_used for r in self.reports
            if r.strategy == SelectorStrategy.DOM_ANALYSIS
        )
        visual_tokens = sum(
            r.tokens_used for r in self.reports
            if r.strategy == SelectorStrategy.VISUAL_ANALYSIS
        )
        disamb_tokens = sum(
            r.tokens_used for r in self.reports
            if r.strategy == SelectorStrategy.AI_DISAMBIGUATION
        )

        print("\n" + "=" * 60)
        print("AUTOHEAL TEST SUMMARY")
        print("=" * 60)
        print(
            f"Total: {len(self.reports)} | Success: {successful} | "
            f"Failed: {len(self.reports) - successful}"
        )
        print(
            f"Original: {original_strategy} | DOM Healed: {dom_healed} | "
            f"Visual: {visual_healed} | AI Disambiguated: {ai_disambiguated} | Cached: {cached}"
        )
        if total_tokens > 0:
            print(
                f"Token Usage - Total: {total_tokens} | DOM: {dom_tokens} | "
                f"Visual: {visual_tokens} | Disamb: {disamb_tokens}"
            )
        print("=" * 60)

    def _generate_html_content(self) -> str:
        """Generate the HTML content for the report."""
        successful = sum(1 for r in self.reports if r.success)
        original_strategy = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.ORIGINAL_SELECTOR
        )
        dom_healed = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.DOM_ANALYSIS
        )
        visual_healed = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.VISUAL_ANALYSIS
        )
        ai_disambiguated = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.AI_DISAMBIGUATION
        )
        cached = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.CACHED
        )

        html_parts = []

        # HTML Header and Styles
        html_parts.append("""<!DOCTYPE html><html><head>""")
        html_parts.append(f"<title>AutoHeal Test Report - {self.test_run_id}</title>")
        html_parts.append("""<style>
body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }
.container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
.stat-box { background: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }
.stat-value { font-size: 2em; font-weight: bold; color: #2980b9; }
table { width: 100%; border-collapse: collapse; margin: 20px 0; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background-color: #34495e; color: white; }
tr:nth-child(even) { background-color: #f2f2f2; }
.original { background-color: #d5edd0 !important; }
.dom-healed { background-color: #fff2cc !important; }
.visual-healed { background-color: #ffe6e6 !important; }
.ai-disambiguated { background-color: #e8daef !important; }
.cached { background-color: #e1f5fe !important; }
.failed { background-color: #ffebee !important; }
.success { color: #27ae60; font-weight: bold; }
.failure { color: #e74c3c; font-weight: bold; }
.filter-section { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db; }
.filter-section h3 { margin-top: 0; color: #2c3e50; }
.filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }
.filter-group { }
.filter-group label { display: block; margin-bottom: 5px; font-weight: 600; color: #2c3e50; }
.filter-select { width: 100%; padding: 8px 12px; border: 2px solid #bdc3c7; border-radius: 4px; background: white; }
.filter-select:focus { border-color: #3498db; outline: none; }
.filter-stats { text-align: center; margin: 15px 0; padding: 10px; background: #ecf0f1; border-radius: 4px; }
.reset-btn { background: #e74c3c; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: 600; }
.reset-btn:hover { background: #c0392b; }
.search-box { width: 100%; padding: 8px 12px; border: 2px solid #bdc3c7; border-radius: 4px; }
.search-box:focus { border-color: #3498db; outline: none; }
</style>""")
        html_parts.append("</head><body>")

        # Container
        html_parts.append("<div class='container'>")
        html_parts.append("<h1>[SEARCH] AutoHeal Test Report</h1>")
        html_parts.append(f"<p><strong>Test Run:</strong> {self.test_run_id}</p>")
        html_parts.append(
            f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
        )

        # Statistics
        html_parts.append("<div class='stats'>")
        html_parts.append(f"<div class='stat-box'><div class='stat-value'>{len(self.reports)}</div><div>Total Selectors</div></div>")
        html_parts.append(f"<div class='stat-box'><div class='stat-value'>{successful}</div><div>Successful</div></div>")
        html_parts.append(f"<div class='stat-box'><div class='stat-value'>{original_strategy}</div><div>Original Selectors</div></div>")
        html_parts.append(f"<div class='stat-box'><div class='stat-value'>{dom_healed}</div><div>DOM Healed</div></div>")
        html_parts.append(f"<div class='stat-box'><div class='stat-value'>{visual_healed}</div><div>Visual Healed</div></div>")
        html_parts.append(f"<div class='stat-box'><div class='stat-value'>{ai_disambiguated}</div><div>AI Disambiguated</div></div>")
        html_parts.append(f"<div class='stat-box'><div class='stat-value'>{cached}</div><div>Cached Results</div></div>")
        html_parts.append("</div>")

        # Filter Section
        html_parts.append("""<div class='filter-section'>
<h3>Filter Results</h3>
<div class='filters'>
  <div class='filter-group'>
    <label for='strategyFilter'>Strategy:</label>
    <select id='strategyFilter' class='filter-select'>
      <option value=''>All Strategies</option>
    </select>
  </div>
  <div class='filter-group'>
    <label for='statusFilter'>Status:</label>
    <select id='statusFilter' class='filter-select'>
      <option value=''>All Status</option>
    </select>
  </div>
  <div class='filter-group'>
    <label for='performanceFilter'>Performance:</label>
    <select id='performanceFilter' class='filter-select'>
      <option value=''>All Performance</option>
    </select>
  </div>
  <div class='filter-group'>
    <label for='searchBox'>Search:</label>
    <input type='text' id='searchBox' class='search-box' placeholder='Search all columns...'>
  </div>
</div>
<div class='filter-stats'>""")
        html_parts.append(f"  <span id='resultCount'>Showing {len(self.reports)} of {len(self.reports)} results</span>")
        html_parts.append("""  <button id='resetFilters' class='reset-btn'>Reset Filters</button>
</div>
</div>""")

        # AI Implementation Details
        has_ai_strategies = any(
            r.strategy in (SelectorStrategy.DOM_ANALYSIS, SelectorStrategy.VISUAL_ANALYSIS)
            for r in self.reports
        )

        if has_ai_strategies:
            total_tokens = sum(r.tokens_used for r in self.reports)
            dom_tokens = sum(
                r.tokens_used for r in self.reports
                if r.strategy == SelectorStrategy.DOM_ANALYSIS
            )
            visual_tokens = sum(
                r.tokens_used for r in self.reports
                if r.strategy == SelectorStrategy.VISUAL_ANALYSIS
            )

            html_parts.append("<h2>[AI] AI Implementation Details</h2>")
            html_parts.append("<div style='background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;'>")
            html_parts.append("<div style='display: grid; grid-template-columns: 1fr 1fr; gap: 20px;'>")

            # Configuration Details
            html_parts.append("<div>")
            html_parts.append("<h3>Configuration</h3>")
            html_parts.append("<ul>")
            html_parts.append(f"<li><strong>Provider:</strong> {self.ai_provider}</li>")
            html_parts.append(f"<li><strong>Model:</strong> {self.ai_model}</li>")
            html_parts.append(f"<li><strong>API Endpoint:</strong> {self.api_endpoint}</li>")
            html_parts.append(f"<li><strong>Max Tokens:</strong> {self.dom_max_tokens} (DOM), {self.visual_max_tokens} (Visual)</li>")
            html_parts.append(f"<li><strong>Temperature:</strong> {self.dom_temperature} (DOM), {self.visual_temperature} (Visual)</li>")
            html_parts.append(f"<li><strong>Max Retries:</strong> {self.max_retries}</li>")
            html_parts.append("</ul>")
            html_parts.append("</div>")

            # Statistics
            html_parts.append("<div>")
            html_parts.append("<h3>AI Usage Statistics</h3>")
            html_parts.append("<ul>")
            html_parts.append(f"<li><strong>DOM Analysis Requests:</strong> {dom_healed}</li>")
            html_parts.append(f"<li><strong>Visual Analysis Requests:</strong> {visual_healed}</li>")
            html_parts.append(f"<li><strong>Total Tokens:</strong> {total_tokens}</li>")
            html_parts.append(f"<li><strong>DOM Tokens:</strong> {dom_tokens}</li>")
            html_parts.append(f"<li><strong>Visual Tokens:</strong> {visual_tokens}</li>")

            if total_tokens > 0:
                estimated_cost = (total_tokens * 0.375) / 1000000.0
                html_parts.append(f"<li><strong>Estimated Cost:</strong> ${estimated_cost:.4f}</li>")

            html_parts.append("</ul>")
            html_parts.append("</div>")
            html_parts.append("</div>")
            html_parts.append("</div>")

        # Detailed table
        html_parts.append("<h2>[REPORT] Detailed Selector Report</h2>")
        html_parts.append("<table id='reportTable'>")
        html_parts.append("<tr><th>Original Selector</th><th>Strategy</th><th>Time (ms)</th><th>Status</th><th>Actual Selector</th><th>Element</th><th>Tokens</th><th>Reasoning</th></tr>")

        for report in self.reports:
            row_class = self._get_row_class(report.strategy, report.success)
            status_class = "success" if report.success else "failure"
            status = "[SUCCESS] SUCCESS" if report.success else "[FAILED] FAILED"

            html_parts.append(f"<tr class='{row_class}'>")
            html_parts.append(f"<td><code>{report.original_selector}</code></td>")
            html_parts.append(f"<td>{report.strategy.icon} {report.strategy.display_name}</td>")
            html_parts.append(f"<td>{report.execution_time_ms}</td>")
            html_parts.append(f"<td class='{status_class}'>{status}</td>")
            html_parts.append(f"<td><code>{report.actual_selector if report.actual_selector else '-'}</code></td>")
            html_parts.append(f"<td>{report.element_details if report.element_details else '-'}</td>")

            # Add tokens column - show tokens only for AI strategies
            if (report.tokens_used > 0 and
                report.strategy in (SelectorStrategy.DOM_ANALYSIS, SelectorStrategy.VISUAL_ANALYSIS)):
                html_parts.append(f"<td>{report.tokens_used}</td>")
            else:
                html_parts.append("<td>-</td>")

            html_parts.append(f"<td>{report.reasoning if report.reasoning else '-'}</td>")
            html_parts.append("</tr>")

        html_parts.append("</table>")

        # JavaScript for filtering
        html_parts.append(self._get_filter_javascript())

        html_parts.append("</div>")
        html_parts.append("</body></html>")

        return "".join(html_parts)

    def _generate_text_content(self) -> str:
        """Generate the text content for the report."""
        lines = []

        lines.append("=" * 47)
        lines.append("         AutoHeal Test Report")
        lines.append("=" * 47)
        lines.append(f"Test Run ID: {self.test_run_id}")
        lines.append(f"Start Time: {self.start_time}")
        lines.append(f"End Time: {datetime.now()}")
        lines.append(f"Total Selectors Tested: {len(self.reports)}")
        lines.append("=" * 47)
        lines.append("")

        # Statistics
        successful = sum(1 for r in self.reports if r.success)
        original_strategy = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.ORIGINAL_SELECTOR
        )
        dom_healed = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.DOM_ANALYSIS
        )
        visual_healed = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.VISUAL_ANALYSIS
        )
        ai_disambiguated = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.AI_DISAMBIGUATION
        )
        cached = sum(
            1 for r in self.reports
            if r.strategy == SelectorStrategy.CACHED
        )

        # Token usage statistics
        total_tokens = sum(r.tokens_used for r in self.reports)
        dom_tokens = sum(
            r.tokens_used for r in self.reports
            if r.strategy == SelectorStrategy.DOM_ANALYSIS
        )
        visual_tokens = sum(
            r.tokens_used for r in self.reports
            if r.strategy == SelectorStrategy.VISUAL_ANALYSIS
        )
        disamb_tokens = sum(
            r.tokens_used for r in self.reports
            if r.strategy == SelectorStrategy.AI_DISAMBIGUATION
        )

        lines.append("SUMMARY STATISTICS:")
        success_rate = (successful / len(self.reports) * 100) if self.reports else 0
        lines.append(f"- Successful: {successful} ({success_rate:.1f}%)")
        lines.append(f"- Failed: {len(self.reports) - successful}")
        lines.append(f"- Original Selectors (no healing): {original_strategy}")
        lines.append(f"- DOM Healed: {dom_healed}")
        lines.append(f"- Visual Healed: {visual_healed}")
        lines.append(f"- AI Disambiguated: {ai_disambiguated}")
        lines.append(f"- Cached Results: {cached}")
        if total_tokens > 0:
            lines.append(f"- Token Usage - Total: {total_tokens} | DOM: {dom_tokens} | Visual: {visual_tokens} | Disamb: {disamb_tokens}")
        lines.append("")

        # AI Implementation Details
        has_ai_strategies = any(
            r.strategy in (SelectorStrategy.DOM_ANALYSIS, SelectorStrategy.VISUAL_ANALYSIS)
            for r in self.reports
        )

        if has_ai_strategies:
            lines.append("AI IMPLEMENTATION DETAILS:")
            lines.append("=" * 47)
            lines.append("Configuration:")
            lines.append(f"- Provider: {self.ai_provider}")
            lines.append(f"- Model: {self.ai_model}")
            lines.append(f"- API Endpoint: {self.api_endpoint}")
            lines.append(f"- Max Tokens: {self.dom_max_tokens} (DOM), {self.visual_max_tokens} (Visual)")
            lines.append(f"- Temperature: {self.dom_temperature} (DOM), {self.visual_temperature} (Visual)")
            lines.append(f"- Max Retries: {self.max_retries}")
            lines.append("")

            lines.append("AI Usage Statistics:")
            lines.append(f"- DOM Analysis Requests: {dom_healed}")
            lines.append(f"- Visual Analysis Requests: {visual_healed}")
            lines.append(f"- Total Tokens: {total_tokens}")
            lines.append(f"- DOM Tokens: {dom_tokens}")
            lines.append(f"- Visual Tokens: {visual_tokens}")

            if total_tokens > 0:
                estimated_cost = (total_tokens * 0.375) / 1000000.0
                lines.append(f"- Estimated Cost: ${estimated_cost:.4f}")
            lines.append("")

        lines.append("DETAILED SELECTOR REPORT:")
        lines.append("=" * 47)

        for i, report in enumerate(self.reports, 1):
            lines.append(f"{i}. {report.original_selector}")
            lines.append(f"   Strategy: {report.strategy.icon} {report.strategy.display_name}")
            lines.append(f"   Time: {report.execution_time_ms}ms")
            lines.append(f"   Status: {'SUCCESS' if report.success else 'FAILED'}")

            # Add tokens if available for AI strategies
            if (report.tokens_used > 0 and
                report.strategy in (SelectorStrategy.DOM_ANALYSIS, SelectorStrategy.VISUAL_ANALYSIS)):
                lines.append(f"   Tokens: {report.tokens_used}")

            if report.success:
                lines.append(f"   Actual Selector: {report.actual_selector}")
                if report.element_details:
                    lines.append(f"   Element: {report.element_details}")
                if report.reasoning:
                    lines.append(f"   Reasoning: {report.reasoning}")

            lines.append(f"   Description: {report.description}")
            lines.append(f"   Timestamp: {report.timestamp.strftime('%H:%M:%S')}")
            lines.append("-" * 47)

        return "\n".join(lines)

    def _get_row_class(self, strategy: SelectorStrategy, success: bool) -> str:
        """Get the CSS class for a table row."""
        if not success:
            return "failed"

        strategy_classes = {
            SelectorStrategy.ORIGINAL_SELECTOR: "original",
            SelectorStrategy.DOM_ANALYSIS: "dom-healed",
            SelectorStrategy.VISUAL_ANALYSIS: "visual-healed",
            SelectorStrategy.AI_DISAMBIGUATION: "ai-disambiguated",
            SelectorStrategy.CACHED: "cached",
            SelectorStrategy.FAILED: "failed"
        }
        return strategy_classes.get(strategy, "")

    def _get_filter_javascript(self) -> str:
        """Get the JavaScript code for filtering functionality."""
        return """<script>
// Filter functionality
document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('reportTable');
    const rows = Array.from(table.querySelectorAll('tr')).slice(1); // Skip header
    const strategyFilter = document.getElementById('strategyFilter');
    const statusFilter = document.getElementById('statusFilter');
    const performanceFilter = document.getElementById('performanceFilter');
    const searchBox = document.getElementById('searchBox');
    const resetBtn = document.getElementById('resetFilters');
    const resultCount = document.getElementById('resultCount');

    // Populate filter options dynamically
    const strategies = new Set();
    const statuses = new Set();
    const performances = new Set();

    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 4) {
            strategies.add(cells[1].textContent.trim());
            statuses.add(cells[3].textContent.trim());
            const time = parseInt(cells[2].textContent.trim());
            if (time < 100) performances.add('Fast (<100ms)');
            else if (time < 500) performances.add('Medium (100-500ms)');
            else performances.add('Slow (>500ms)');
        }
    });

    // Add options to dropdowns
    strategies.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s; opt.textContent = s;
        strategyFilter.appendChild(opt);
    });
    statuses.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s; opt.textContent = s;
        statusFilter.appendChild(opt);
    });
    performances.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p; opt.textContent = p;
        performanceFilter.appendChild(opt);
    });

    // Filter function
    function applyFilters() {
        const strategyValue = strategyFilter.value;
        const statusValue = statusFilter.value;
        const performanceValue = performanceFilter.value;
        const searchValue = searchBox.value.toLowerCase();
        let visibleCount = 0;

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            let show = true;

            if (cells.length >= 4) {
                // Strategy filter
                if (strategyValue && cells[1].textContent.trim() !== strategyValue) {
                    show = false;
                }
                // Status filter
                if (statusValue && cells[3].textContent.trim() !== statusValue) {
                    show = false;
                }
                // Performance filter
                if (performanceValue) {
                    const time = parseInt(cells[2].textContent.trim());
                    let perfCategory = '';
                    if (time < 100) perfCategory = 'Fast (<100ms)';
                    else if (time < 500) perfCategory = 'Medium (100-500ms)';
                    else perfCategory = 'Slow (>500ms)';
                    if (perfCategory !== performanceValue) show = false;
                }
                // Search filter
                if (searchValue) {
                    const rowText = Array.from(cells).map(c => c.textContent.toLowerCase()).join(' ');
                    if (!rowText.includes(searchValue)) show = false;
                }
            }

            row.style.display = show ? '' : 'none';
            if (show) visibleCount++;
        });

        resultCount.textContent = `Showing ${visibleCount} of ${rows.length} results`;
    }

    // Reset function
    function resetFilters() {
        strategyFilter.value = '';
        statusFilter.value = '';
        performanceFilter.value = '';
        searchBox.value = '';
        applyFilters();
    }

    // Event listeners
    strategyFilter.addEventListener('change', applyFilters);
    statusFilter.addEventListener('change', applyFilters);
    performanceFilter.addEventListener('change', applyFilters);
    searchBox.addEventListener('input', applyFilters);
    resetBtn.addEventListener('click', resetFilters);

    // Initial count
    resultCount.textContent = `Showing ${rows.length} of ${rows.length} results`;
});
</script>"""
