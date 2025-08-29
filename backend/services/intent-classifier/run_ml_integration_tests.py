#!/usr/bin/env python3
"""
Comprehensive ML Integration Test Suite
Validates the complete ML pipeline including TorchServe integration
"""

import asyncio
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple
import httpx
from datetime import datetime

# Test configuration
TEST_CONFIG = {
    "unit_tests": {
        "markers": "unit and not torchserve",
        "description": "Unit tests without external dependencies",
        "required": True
    },
    "integration_tests": {
        "markers": "integration",
        "description": "Integration tests with mocked services",
        "required": True
    },
    "torchserve_tests": {
        "markers": "torchserve",
        "description": "Tests requiring TorchServe connection",
        "required": False  # May not have TorchServe running
    },
    "e2e_tests": {
        "markers": "e2e",
        "description": "End-to-end tests with all services",
        "required": False
    }
}

# Test validation criteria
VALIDATION_CRITERIA = {
    "min_coverage": 80,
    "max_test_duration": 300,  # 5 minutes
    "critical_tests_must_pass": True,
    "error_threshold": 0.05  # 5% error rate allowed
}


class MLIntegrationTestRunner:
    """Orchestrates ML integration testing with comprehensive validation."""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.start_time = datetime.now()
        self.test_dir = Path(__file__).parent
        
    async def check_services_health(self) -> Dict[str, bool]:
        """Check health of required services."""
        print("\n🔍 Checking service health...")
        
        services = {
            "intent-classifier": "http://localhost:8001/health",
            "torchserve": "http://localhost:8080/ping",
            "redis": None,  # Will use redis-cli
            "postgres": None  # Will use psql
        }
        
        health_status = {}
        
        # Check HTTP services
        async with httpx.AsyncClient(timeout=5.0) as client:
            for service, url in services.items():
                if url:
                    try:
                        response = await client.get(url)
                        health_status[service] = response.status_code == 200
                        print(f"  ✅ {service}: Healthy" if health_status[service] else f"  ❌ {service}: Unhealthy")
                    except Exception as e:
                        health_status[service] = False
                        print(f"  ❌ {service}: Not reachable - {e}")
        
        # Check Redis
        try:
            result = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True)
            health_status["redis"] = result.stdout.strip() == "PONG"
            print(f"  ✅ Redis: Healthy" if health_status["redis"] else "  ❌ Redis: Unhealthy")
        except:
            health_status["redis"] = False
            print("  ❌ Redis: Not reachable")
            
        # Check PostgreSQL
        try:
            result = subprocess.run(
                ["psql", "-h", "localhost", "-U", "betterprompts", "-d", "betterprompts", "-c", "SELECT 1"],
                capture_output=True,
                text=True,
                env={"PGPASSWORD": "changeme"}
            )
            health_status["postgres"] = result.returncode == 0
            print(f"  ✅ PostgreSQL: Healthy" if health_status["postgres"] else "  ❌ PostgreSQL: Unhealthy")
        except:
            health_status["postgres"] = False
            print("  ❌ PostgreSQL: Not reachable")
            
        return health_status
    
    def run_test_suite(self, test_type: str, markers: str) -> Tuple[bool, Dict]:
        """Run a specific test suite and capture results."""
        print(f"\n🧪 Running {test_type}...")
        
        cmd = [
            "pytest",
            "-v",
            f"-m", markers,
            "--json-report",
            f"--json-report-file=test_results_{test_type}.json",
            "--tb=short"
        ]
        
        if test_type == "unit_tests":
            cmd.extend(["--cov=app", "--cov-report=json"])
            
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start
        
        # Parse results
        success = result.returncode == 0
        report_file = f"test_results_{test_type}.json"
        
        test_results = {
            "success": success,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "tests": {}
        }
        
        # Load detailed results if available
        if Path(report_file).exists():
            with open(report_file) as f:
                detailed_results = json.load(f)
                test_results["summary"] = detailed_results.get("summary", {})
                test_results["tests"] = detailed_results.get("tests", {})
        
        return success, test_results
    
    def validate_test_results(self) -> Dict[str, any]:
        """Validate test results against criteria."""
        print("\n🔍 Validating test results...")
        
        validation = {
            "passed": True,
            "failures": [],
            "warnings": []
        }
        
        # Check coverage
        if Path("coverage.json").exists():
            with open("coverage.json") as f:
                coverage_data = json.load(f)
                total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
                
                if total_coverage < VALIDATION_CRITERIA["min_coverage"]:
                    validation["failures"].append(
                        f"Coverage {total_coverage:.1f}% is below minimum {VALIDATION_CRITERIA['min_coverage']}%"
                    )
                    validation["passed"] = False
                else:
                    print(f"  ✅ Coverage: {total_coverage:.1f}%")
        
        # Check test duration
        total_duration = sum(r.get("duration", 0) for r in self.results.values())
        if total_duration > VALIDATION_CRITERIA["max_test_duration"]:
            validation["warnings"].append(
                f"Total test duration {total_duration:.1f}s exceeds threshold"
            )
        else:
            print(f"  ✅ Duration: {total_duration:.1f}s")
        
        # Check critical tests
        critical_failures = []
        for test_type, results in self.results.items():
            for test_name, test_data in results.get("tests", {}).items():
                if "critical" in test_data.get("keywords", []) and test_data.get("outcome") != "passed":
                    critical_failures.append(test_name)
        
        if critical_failures and VALIDATION_CRITERIA["critical_tests_must_pass"]:
            validation["failures"].extend([f"Critical test failed: {t}" for t in critical_failures])
            validation["passed"] = False
        elif not critical_failures:
            print("  ✅ All critical tests passed")
        
        # Check error rate
        total_tests = sum(len(r.get("tests", {})) for r in self.results.values())
        failed_tests = sum(
            1 for r in self.results.values() 
            for t in r.get("tests", {}).values() 
            if t.get("outcome") != "passed"
        )
        
        if total_tests > 0:
            error_rate = failed_tests / total_tests
            if error_rate > VALIDATION_CRITERIA["error_threshold"]:
                validation["failures"].append(
                    f"Error rate {error_rate:.1%} exceeds threshold {VALIDATION_CRITERIA['error_threshold']:.1%}"
                )
                validation["passed"] = False
            else:
                print(f"  ✅ Error rate: {error_rate:.1%}")
        
        return validation
    
    def generate_test_report(self, validation_results: Dict) -> str:
        """Generate comprehensive test report."""
        report = [
            "# ML Integration Test Report",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {(datetime.now() - self.start_time).total_seconds():.1f}s",
            "\n## Summary",
            f"- Overall Status: {'✅ PASSED' if validation_results['passed'] else '❌ FAILED'}"
        ]
        
        # Test results summary
        report.append("\n## Test Results")
        for test_type, results in self.results.items():
            summary = results.get("summary", {})
            report.append(f"\n### {test_type}")
            report.append(f"- Status: {'✅ Passed' if results['success'] else '❌ Failed'}")
            report.append(f"- Duration: {results['duration']:.1f}s")
            if summary:
                report.append(f"- Tests: {summary.get('total', 0)}")
                report.append(f"- Passed: {summary.get('passed', 0)}")
                report.append(f"- Failed: {summary.get('failed', 0)}")
                report.append(f"- Skipped: {summary.get('skipped', 0)}")
        
        # Coverage report
        if Path("coverage.json").exists():
            with open("coverage.json") as f:
                coverage_data = json.load(f)
                report.append("\n## Coverage Report")
                report.append(f"- Total Coverage: {coverage_data['totals']['percent_covered']:.1f}%")
                report.append(f"- Lines Covered: {coverage_data['totals']['covered_lines']}/{coverage_data['totals']['num_statements']}")
        
        # Validation results
        report.append("\n## Validation Results")
        if validation_results["failures"]:
            report.append("\n### Failures")
            for failure in validation_results["failures"]:
                report.append(f"- ❌ {failure}")
        
        if validation_results["warnings"]:
            report.append("\n### Warnings")
            for warning in validation_results["warnings"]:
                report.append(f"- ⚠️  {warning}")
        
        # Recommendations
        report.append("\n## Recommendations")
        if not validation_results["passed"]:
            report.append("- Fix failing tests before deployment")
            if any("coverage" in f for f in validation_results["failures"]):
                report.append("- Increase test coverage to meet minimum threshold")
            if any("critical" in f for f in validation_results["failures"]):
                report.append("- Prioritize fixing critical test failures")
        else:
            report.append("- ✅ All validation criteria met")
            report.append("- Consider adding more edge case tests")
            report.append("- Monitor test execution time as suite grows")
        
        return "\n".join(report)
    
    async def run(self) -> bool:
        """Execute the complete test suite."""
        print("🚀 Starting ML Integration Test Suite")
        print("=" * 60)
        
        # Check service health
        health_status = await self.check_services_health()
        
        # Determine which tests to run based on service availability
        tests_to_run = []
        for test_type, config in TEST_CONFIG.items():
            if test_type == "torchserve_tests" and not health_status.get("torchserve", False):
                print(f"\n⚠️  Skipping {test_type} - TorchServe not available")
                continue
            if test_type == "e2e_tests" and not all(health_status.values()):
                print(f"\n⚠️  Skipping {test_type} - Not all services available")
                continue
            tests_to_run.append((test_type, config))
        
        # Run selected test suites
        all_passed = True
        for test_type, config in tests_to_run:
            success, results = self.run_test_suite(test_type, config["markers"])
            self.results[test_type] = results
            
            if not success and config["required"]:
                all_passed = False
                print(f"  ❌ {test_type} failed (required)")
            elif not success:
                print(f"  ⚠️  {test_type} failed (optional)")
            else:
                print(f"  ✅ {test_type} passed")
        
        # Validate results
        validation_results = self.validate_test_results()
        
        # Generate report
        report = self.generate_test_report(validation_results)
        
        # Save report
        report_path = "ml_integration_test_report.md"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\n📄 Test report saved to: {report_path}")
        
        # Print summary
        print("\n" + "=" * 60)
        if validation_results["passed"] and all_passed:
            print("✅ ML Integration Tests PASSED")
            return True
        else:
            print("❌ ML Integration Tests FAILED")
            if validation_results["failures"]:
                print("\nFailures:")
                for failure in validation_results["failures"]:
                    print(f"  - {failure}")
            return False


async def main():
    """Main entry point."""
    runner = MLIntegrationTestRunner()
    success = await runner.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())