#!/usr/bin/env python3
"""
Generate comprehensive coverage report for Python services.
Combines coverage data from multiple services and generates a unified report.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import xml.etree.ElementTree as ET


class CoverageReporter:
    """Generate and combine coverage reports for Python services."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.services = {
            'intent-classifier': project_root / 'backend' / 'services' / 'intent-classifier',
            'prompt-generator': project_root / 'backend' / 'services' / 'prompt-generator'
        }
        self.coverage_dir = project_root / 'coverage-reports'
        self.coverage_dir.mkdir(exist_ok=True)
    
    def run_coverage_for_service(self, service_name: str, service_path: Path) -> Tuple[bool, float]:
        """Run coverage analysis for a specific service."""
        print(f"\n{'='*60}")
        print(f"Running coverage for {service_name}")
        print(f"{'='*60}")
        
        # Change to service directory
        original_dir = os.getcwd()
        os.chdir(service_path)
        
        try:
            # Activate virtual environment if it exists
            venv_path = service_path / 'venv'
            if venv_path.exists():
                activate_cmd = f"source {venv_path}/bin/activate && "
            else:
                activate_cmd = ""
            
            # Run tests with coverage
            cmd = f"{activate_cmd}pytest tests/ -v --cov=app --cov-report=xml --cov-report=html --cov-report=term"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error running tests: {result.stderr}")
                return False, 0.0
            
            # Parse coverage percentage from XML
            coverage_xml = service_path / 'coverage.xml'
            if coverage_xml.exists():
                tree = ET.parse(coverage_xml)
                root = tree.getroot()
                coverage_percent = float(root.attrib.get('line-rate', 0)) * 100
                
                # Copy coverage reports to central location
                service_coverage_dir = self.coverage_dir / service_name
                service_coverage_dir.mkdir(exist_ok=True)
                
                # Copy HTML report
                html_dir = service_path / 'htmlcov'
                if html_dir.exists():
                    subprocess.run(f"cp -r {html_dir}/* {service_coverage_dir}/", shell=True)
                
                # Copy XML report
                subprocess.run(f"cp {coverage_xml} {service_coverage_dir}/coverage.xml", shell=True)
                
                return True, coverage_percent
            else:
                print(f"Coverage XML not found for {service_name}")
                return False, 0.0
            
        finally:
            os.chdir(original_dir)
    
    def generate_summary_report(self, results: Dict[str, Tuple[bool, float]]) -> None:
        """Generate a summary HTML report combining all services."""
        summary_html = self.coverage_dir / 'index.html'
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BetterPrompts Python Services Coverage Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .service-card {{
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            background-color: #f8f9fa;
        }}
        .service-card h3 {{
            margin-top: 0;
            color: #495057;
        }}
        .coverage-bar {{
            background-color: #e9ecef;
            border-radius: 4px;
            height: 30px;
            position: relative;
            overflow: hidden;
        }}
        .coverage-fill {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.3s ease;
        }}
        .coverage-high {{ background-color: #28a745; }}
        .coverage-medium {{ background-color: #ffc107; }}
        .coverage-low {{ background-color: #dc3545; }}
        .timestamp {{
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 20px;
        }}
        .links {{
            margin-top: 10px;
        }}
        .links a {{
            color: #007bff;
            text-decoration: none;
            margin-right: 15px;
        }}
        .links a:hover {{
            text-decoration: underline;
        }}
        .overall-stats {{
            background-color: #007bff;
            color: white;
            padding: 20px;
            border-radius: 4px;
            margin: 20px 0;
            text-align: center;
        }}
        .threshold-info {{
            background-color: #e9ecef;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>BetterPrompts Python Services Coverage Report</h1>
        
        <div class="overall-stats">
            <h2>Overall Coverage: {self._calculate_overall_coverage(results):.1f}%</h2>
            <p>Target: 85% | Services: {len(results)}</p>
        </div>
        
        <div class="threshold-info">
            <strong>Coverage Thresholds:</strong>
            <span style="color: #28a745;">■ High (≥85%)</span>
            <span style="color: #ffc107;">■ Medium (70-84%)</span>
            <span style="color: #dc3545;">■ Low (<70%)</span>
        </div>
        
        <div class="summary">
"""
        
        for service_name, (success, coverage) in results.items():
            coverage_class = self._get_coverage_class(coverage)
            status = "✓ Passed" if success and coverage >= 85 else "✗ Failed"
            status_color = "#28a745" if success and coverage >= 85 else "#dc3545"
            
            html_content += f"""
            <div class="service-card">
                <h3>{service_name.replace('-', ' ').title()}</h3>
                <p>Status: <span style="color: {status_color}; font-weight: bold;">{status}</span></p>
                <div class="coverage-bar">
                    <div class="coverage-fill {coverage_class}" style="width: {coverage}%;">
                        {coverage:.1f}%
                    </div>
                </div>
                <div class="links">
                    <a href="{service_name}/index.html">View Details</a>
                    <a href="{service_name}/coverage.xml">XML Report</a>
                </div>
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="timestamp">
            Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
        
        with open(summary_html, 'w') as f:
            f.write(html_content)
        
        print(f"\nSummary report generated: {summary_html}")
    
    def _calculate_overall_coverage(self, results: Dict[str, Tuple[bool, float]]) -> float:
        """Calculate the overall coverage percentage."""
        if not results:
            return 0.0
        
        total_coverage = sum(coverage for _, (_, coverage) in results.items())
        return total_coverage / len(results)
    
    def _get_coverage_class(self, coverage: float) -> str:
        """Get CSS class based on coverage percentage."""
        if coverage >= 85:
            return "coverage-high"
        elif coverage >= 70:
            return "coverage-medium"
        else:
            return "coverage-low"
    
    def run(self) -> None:
        """Run coverage analysis for all services."""
        results = {}
        
        for service_name, service_path in self.services.items():
            if service_path.exists():
                success, coverage = self.run_coverage_for_service(service_name, service_path)
                results[service_name] = (success, coverage)
                
                print(f"\n{service_name}: {'PASS' if success else 'FAIL'} - {coverage:.1f}% coverage")
            else:
                print(f"\nService path not found: {service_path}")
                results[service_name] = (False, 0.0)
        
        # Generate summary report
        self.generate_summary_report(results)
        
        # Print summary
        print("\n" + "="*60)
        print("COVERAGE SUMMARY")
        print("="*60)
        
        overall_coverage = self._calculate_overall_coverage(results)
        print(f"Overall Coverage: {overall_coverage:.1f}%")
        print(f"Target: 85%")
        print(f"Status: {'PASS' if overall_coverage >= 85 else 'FAIL'}")
        
        print("\nService Breakdown:")
        for service_name, (success, coverage) in results.items():
            status = "✓" if success and coverage >= 85 else "✗"
            print(f"  {status} {service_name}: {coverage:.1f}%")
        
        # Exit with error if coverage is below threshold
        if overall_coverage < 85:
            sys.exit(1)


def main():
    """Main entry point."""
    # Determine project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Create and run reporter
    reporter = CoverageReporter(project_root)
    reporter.run()


if __name__ == "__main__":
    main()