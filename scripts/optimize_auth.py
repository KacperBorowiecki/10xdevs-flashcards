#!/usr/bin/env python3
"""
Auth view optimization and performance analysis script.
Analyzes code quality, performance metrics, and provides optimization suggestions.
"""

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List


class AuthOptimizer:
    """Analyzes and optimizes auth view implementation."""

    def __init__(self):
        self.base_path = Path.cwd()
        self.results = {
            "analysis_timestamp": time.time(),
            "file_sizes": {},
            "code_metrics": {},
            "optimization_suggestions": [],
            "performance_issues": [],
            "security_checks": [],
        }

    def analyze_file_sizes(self):
        """Analyze file sizes for optimization opportunities."""
        print("📊 Analyzing file sizes...")

        files_to_check = [
            "templates/auth.html",
            "static/css/auth.css",
            "static/js/auth.js",
            "static/js/auth-test-scenarios.js",
            "src/api/v1/routers/auth_views.py",
            "src/services/auth_service.py",
            "src/core/exceptions.py",
        ]

        for file_path in files_to_check:
            full_path = self.base_path / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                self.results["file_sizes"][file_path] = {
                    "bytes": size,
                    "kb": round(size / 1024, 2),
                }

                # Flag large files
                if size > 50000:  # 50KB
                    self.results["optimization_suggestions"].append(
                        {
                            "type": "file_size",
                            "file": file_path,
                            "issue": f"Large file ({round(size/1024, 2)}KB)",
                            "suggestion": "Consider code splitting or minification",
                        }
                    )

    def analyze_javascript_complexity(self):
        """Analyze JavaScript code complexity and performance."""
        print("🔍 Analyzing JavaScript complexity...")

        js_file = self.base_path / "static/js/auth.js"
        if not js_file.exists():
            return

        content = js_file.read_text()

        # Count functions
        function_count = len(
            re.findall(
                r"function\s+\w+|^\s*\w+\s*\(.*\)\s*{|\w+:\s*function",
                content,
                re.MULTILINE,
            )
        )

        # Count event listeners
        event_listeners = len(re.findall(r"addEventListener\s*\(", content))

        # Count DOM queries
        dom_queries = len(
            re.findall(
                r"document\.(getElementById|querySelector|querySelectorAll)", content
            )
        )

        # Check for potential memory leaks
        timeout_calls = len(re.findall(r"setTimeout|setInterval", content))

        self.results["code_metrics"]["javascript"] = {
            "functions": function_count,
            "event_listeners": event_listeners,
            "dom_queries": dom_queries,
            "timeout_calls": timeout_calls,
            "lines": len(content.split("\n")),
        }

        # Performance suggestions
        if dom_queries > 20:
            self.results["performance_issues"].append(
                {
                    "type": "dom_queries",
                    "count": dom_queries,
                    "suggestion": "Consider caching DOM element references",
                }
            )

        if event_listeners > 10:
            self.results["performance_issues"].append(
                {
                    "type": "event_listeners",
                    "count": event_listeners,
                    "suggestion": "Consider event delegation for better performance",
                }
            )

    def analyze_css_optimization(self):
        """Analyze CSS for optimization opportunities."""
        print("🎨 Analyzing CSS optimization...")

        css_file = self.base_path / "static/css/auth.css"
        if not css_file.exists():
            return

        content = css_file.read_text()

        # Count selectors
        selectors = len(re.findall(r"[.#]?[\w-]+\s*{", content))

        # Count media queries
        media_queries = len(re.findall(r"@media", content))

        # Check for unused vendor prefixes (example)
        vendor_prefixes = len(re.findall(r"-webkit-|-moz-|-ms-|-o-", content))

        # Count animations
        animations = len(re.findall(r"@keyframes|animation:", content))

        self.results["code_metrics"]["css"] = {
            "selectors": selectors,
            "media_queries": media_queries,
            "vendor_prefixes": vendor_prefixes,
            "animations": animations,
            "lines": len(content.split("\n")),
        }

        # Optimization suggestions
        if vendor_prefixes > 10:
            self.results["optimization_suggestions"].append(
                {
                    "type": "css_optimization",
                    "issue": f"Many vendor prefixes ({vendor_prefixes})",
                    "suggestion": "Consider using autoprefixer for better maintenance",
                }
            )

    def analyze_python_code_quality(self):
        """Analyze Python code quality and complexity."""
        print("🐍 Analyzing Python code quality...")

        python_files = [
            "src/api/v1/routers/auth_views.py",
            "src/services/auth_service.py",
            "src/core/exceptions.py",
        ]

        for file_path in python_files:
            full_path = self.base_path / file_path
            if not full_path.exists():
                continue

            content = full_path.read_text()

            # Count functions/methods
            functions = len(re.findall(r"def \w+\(", content))

            # Count classes
            classes = len(re.findall(r"class \w+", content))

            # Count imports
            imports = len(re.findall(r"^(import|from)", content, re.MULTILINE))

            # Check for long lines
            lines = content.split("\n")
            long_lines = sum(1 for line in lines if len(line) > 120)

            self.results["code_metrics"][file_path] = {
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "long_lines": long_lines,
                "total_lines": len(lines),
            }

            if long_lines > 5:
                self.results["optimization_suggestions"].append(
                    {
                        "type": "code_style",
                        "file": file_path,
                        "issue": f"{long_lines} lines over 120 characters",
                        "suggestion": "Consider breaking long lines for better readability",
                    }
                )

    def security_analysis(self):
        """Perform basic security analysis."""
        print("🔒 Performing security analysis...")

        # Check auth.html for security features
        html_file = self.base_path / "templates/auth.html"
        if html_file.exists():
            content = html_file.read_text()

            security_features = {
                "csrf_token": "csrf" in content.lower(),
                "autocomplete_off": 'autocomplete="off"' in content,
                "secure_headers": "X-Frame-Options" in content
                or "X-Content-Type-Options" in content,
                "password_autocomplete": 'autocomplete="current-password"' in content,
                "form_validation": "required" in content,
            }

            self.results["security_checks"] = security_features

            # Security suggestions
            if not security_features["csrf_token"]:
                self.results["optimization_suggestions"].append(
                    {
                        "type": "security",
                        "issue": "CSRF protection not detected",
                        "suggestion": "Implement CSRF token for form protection",
                    }
                )

    def check_accessibility_compliance(self):
        """Check accessibility compliance."""
        print("♿ Checking accessibility compliance...")

        html_file = self.base_path / "templates/auth.html"
        if not html_file.exists():
            return

        content = html_file.read_text()

        accessibility_features = {
            "aria_labels": len(re.findall(r"aria-label=", content)),
            "aria_describedby": len(re.findall(r"aria-describedby=", content)),
            "labels_for": len(re.findall(r"<label[^>]+for=", content)),
            "alt_attributes": len(re.findall(r"alt=", content)),
            "semantic_html": len(
                re.findall(r"<(main|section|article|header|nav|aside|footer)", content)
            ),
        }

        self.results["code_metrics"]["accessibility"] = accessibility_features

        # Accessibility suggestions
        if accessibility_features["aria_labels"] == 0:
            self.results["optimization_suggestions"].append(
                {
                    "type": "accessibility",
                    "issue": "No ARIA labels found",
                    "suggestion": "Add ARIA labels for better screen reader support",
                }
            )

    def generate_performance_report(self):
        """Generate comprehensive performance report."""
        print("📋 Generating performance report...")

        # Calculate overall score
        total_files = len(self.results["file_sizes"])
        performance_issues = len(self.results["performance_issues"])
        optimization_suggestions = len(self.results["optimization_suggestions"])

        # Simple scoring system
        score = max(0, 100 - (performance_issues * 10) - (optimization_suggestions * 5))

        self.results["overall_score"] = score
        self.results["grade"] = (
            "A"
            if score >= 90
            else (
                "B"
                if score >= 80
                else "C" if score >= 70 else "D" if score >= 60 else "F"
            )
        )

    def save_report(self):
        """Save analysis report to file."""
        report_file = self.base_path / "auth_optimization_report.json"

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"📄 Report saved to: {report_file}")

    def print_summary(self):
        """Print optimization summary."""
        print("\n" + "=" * 60)
        print("🚀 AUTH VIEW OPTIMIZATION SUMMARY")
        print("=" * 60)

        print(
            f"\n📊 Overall Score: {self.results['overall_score']}/100 (Grade: {self.results['grade']})"
        )

        print(f"\n📁 File Analysis:")
        for file_path, data in self.results["file_sizes"].items():
            print(f"  • {file_path}: {data['kb']}KB")

        if self.results["performance_issues"]:
            print(
                f"\n⚠️  Performance Issues ({len(self.results['performance_issues'])}):"
            )
            for issue in self.results["performance_issues"]:
                print(f"  • {issue['type']}: {issue['suggestion']}")

        if self.results["optimization_suggestions"]:
            print(
                f"\n💡 Optimization Suggestions ({len(self.results['optimization_suggestions'])}):"
            )
            for suggestion in self.results["optimization_suggestions"][
                :5
            ]:  # Show top 5
                print(f"  • {suggestion['type']}: {suggestion['suggestion']}")

        print(f"\n🔒 Security Features:")
        for feature, status in self.results.get("security_checks", {}).items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {feature.replace('_', ' ').title()}")

        print(f"\n♿ Accessibility Score:")
        acc_features = self.results["code_metrics"].get("accessibility", {})
        acc_score = sum(1 for v in acc_features.values() if v > 0)
        print(f"  Score: {acc_score}/{len(acc_features)} features implemented")

        print("\n" + "=" * 60)

    def run_optimization(self):
        """Run complete optimization analysis."""
        print("🔧 Starting Auth View Optimization Analysis...\n")

        self.analyze_file_sizes()
        self.analyze_javascript_complexity()
        self.analyze_css_optimization()
        self.analyze_python_code_quality()
        self.security_analysis()
        self.check_accessibility_compliance()
        self.generate_performance_report()

        self.print_summary()
        self.save_report()

        print("\n✨ Optimization analysis complete!")


def main():
    """Main entry point."""
    optimizer = AuthOptimizer()
    optimizer.run_optimization()


if __name__ == "__main__":
    main()
