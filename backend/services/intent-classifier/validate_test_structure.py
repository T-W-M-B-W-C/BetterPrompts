#!/usr/bin/env python3
"""
Validate ML integration test structure and configuration.
This script checks test files without executing them.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


class TestStructureValidator:
    """Validates test structure and configuration."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.test_path = self.base_path / "tests"
        self.issues = []
        self.stats = {
            "total_files": 0,
            "test_files": 0,
            "test_functions": 0,
            "markers": {},
            "async_tests": 0,
            "fixtures": 0
        }
    
    def validate_all(self) -> Tuple[bool, Dict]:
        """Run all validation checks."""
        print("🔍 Validating ML Integration Test Structure")
        print("=" * 60)
        
        # Check test directory structure
        self._check_directory_structure()
        
        # Analyze test files
        self._analyze_test_files()
        
        # Check configuration files
        self._check_config_files()
        
        # Generate report
        self._generate_report()
        
        return len(self.issues) == 0, self.stats
    
    def _check_directory_structure(self):
        """Check if test directory structure is correct."""
        print("\n📁 Checking directory structure...")
        
        required_paths = [
            self.test_path,
            self.test_path / "__init__.py",
            self.test_path / "conftest.py"
        ]
        
        for path in required_paths:
            if path.exists():
                print(f"  ✅ {path.relative_to(self.base_path)}")
            else:
                self.issues.append(f"Missing: {path.relative_to(self.base_path)}")
                print(f"  ❌ {path.relative_to(self.base_path)} - MISSING")
    
    def _analyze_test_files(self):
        """Analyze all test files."""
        print("\n📝 Analyzing test files...")
        
        test_files = list(self.test_path.glob("test_*.py"))
        self.stats["test_files"] = len(test_files)
        
        for test_file in test_files:
            print(f"\n  📄 {test_file.name}")
            self._analyze_single_test_file(test_file)
    
    def _analyze_single_test_file(self, file_path: Path):
        """Analyze a single test file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Count test functions
            test_funcs = re.findall(r'def (test_\w+)', content)
            async_tests = re.findall(r'async def (test_\w+)', content)
            
            self.stats["test_functions"] += len(test_funcs)
            self.stats["async_tests"] += len(async_tests)
            
            # Find markers
            markers = re.findall(r'@pytest\.mark\.(\w+)', content)
            for marker in markers:
                self.stats["markers"][marker] = self.stats["markers"].get(marker, 0) + 1
            
            # Find fixtures
            fixtures = re.findall(r'@pytest\.fixture', content)
            self.stats["fixtures"] += len(fixtures)
            
            print(f"    Tests: {len(test_funcs)} ({len(async_tests)} async)")
            print(f"    Markers: {', '.join(set(markers)) if markers else 'none'}")
            
        except Exception as e:
            self.issues.append(f"Error reading {file_path}: {e}")
    
    def _check_config_files(self):
        """Check configuration files."""
        print("\n⚙️  Checking configuration files...")
        
        config_files = {
            "pytest.ini": self.base_path / "pytest.ini",
            "requirements.txt": self.base_path / "requirements.txt",
            ".env.example": self.base_path / ".env.example"
        }
        
        for name, path in config_files.items():
            if path.exists():
                print(f"  ✅ {name}")
                if name == "pytest.ini":
                    self._validate_pytest_config(path)
            else:
                print(f"  ❌ {name} - MISSING")
                self.issues.append(f"Missing config: {name}")
    
    def _validate_pytest_config(self, config_path: Path):
        """Validate pytest configuration."""
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check for important settings
        important_settings = [
            "testpaths",
            "python_files",
            "asyncio_mode",
            "markers",
            "--cov"
        ]
        
        for setting in important_settings:
            if setting in content:
                print(f"    ✓ {setting} configured")
            else:
                print(f"    ⚠️  {setting} not configured")
    
    def _generate_report(self):
        """Generate validation report."""
        print("\n" + "=" * 60)
        print("📊 Test Structure Validation Report")
        print("=" * 60)
        
        print(f"\nTest Files: {self.stats['test_files']}")
        print(f"Test Functions: {self.stats['test_functions']}")
        print(f"Async Tests: {self.stats['async_tests']}")
        print(f"Test Fixtures: {self.stats['fixtures']}")
        
        print("\nTest Markers Used:")
        for marker, count in sorted(self.stats["markers"].items()):
            print(f"  - {marker}: {count} times")
        
        if self.issues:
            print(f"\n⚠️  Issues Found ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  - {issue}")
        else:
            print("\n✅ No structural issues found!")
        
        # Test coverage estimation
        print("\n📈 Test Coverage Estimation:")
        files_to_test = [
            "classifier.py",
            "torchserve_client.py",
            "api/v1/intents.py",
            "api/v1/health.py"
        ]
        
        covered_files = []
        for test_file in ["test_classifier.py", "test_torchserve_client.py", "test_api.py"]:
            if (self.test_path / test_file).exists():
                covered_files.append(test_file.replace("test_", "").replace(".py", ""))
        
        coverage_estimate = (len(covered_files) / len(files_to_test)) * 100
        print(f"  Estimated file coverage: {coverage_estimate:.0f}%")
        print(f"  Files with tests: {', '.join(covered_files)}")


def main():
    """Run validation."""
    validator = TestStructureValidator()
    success, stats = validator.validate_all()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ML Integration Test Structure Valid!")
        print("\nNext Steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run unit tests: pytest -m unit -v")
        print("3. Run all tests: pytest -v --cov=app")
    else:
        print("❌ Test Structure Has Issues - Please Fix Above")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())