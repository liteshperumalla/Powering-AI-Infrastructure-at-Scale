#!/usr/bin/env python3
"""
Comprehensive Test Runner for Task 8: Production Frontend Integration

This script runs all frontend integration tests and provides a comprehensive
report on the implementation status of:
- Real backend API integration (Task 8.1)
- User authentication implementation (Task 8.2) 
- Real-time features (Task 8.3)
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import json

# Import test modules
from test_frontend_integration import FrontendIntegrationTester
from test_websocket_integration import WebSocketIntegrationTester
from test_authentication_system import AuthenticationSystemTester

class ComprehensiveFrontendTestRunner:
    """Comprehensive test runner for all frontend integration tests."""
    
    def __init__(self):
        self.start_time = time.time()
        self.all_results = {}
        
    def print_header(self):
        """Print test suite header."""
        print("🚀" + "=" * 78 + "🚀")
        print("🎯 COMPREHENSIVE FRONTEND INTEGRATION TEST SUITE")
        print("📋 Task 8: Production Frontend Integration")
        print("=" * 80)
        print("📅 Testing Implementation of:")
        print("   ✅ Task 8.1: Connect React dashboard to real backend APIs")
        print("   ✅ Task 8.2: Implement real user authentication in frontend")
        print("   ✅ Task 8.3: Add real-time features to frontend")
        print("=" * 80)
    
    def check_prerequisites(self) -> bool:
        """Check if all required files and dependencies are present."""
        print("\n🔍 Checking Prerequisites...")
        
        required_files = [
            "frontend-react/src/services/api.ts",
            "frontend-react/src/store/slices/authSlice.ts",
            "frontend-react/src/hooks/useWebSocket.ts",
            "frontend-react/src/components/ProtectedRoute.tsx",
            "frontend-react/src/components/UserProfile.tsx",
            "frontend-react/src/components/RealTimeProgress.tsx",
            "frontend-react/src/components/RealTimeDashboard.tsx",
            "frontend-react/next.config.ts",
            "frontend-react/Dockerfile"
        ]
        
        missing_files = []
        project_root = Path(__file__).parent
        
        for file_path in required_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            print("❌ Missing required files:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        print("✅ All required files present")
        return True
    
    async def run_all_test_suites(self) -> Dict[str, Any]:
        """Run all test suites."""
        print("\n🧪 Running Test Suites...")
        
        results = {}
        
        # Test Suite 1: Frontend Integration
        print("\n" + "🔧" * 60)
        print("TEST SUITE 1: FRONTEND INTEGRATION")
        print("🔧" * 60)
        
        integration_tester = FrontendIntegrationTester()
        results["frontend_integration"] = integration_tester.run_all_tests()
        
        # Test Suite 2: Authentication System
        print("\n" + "🔐" * 60)
        print("TEST SUITE 2: AUTHENTICATION SYSTEM")
        print("🔐" * 60)
        
        auth_tester = AuthenticationSystemTester()
        results["authentication"] = auth_tester.run_all_tests()
        
        # Test Suite 3: WebSocket Integration
        print("\n" + "⚡" * 60)
        print("TEST SUITE 3: WEBSOCKET INTEGRATION")
        print("⚡" * 60)
        
        websocket_tester = WebSocketIntegrationTester()
        results["websocket"] = await websocket_tester.run_all_tests()
        
        return results
    
    def generate_comprehensive_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        print("\n" + "📊" * 60)
        print("COMPREHENSIVE TEST REPORT")
        print("📊" * 60)
        
        # Calculate overall statistics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        suite_results = {}
        
        for suite_name, suite_result in results.items():
            suite_summary = suite_result["summary"]
            total_tests += suite_summary["total"]
            total_passed += suite_summary["passed"]
            total_failed += suite_summary["failed"]
            
            suite_results[suite_name] = {
                "success": suite_result["overall_success"],
                "tests": suite_summary["total"],
                "passed": suite_summary["passed"],
                "failed": suite_summary["failed"],
                "success_rate": suite_summary["success_rate"]
            }
        
        overall_success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        overall_success = all(result["overall_success"] for result in results.values())
        
        # Print summary table
        print(f"{'Test Suite':<25} {'Tests':<8} {'Passed':<8} {'Failed':<8} {'Rate':<8} {'Status':<10}")
        print("-" * 75)
        
        for suite_name, suite_data in suite_results.items():
            status = "✅ PASS" if suite_data["success"] else "❌ FAIL"
            print(f"{suite_name.replace('_', ' ').title():<25} "
                  f"{suite_data['tests']:<8} "
                  f"{suite_data['passed']:<8} "
                  f"{suite_data['failed']:<8} "
                  f"{suite_data['success_rate']:.1f}%{'':<3} "
                  f"{status:<10}")
        
        print("-" * 75)
        print(f"{'TOTAL':<25} {total_tests:<8} {total_passed:<8} {total_failed:<8} {overall_success_rate:.1f}%{'':<3} {'✅ PASS' if overall_success else '❌ FAIL':<10}")
        
        # Task completion status
        print("\n🎯 TASK COMPLETION STATUS:")
        print("=" * 40)
        
        task_status = {
            "8.1": results["frontend_integration"]["test_results"]["api_service"],
            "8.2": results["authentication"]["overall_success"],
            "8.3": results["websocket"]["overall_success"]
        }
        
        for task, status in task_status.items():
            status_icon = "✅" if status else "❌"
            task_name = {
                "8.1": "Real Backend API Integration",
                "8.2": "User Authentication Implementation", 
                "8.3": "Real-time Features Implementation"
            }[task]
            print(f"{status_icon} Task {task}: {task_name}")
        
        # Overall assessment
        print(f"\n🏆 OVERALL ASSESSMENT: {'✅ SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")
        
        if overall_success:
            print("\n🎉 CONGRATULATIONS!")
            print("All frontend integration tasks have been successfully implemented!")
            print("\n✨ Key Achievements:")
            print("   🔗 Real backend API integration with error handling")
            print("   🔐 Complete JWT authentication system")
            print("   ⚡ Real-time WebSocket features")
            print("   🛡️ Protected routes and role-based access")
            print("   👤 User profile management")
            print("   📱 Production-ready configuration")
            print("   🚀 Optimized build and deployment setup")
        else:
            print("\n⚠️  Some areas need attention:")
            failed_suites = [name for name, result in results.items() if not result["overall_success"]]
            for suite in failed_suites:
                print(f"   - {suite.replace('_', ' ').title()}")
            print("\nPlease review the detailed test results above.")
        
        # Performance metrics
        execution_time = time.time() - self.start_time
        print(f"\n⏱️  Test Execution Time: {execution_time:.2f} seconds")
        print(f"📈 Test Coverage: {total_tests} tests across 3 major areas")
        
        return {
            "overall_success": overall_success,
            "overall_success_rate": overall_success_rate,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "execution_time": execution_time,
            "task_completion": task_status,
            "suite_results": suite_results,
            "detailed_results": results
        }
    
    def save_test_report(self, report: Dict[str, Any]):
        """Save test report to file."""
        try:
            report_file = Path(__file__).parent / "frontend_integration_test_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 Test report saved to: {report_file}")
        except Exception as e:
            print(f"\n⚠️  Could not save test report: {e}")
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive frontend integration tests."""
        self.print_header()
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Prerequisites not met. Please ensure all required files are present.")
            return {"overall_success": False, "error": "Prerequisites not met"}
        
        # Run all test suites
        try:
            results = await self.run_all_test_suites()
            self.all_results = results
            
            # Generate comprehensive report
            report = self.generate_comprehensive_report(results)
            
            # Save report
            self.save_test_report(report)
            
            return report
            
        except Exception as e:
            print(f"\n❌ Error during test execution: {e}")
            return {"overall_success": False, "error": str(e)}


async def main():
    """Main test execution function."""
    runner = ComprehensiveFrontendTestRunner()
    report = await runner.run_comprehensive_tests()
    
    # Exit with appropriate code
    sys.exit(0 if report.get("overall_success", False) else 1)


if __name__ == "__main__":
    asyncio.run(main())