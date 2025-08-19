#!/usr/bin/env python3
"""
Frontend Code Audit - Check for Mock Data and Integration Issues

This script analyzes the frontend codebase to:
- Find mock data usage
- Check API integration patterns
- Verify real data usage
- Identify potential UI bugs
- Check component implementations

Run with: python frontend_code_audit.py
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Set
from pathlib import Path

class FrontendCodeAuditor:
    def __init__(self):
        self.frontend_path = Path("frontend-react/src")
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "mock_data_analysis": {},
            "api_integration": {},
            "component_analysis": {},
            "potential_issues": [],
            "recommendations": []
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def find_mock_data_usage(self):
        """Find mock data usage in frontend code."""
        self.log("🔍 Analyzing frontend code for mock data usage...")
        
        mock_patterns = [
            r'mock\w*\s*[:=]',  # mock variables
            r'demo\w*\s*[:=]',  # demo variables
            r'sample\w*\s*[:=]',  # sample data
            r'test\w*\s*[:=]',  # test data
            r'dummy\w*\s*[:=]',  # dummy data
            r'fake\w*\s*[:=]',  # fake data
            r'placeholder\w*\s*[:=]',  # placeholder data
            r'const\s+\w*mock\w*\s*=',  # const mockData =
            r'const\s+\w*demo\w*\s*=',  # const demoData =
            r'fallback\w*\s*[:=]',  # fallback data
            r'defaultData\s*[:=]',  # default data
        ]
        
        mock_data_files = {}
        total_mock_instances = 0
        
        for file_path in self.frontend_path.rglob("*.ts"):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    file_mocks = []
                    for pattern in mock_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line_num - 1].strip()
                            file_mocks.append({
                                "pattern": pattern,
                                "line": line_num,
                                "content": line_content[:100] + "..." if len(line_content) > 100 else line_content
                            })
                    
                    if file_mocks:
                        relative_path = str(file_path.relative_to(self.frontend_path))
                        mock_data_files[relative_path] = file_mocks
                        total_mock_instances += len(file_mocks)
                        
                except Exception as e:
                    self.log(f"Error reading {file_path}: {e}", "WARNING")
        
        # Also check .tsx files
        for file_path in self.frontend_path.rglob("*.tsx"):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    file_mocks = []
                    for pattern in mock_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line_num - 1].strip()
                            file_mocks.append({
                                "pattern": pattern,
                                "line": line_num,
                                "content": line_content[:100] + "..." if len(line_content) > 100 else line_content
                            })
                    
                    if file_mocks:
                        relative_path = str(file_path.relative_to(self.frontend_path))
                        if relative_path in mock_data_files:
                            mock_data_files[relative_path].extend(file_mocks)
                        else:
                            mock_data_files[relative_path] = file_mocks
                        total_mock_instances += len(file_mocks)
                        
                except Exception as e:
                    self.log(f"Error reading {file_path}: {e}", "WARNING")
        
        self.audit_results["mock_data_analysis"] = {
            "total_files_with_mocks": len(mock_data_files),
            "total_mock_instances": total_mock_instances,
            "files": mock_data_files
        }
        
        if total_mock_instances > 0:
            self.log(f"⚠️  Found {total_mock_instances} mock data instances in {len(mock_data_files)} files")
        else:
            self.log("✅ No obvious mock data patterns found")
        
        return mock_data_files

    def analyze_api_integration(self):
        """Analyze API integration patterns."""
        self.log("🔗 Analyzing API integration patterns...")
        
        api_patterns = {
            "api_calls": [
                r'fetch\s*\(',  # fetch calls
                r'axios\.',  # axios calls
                r'\.request\s*\(',  # request method calls
                r'\.get\s*\(',  # GET requests
                r'\.post\s*\(',  # POST requests
                r'\.put\s*\(',  # PUT requests
                r'\.delete\s*\(',  # DELETE requests
            ],
            "api_endpoints": [
                r'["\']\/api\/[^"\']*["\']',  # API endpoint strings
                r'API_BASE_URL',  # API base URL usage
                r'FRONTEND_URL',  # Frontend URL usage
            ],
            "error_handling": [
                r'catch\s*\(',  # catch blocks
                r'\.catch\s*\(',  # promise catch
                r'try\s*{',  # try blocks
                r'throw\s+',  # throw statements
            ]
        }
        
        api_analysis = {}
        
        for category, patterns in api_patterns.items():
            category_results = {}
            total_instances = 0
            
            for file_path in self.frontend_path.rglob("*.ts"):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        file_instances = []
                        for pattern in patterns:
                            matches = list(re.finditer(pattern, content, re.IGNORECASE))
                            file_instances.extend(matches)
                        
                        if file_instances:
                            relative_path = str(file_path.relative_to(self.frontend_path))
                            category_results[relative_path] = len(file_instances)
                            total_instances += len(file_instances)
                            
                    except Exception as e:
                        continue
            
            # Also check .tsx files
            for file_path in self.frontend_path.rglob("*.tsx"):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        file_instances = []
                        for pattern in patterns:
                            matches = list(re.finditer(pattern, content, re.IGNORECASE))
                            file_instances.extend(matches)
                        
                        if file_instances:
                            relative_path = str(file_path.relative_to(self.frontend_path))
                            if relative_path in category_results:
                                category_results[relative_path] += len(file_instances)
                            else:
                                category_results[relative_path] = len(file_instances)
                            total_instances += len(file_instances)
                            
                    except Exception as e:
                        continue
            
            api_analysis[category] = {
                "total_instances": total_instances,
                "files": category_results
            }
        
        self.audit_results["api_integration"] = api_analysis
        
        self.log(f"✅ API Integration Analysis:")
        for category, data in api_analysis.items():
            self.log(f"  - {category}: {data['total_instances']} instances in {len(data['files'])} files")
        
        return api_analysis

    def analyze_components(self):
        """Analyze React components for potential issues."""
        self.log("⚛️  Analyzing React components...")
        
        component_issues = []
        component_stats = {
            "total_components": 0,
            "components_with_state": 0,
            "components_with_effects": 0,
            "components_with_api_calls": 0
        }
        
        component_patterns = {
            "state_usage": [r'useState\s*\(', r'this\.state'],
            "effect_usage": [r'useEffect\s*\(', r'componentDidMount', r'componentDidUpdate'],
            "api_usage": [r'fetch\s*\(', r'axios\.', r'\.request\s*\('],
            "error_boundaries": [r'componentDidCatch', r'getDerivedStateFromError']
        }
        
        for file_path in self.frontend_path.rglob("*.tsx"):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if it's a React component
                    if ('export default' in content or 'export const' in content) and 'React' in content:
                        component_stats["total_components"] += 1
                        relative_path = str(file_path.relative_to(self.frontend_path))
                        
                        # Check for various patterns
                        component_analysis = {"file": relative_path}
                        
                        for pattern_type, patterns in component_patterns.items():
                            found = False
                            for pattern in patterns:
                                if re.search(pattern, content):
                                    found = True
                                    break
                            component_analysis[pattern_type] = found
                            
                            if pattern_type == "state_usage" and found:
                                component_stats["components_with_state"] += 1
                            elif pattern_type == "effect_usage" and found:
                                component_stats["components_with_effects"] += 1
                            elif pattern_type == "api_usage" and found:
                                component_stats["components_with_api_calls"] += 1
                        
                        # Check for potential issues
                        issues = []
                        
                        # Check for missing error handling in API calls
                        if component_analysis["api_usage"] and not re.search(r'catch\s*\(|\.catch', content):
                            issues.append("API calls without error handling")
                        
                        # Check for hardcoded URLs
                        if re.search(r'["\']https?://[^"\']*["\']', content):
                            issues.append("Hardcoded URLs found")
                        
                        # Check for console.log statements
                        if re.search(r'console\.log\s*\(', content):
                            issues.append("Console.log statements found")
                        
                        if issues:
                            component_analysis["issues"] = issues
                            component_issues.append(component_analysis)
                        
                except Exception as e:
                    self.log(f"Error analyzing component {file_path}: {e}", "WARNING")
        
        self.audit_results["component_analysis"] = {
            "stats": component_stats,
            "components_with_issues": component_issues
        }
        
        self.log(f"✅ Component Analysis:")
        self.log(f"  - Total components: {component_stats['total_components']}")
        self.log(f"  - With state: {component_stats['components_with_state']}")
        self.log(f"  - With effects: {component_stats['components_with_effects']}")
        self.log(f"  - With API calls: {component_stats['components_with_api_calls']}")
        self.log(f"  - Components with issues: {len(component_issues)}")
        
        return component_stats, component_issues

    def check_package_dependencies(self):
        """Check package.json for dependencies and potential issues."""
        self.log("📦 Checking package dependencies...")
        
        package_json_path = Path("frontend-react/package.json")
        
        if not package_json_path.exists():
            self.log("❌ package.json not found", "ERROR")
            return {}
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            dependencies = package_data.get("dependencies", {})
            dev_dependencies = package_data.get("devDependencies", {})
            
            # Check for testing libraries
            testing_libs = [lib for lib in dependencies.keys() if 'test' in lib.lower() or 'mock' in lib.lower()]
            testing_libs.extend([lib for lib in dev_dependencies.keys() if 'test' in lib.lower() or 'mock' in lib.lower()])
            
            # Check for API/HTTP libraries
            api_libs = [lib for lib in dependencies.keys() if lib in ['axios', 'fetch', 'superagent', 'node-fetch']]
            
            dependency_analysis = {
                "total_dependencies": len(dependencies),
                "total_dev_dependencies": len(dev_dependencies),
                "testing_libraries": testing_libs,
                "api_libraries": api_libs,
                "has_typescript": "typescript" in dev_dependencies or "@types/node" in dependencies,
                "has_react": "react" in dependencies
            }
            
            self.audit_results["dependencies"] = dependency_analysis
            
            self.log(f"✅ Dependencies: {len(dependencies)} runtime, {len(dev_dependencies)} dev")
            if testing_libs:
                self.log(f"  - Testing libraries: {', '.join(testing_libs)}")
            if api_libs:
                self.log(f"  - API libraries: {', '.join(api_libs)}")
            
            return dependency_analysis
            
        except Exception as e:
            self.log(f"❌ Error reading package.json: {e}", "ERROR")
            return {}

    def generate_recommendations(self):
        """Generate recommendations based on analysis."""
        self.log("💡 Generating recommendations...")
        
        recommendations = []
        
        # Mock data recommendations
        mock_analysis = self.audit_results.get("mock_data_analysis", {})
        if mock_analysis.get("total_mock_instances", 0) > 0:
            recommendations.append({
                "category": "Mock Data",
                "priority": "HIGH",
                "issue": f"Found {mock_analysis['total_mock_instances']} mock data instances",
                "recommendation": "Replace mock data with real API calls and proper loading states"
            })
        
        # API integration recommendations
        api_analysis = self.audit_results.get("api_integration", {})
        api_calls = api_analysis.get("api_calls", {}).get("total_instances", 0)
        error_handling = api_analysis.get("error_handling", {}).get("total_instances", 0)
        
        if api_calls > 0 and error_handling < api_calls * 0.5:
            recommendations.append({
                "category": "Error Handling",
                "priority": "MEDIUM",
                "issue": "Insufficient error handling for API calls",
                "recommendation": "Add comprehensive error handling for all API calls"
            })
        
        # Component recommendations
        component_analysis = self.audit_results.get("component_analysis", {})
        components_with_issues = component_analysis.get("components_with_issues", [])
        
        if len(components_with_issues) > 0:
            recommendations.append({
                "category": "Components",
                "priority": "MEDIUM",
                "issue": f"{len(components_with_issues)} components have potential issues",
                "recommendation": "Review and fix component issues (error handling, hardcoded URLs, console.log statements)"
            })
        
        self.audit_results["recommendations"] = recommendations
        
        for rec in recommendations:
            self.log(f"  🔧 {rec['category']}: {rec['recommendation']}")
        
        return recommendations

    def print_detailed_report(self):
        """Print detailed audit report."""
        print("\n" + "="*80)
        print("FRONTEND CODE AUDIT REPORT")
        print("="*80)
        print(f"Audit Timestamp: {self.audit_results['timestamp']}")
        
        # Mock data analysis
        mock_analysis = self.audit_results.get("mock_data_analysis", {})
        print(f"\n📊 MOCK DATA ANALYSIS:")
        print(f"  Files with mock data: {mock_analysis.get('total_files_with_mocks', 0)}")
        print(f"  Total mock instances: {mock_analysis.get('total_mock_instances', 0)}")
        
        if mock_analysis.get("files"):
            print(f"  Files containing mock data:")
            for file_path, mocks in list(mock_analysis["files"].items())[:5]:  # Show first 5
                print(f"    - {file_path}: {len(mocks)} instances")
        
        # API integration
        api_analysis = self.audit_results.get("api_integration", {})
        print(f"\n🔗 API INTEGRATION:")
        for category, data in api_analysis.items():
            print(f"  {category}: {data.get('total_instances', 0)} instances")
        
        # Component analysis
        component_analysis = self.audit_results.get("component_analysis", {})
        stats = component_analysis.get("stats", {})
        print(f"\n⚛️  COMPONENT ANALYSIS:")
        print(f"  Total components: {stats.get('total_components', 0)}")
        print(f"  With state: {stats.get('components_with_state', 0)}")
        print(f"  With API calls: {stats.get('components_with_api_calls', 0)}")
        print(f"  With issues: {len(component_analysis.get('components_with_issues', []))}")
        
        # Dependencies
        dependencies = self.audit_results.get("dependencies", {})
        if dependencies:
            print(f"\n📦 DEPENDENCIES:")
            print(f"  Runtime dependencies: {dependencies.get('total_dependencies', 0)}")
            print(f"  Dev dependencies: {dependencies.get('total_dev_dependencies', 0)}")
            print(f"  Has TypeScript: {dependencies.get('has_typescript', False)}")
            print(f"  API libraries: {', '.join(dependencies.get('api_libraries', []))}")
        
        # Recommendations
        recommendations = self.audit_results.get("recommendations", [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
                print(f"  {priority_emoji.get(rec['priority'], '•')} {rec['category']}: {rec['recommendation']}")
        
        print("="*80)

    def save_report(self, filename: str = None):
        """Save the audit report."""
        if not filename:
            filename = f"frontend_code_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.audit_results, f, indent=2, default=str)
            self.log(f"✅ Report saved to {filename}")
        except Exception as e:
            self.log(f"❌ Failed to save report: {e}", "ERROR")

    def run_audit(self):
        """Run the complete frontend code audit."""
        self.log("🚀 Starting frontend code audit...")
        
        if not self.frontend_path.exists():
            self.log(f"❌ Frontend path not found: {self.frontend_path}", "ERROR")
            return False
        
        try:
            # Run analysis
            self.find_mock_data_usage()
            self.analyze_api_integration()
            self.analyze_components()
            self.check_package_dependencies()
            self.generate_recommendations()
            
            # Generate reports
            self.print_detailed_report()
            self.save_report()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Audit failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main function."""
    auditor = FrontendCodeAuditor()
    success = auditor.run_audit()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)