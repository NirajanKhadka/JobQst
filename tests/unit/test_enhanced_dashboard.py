#!/usr/bin/env python3
"""
Enhanced Dashboard Test Suite

Tests the enhanced dashboard functionality including:
- Comprehensive statistics API endpoints
- Professional UI components
- Real-time data updates
- Job tracking and application monitoring
- Manual review and failure analysis
- Duplicate detection statistics

IMPORTANT: Tests real dashboard functionality with actual data
"""

import sys
import time
import json
import requests
from datetime import datetime
from typing import Dict, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class EnhancedDashboardTest:
    """Test suite for enhanced dashboard functionality."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        
    def test_api_endpoints(self) -> Dict:
        """Test all enhanced API endpoints."""
        console.print("\n[bold blue]🌐 Testing Enhanced API Endpoints[/bold blue]")
        
        test_result = {
            "success": False,
            "endpoints_tested": 0,
            "endpoints_working": 0,
            "endpoint_details": {},
            "errors": []
        }
        
        # Define API endpoints to test
        endpoints = [
            ("/api/comprehensive-stats", "Comprehensive Statistics"),
            ("/api/job-stats", "Job Statistics"),
            ("/api/application-stats", "Application Statistics"),
            ("/api/duplicate-stats", "Duplicate Statistics"),
            ("/api/performance-stats", "Performance Statistics"),
            ("/api/profile-stats", "Profile Statistics"),
            ("/stats", "Legacy Statistics"),
            ("/status", "System Status")
        ]
        
        try:
            for endpoint, description in endpoints:
                test_result["endpoints_tested"] += 1
                
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        test_result["endpoints_working"] += 1
                        test_result["endpoint_details"][endpoint] = {
                            "status": "✅ Working",
                            "description": description,
                            "data_keys": list(data.keys()) if isinstance(data, dict) else "Non-dict response"
                        }
                        console.print(f"[green]✅ {description}: {endpoint}[/green]")
                    else:
                        test_result["endpoint_details"][endpoint] = {
                            "status": f"❌ HTTP {response.status_code}",
                            "description": description,
                            "error": response.text
                        }
                        console.print(f"[red]❌ {description}: HTTP {response.status_code}[/red]")
                        
                except requests.exceptions.RequestException as e:
                    test_result["endpoint_details"][endpoint] = {
                        "status": "❌ Connection Error",
                        "description": description,
                        "error": str(e)
                    }
                    console.print(f"[red]❌ {description}: Connection Error[/red]")
            
            # Success if most endpoints work
            success_rate = test_result["endpoints_working"] / test_result["endpoints_tested"]
            if success_rate >= 0.8:  # 80% success rate
                test_result["success"] = True
                console.print(f"[green]✅ API endpoints test passed: {test_result['endpoints_working']}/{test_result['endpoints_tested']} working[/green]")
            else:
                test_result["errors"].append(f"Only {test_result['endpoints_working']}/{test_result['endpoints_tested']} endpoints working")
                
        except Exception as e:
            test_result["errors"].append(str(e))
            console.print(f"[red]❌ API endpoints test failed: {e}[/red]")
        
        return test_result
    
    def test_comprehensive_stats_structure(self) -> Dict:
        """Test the structure and content of comprehensive statistics."""
        console.print("\n[bold blue]📊 Testing Comprehensive Statistics Structure[/bold blue]")
        
        test_result = {
            "success": False,
            "required_sections": 0,
            "sections_present": 0,
            "data_quality": {},
            "errors": []
        }
        
        try:
            response = requests.get(f"{self.base_url}/api/comprehensive-stats", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required sections
                required_sections = [
                    "job_stats",
                    "application_stats", 
                    "duplicate_stats",
                    "performance_stats",
                    "profile_stats"
                ]
                
                test_result["required_sections"] = len(required_sections)
                
                for section in required_sections:
                    if section in data:
                        test_result["sections_present"] += 1
                        
                        # Analyze data quality for each section
                        section_data = data[section]
                        if isinstance(section_data, dict):
                            test_result["data_quality"][section] = {
                                "type": "dict",
                                "keys": list(section_data.keys()),
                                "non_empty": len([k for k, v in section_data.items() if v not in [None, "", 0, {}]])
                            }
                            console.print(f"[green]✅ {section}: {len(section_data)} fields[/green]")
                        else:
                            test_result["data_quality"][section] = {
                                "type": type(section_data).__name__,
                                "value": section_data
                            }
                            console.print(f"[yellow]⚠️ {section}: Non-dict data[/yellow]")
                    else:
                        console.print(f"[red]❌ Missing section: {section}[/red]")
                
                # Success if most sections are present
                if test_result["sections_present"] >= test_result["required_sections"] * 0.8:
                    test_result["success"] = True
                    console.print(f"[green]✅ Comprehensive stats structure valid: {test_result['sections_present']}/{test_result['required_sections']} sections[/green]")
                else:
                    test_result["errors"].append(f"Only {test_result['sections_present']}/{test_result['required_sections']} required sections present")
            else:
                test_result["errors"].append(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            test_result["errors"].append(str(e))
            console.print(f"[red]❌ Comprehensive stats test failed: {e}[/red]")
        
        return test_result
    
    def test_dashboard_ui_accessibility(self) -> Dict:
        """Test dashboard UI accessibility and responsiveness."""
        console.print("\n[bold blue]🎨 Testing Dashboard UI Accessibility[/bold blue]")
        
        test_result = {
            "success": False,
            "ui_elements_found": 0,
            "expected_elements": 0,
            "ui_analysis": {},
            "errors": []
        }
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Check for key UI elements
                ui_elements = [
                    ("AutoJobAgent Dashboard", "Page Title"),
                    ("totalScraped", "Jobs Scraped Metric"),
                    ("totalApplications", "Applications Metric"),
                    ("manualReviews", "Manual Reviews Metric"),
                    ("duplicatesDetected", "Duplicates Metric"),
                    ("applicationChart", "Application Chart"),
                    ("sourcesChart", "Sources Chart"),
                    ("manualReasons", "Manual Reasons Section"),
                    ("failureReasons", "Failure Reasons Section"),
                    ("recentActivity", "Recent Activity Table"),
                    ("pauseBtn", "Pause Button"),
                    ("refreshBtn", "Refresh Button")
                ]
                
                test_result["expected_elements"] = len(ui_elements)
                
                for element_id, description in ui_elements:
                    if element_id in html_content:
                        test_result["ui_elements_found"] += 1
                        test_result["ui_analysis"][element_id] = "✅ Present"
                        console.print(f"[green]✅ {description}: Found[/green]")
                    else:
                        test_result["ui_analysis"][element_id] = "❌ Missing"
                        console.print(f"[red]❌ {description}: Missing[/red]")
                
                # Check for modern UI frameworks
                modern_features = [
                    ("tailwindcss", "Tailwind CSS"),
                    ("chart.js", "Chart.js"),
                    ("font-awesome", "Font Awesome Icons"),
                    ("WebSocket", "WebSocket Support")
                ]
                
                for feature, description in modern_features:
                    if feature in html_content:
                        console.print(f"[green]✅ {description}: Included[/green]")
                    else:
                        console.print(f"[yellow]⚠️ {description}: Not found[/yellow]")
                
                # Success if most UI elements are present
                if test_result["ui_elements_found"] >= test_result["expected_elements"] * 0.8:
                    test_result["success"] = True
                    console.print(f"[green]✅ Dashboard UI test passed: {test_result['ui_elements_found']}/{test_result['expected_elements']} elements found[/green]")
                else:
                    test_result["errors"].append(f"Only {test_result['ui_elements_found']}/{test_result['expected_elements']} UI elements found")
            else:
                test_result["errors"].append(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            test_result["errors"].append(str(e))
            console.print(f"[red]❌ Dashboard UI test failed: {e}[/red]")
        
        return test_result
    
    def test_real_time_functionality(self) -> Dict:
        """Test real-time functionality and WebSocket connections."""
        console.print("\n[bold blue]⚡ Testing Real-time Functionality[/bold blue]")
        
        test_result = {
            "success": False,
            "websocket_support": False,
            "pause_resume_works": False,
            "auto_refresh_configured": False,
            "errors": []
        }
        
        try:
            # Test pause functionality
            try:
                pause_response = requests.post(f"{self.base_url}/action/pause", timeout=5)
                if pause_response.status_code == 200:
                    console.print("[green]✅ Pause endpoint working[/green]")
                    
                    # Test resume functionality
                    resume_response = requests.post(f"{self.base_url}/action/resume", timeout=5)
                    if resume_response.status_code == 200:
                        test_result["pause_resume_works"] = True
                        console.print("[green]✅ Resume endpoint working[/green]")
                    else:
                        console.print(f"[red]❌ Resume endpoint failed: HTTP {resume_response.status_code}[/red]")
                else:
                    console.print(f"[red]❌ Pause endpoint failed: HTTP {pause_response.status_code}[/red]")
            except requests.exceptions.RequestException as e:
                console.print(f"[red]❌ Pause/Resume test failed: {e}[/red]")
            
            # Check for WebSocket support in HTML
            try:
                response = requests.get(f"{self.base_url}/", timeout=5)
                if response.status_code == 200:
                    html_content = response.text
                    if "WebSocket" in html_content and "connectWebSocket" in html_content:
                        test_result["websocket_support"] = True
                        console.print("[green]✅ WebSocket support detected[/green]")
                    else:
                        console.print("[red]❌ WebSocket support not found[/red]")
                    
                    if "setInterval" in html_content and "30000" in html_content:
                        test_result["auto_refresh_configured"] = True
                        console.print("[green]✅ Auto-refresh configured (30s interval)[/green]")
                    else:
                        console.print("[red]❌ Auto-refresh not configured[/red]")
            except requests.exceptions.RequestException as e:
                console.print(f"[red]❌ HTML analysis failed: {e}[/red]")
            
            # Overall success
            features_working = sum([
                test_result["pause_resume_works"],
                test_result["websocket_support"],
                test_result["auto_refresh_configured"]
            ])
            
            if features_working >= 2:  # At least 2 out of 3 features working
                test_result["success"] = True
                console.print(f"[green]✅ Real-time functionality test passed: {features_working}/3 features working[/green]")
            else:
                test_result["errors"].append(f"Only {features_working}/3 real-time features working")
                
        except Exception as e:
            test_result["errors"].append(str(e))
            console.print(f"[red]❌ Real-time functionality test failed: {e}[/red]")
        
        return test_result

    def run_all_tests(self) -> bool:
        """Run all enhanced dashboard tests."""
        console.print(Panel("🧪 Enhanced Dashboard Test Suite", style="bold blue"))

        # Check if dashboard is running
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code != 200:
                console.print(f"[red]❌ Dashboard not accessible at {self.base_url}[/red]")
                console.print("[yellow]💡 Please start the dashboard with: python dashboard_api.py[/yellow]")
                return False
        except requests.exceptions.RequestException:
            console.print(f"[red]❌ Dashboard not running at {self.base_url}[/red]")
            console.print("[yellow]💡 Please start the dashboard with: python dashboard_api.py[/yellow]")
            return False

        console.print(f"[green]✅ Dashboard accessible at {self.base_url}[/green]")

        # Run tests
        tests = [
            ("API Endpoints", self.test_api_endpoints),
            ("Comprehensive Statistics", self.test_comprehensive_stats_structure),
            ("Dashboard UI", self.test_dashboard_ui_accessibility),
            ("Real-time Functionality", self.test_real_time_functionality),
        ]

        all_passed = True

        for test_name, test_func in tests:
            console.print(f"\n[bold cyan]Running: {test_name}[/bold cyan]")
            start_time = time.time()

            try:
                result = test_func()
                duration = time.time() - start_time

                self.test_results.append({
                    'test_name': test_name,
                    'result': result,
                    'duration': duration,
                    'success': result.get('success', False)
                })

                if result.get('success', False):
                    console.print(f"[green]✅ {test_name} passed ({duration:.2f}s)[/green]")
                else:
                    console.print(f"[red]❌ {test_name} failed ({duration:.2f}s)[/red]")
                    if result.get('errors'):
                        for error in result['errors']:
                            console.print(f"[red]  - {error}[/red]")
                    all_passed = False

            except Exception as e:
                console.print(f"[red]❌ {test_name} crashed: {e}[/red]")
                all_passed = False

        # Display final results
        self.display_results()

        return all_passed

    def display_results(self):
        """Display comprehensive test results."""
        console.print("\n")

        # Results table
        table = Table(title="🧪 Enhanced Dashboard Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Duration", style="yellow")
        table.add_column("Key Metrics", style="white")

        for test in self.test_results:
            status = "[green]✅ PASS[/green]" if test['success'] else "[red]❌ FAIL[/red]"
            duration = f"{test['duration']:.2f}s"

            # Extract key metrics
            result = test['result']
            metrics = []

            if 'endpoints_working' in result:
                metrics.append(f"Endpoints: {result['endpoints_working']}/{result['endpoints_tested']}")
            if 'sections_present' in result:
                metrics.append(f"Sections: {result['sections_present']}/{result['required_sections']}")
            if 'ui_elements_found' in result:
                metrics.append(f"UI Elements: {result['ui_elements_found']}/{result['expected_elements']}")

            metrics_str = " | ".join(metrics[:2]) if metrics else "N/A"

            table.add_row(test['test_name'], status, duration, metrics_str)

        console.print(table)

        # Summary
        passed_tests = sum(1 for t in self.test_results if t['success'])
        total_tests = len(self.test_results)

        if passed_tests == total_tests:
            console.print(f"\n[bold green]🎉 All {total_tests} enhanced dashboard tests passed![/bold green]")
            console.print("[green]✨ Dashboard is fully functional with professional UI and real-time features![/green]")
        else:
            console.print(f"\n[bold yellow]⚠️ {passed_tests}/{total_tests} enhanced dashboard tests passed[/bold yellow]")


def main():
    """Run the enhanced dashboard test suite."""
    test_suite = EnhancedDashboardTest()
    success = test_suite.run_all_tests()

    if success:
        console.print(f"\n[bold green]✅ Enhanced dashboard is fully functional![/bold green]")
        console.print(f"[cyan]🌐 Access the dashboard at: http://localhost:8000[/cyan]")
        return 0
    else:
        console.print(f"\n[bold red]❌ Some dashboard tests failed. Check results above.[/bold red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
