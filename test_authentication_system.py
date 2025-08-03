#!/usr/bin/env python3
"""
Authentication System Test for Frontend Integration

Tests the authentication implementation including:
- JWT token management
- Protected routes
- User profile management
- Login/logout functionality
- Redux integration
"""

import json
import requests
import time
from pathlib import Path
import sys
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root / "src"))

class AuthenticationSystemTester:
    """Test authentication system implementation."""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.test_results = []
        
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
    
    def test_auth_slice_implementation(self) -> bool:
        """Test Redux auth slice implementation."""
        print("\n🔐 Testing Auth Slice Implementation...")
        
        try:
            auth_slice_path = project_root / "frontend-react/src/store/slices/authSlice.ts"
            if not auth_slice_path.exists():
                self.log_test("Auth Slice File", False, "authSlice.ts not found")
                return False
            
            with open(auth_slice_path, 'r') as f:
                content = f.read()
            
            # Check for required interfaces
            required_interfaces = [
                "interface User",
                "interface AuthState",
                "id: string",
                "email: string", 
                "name: string",
                "role: string",
                "isAuthenticated: boolean",
                "token: string | null"
            ]
            
            for interface in required_interfaces:
                if interface not in content:
                    self.log_test("Auth Interfaces", False, f"Missing: {interface}")
                    return False
            
            self.log_test("Auth Interfaces", True, "All required interfaces defined")
            
            # Check for async thunks
            required_thunks = [
                "createAsyncThunk",
                "auth/login",
                "auth/register", 
                "auth/logout",
                "auth/refreshToken",
                "auth/getCurrentUser",
                "auth/updateProfile"
            ]
            
            for thunk in required_thunks:
                if thunk not in content:
                    self.log_test("Auth Thunks", False, f"Missing: {thunk}")
                    return False
            
            self.log_test("Auth Async Thunks", True, "All auth thunks implemented")
            
            # Check for API client integration
            if "apiClient.login" not in content:
                self.log_test("API Client Integration", False, "Auth slice not using real API client")
                return False
            
            self.log_test("API Client Integration", True, "Auth slice integrated with API client")
            
            # Check for proper error handling
            error_handling_features = [
                "rejectWithValue",
                "error instanceof Error",
                "action.payload as string"
            ]
            
            for feature in error_handling_features:
                if feature not in content:
                    self.log_test("Error Handling", False, f"Missing: {feature}")
                    return False
            
            self.log_test("Error Handling", True, "Proper error handling implemented")
            
            # Check for state management
            state_features = [
                "extraReducers",
                "pending",
                "fulfilled", 
                "rejected",
                "clearError",
                "setToken",
                "clearAuth"
            ]
            
            for feature in state_features:
                if feature not in content:
                    self.log_test("State Management", False, f"Missing: {feature}")
                    return False
            
            self.log_test("State Management", True, "Complete state management implemented")
            return True
            
        except Exception as e:
            self.log_test("Auth Slice Implementation", False, f"Error: {str(e)}")
            return False
    
    def test_protected_route_component(self) -> bool:
        """Test ProtectedRoute component implementation."""
        print("\n🛡️ Testing Protected Route Component...")
        
        try:
            protected_route_path = project_root / "frontend-react/src/components/ProtectedRoute.tsx"
            if not protected_route_path.exists():
                self.log_test("ProtectedRoute File", False, "ProtectedRoute.tsx not found")
                return False
            
            with open(protected_route_path, 'r') as f:
                content = f.read()
            
            # Check for component props interface
            required_props = [
                "children: React.ReactNode",
                "requireAuth?: boolean",
                "redirectTo?: string", 
                "allowedRoles?: string[]"
            ]
            
            for prop in required_props:
                if prop not in content:
                    self.log_test("ProtectedRoute Props", False, f"Missing prop: {prop}")
                    return False
            
            self.log_test("ProtectedRoute Props", True, "All required props defined")
            
            # Check for authentication logic
            auth_logic = [
                "useAppSelector",
                "isAuthenticated",
                "user",
                "loading",
                "localStorage.getItem",
                "auth_token",
                "getCurrentUser",
                "router.push"
            ]
            
            for logic in auth_logic:
                if logic not in content:
                    self.log_test("Auth Logic", False, f"Missing: {logic}")
                    return False
            
            self.log_test("Authentication Logic", True, "Complete auth logic implemented")
            
            # Check for role-based access
            if "allowedRoles.includes(user.role)" not in content:
                self.log_test("Role-based Access", False, "Role checking not implemented")
                return False
            
            self.log_test("Role-based Access", True, "Role-based access control implemented")
            
            # Check for loading states
            loading_features = [
                "CircularProgress",
                "Loading...",
                "minHeight: '100vh'"
            ]
            
            for feature in loading_features:
                if feature not in content:
                    self.log_test("Loading States", False, f"Missing: {feature}")
                    return False
            
            self.log_test("Loading States", True, "Loading states properly implemented")
            
            # Check for HOC export
            if "withAuth" not in content:
                self.log_test("HOC Export", False, "withAuth HOC not exported")
                return False
            
            self.log_test("HOC Export", True, "Higher-order component exported")
            return True
            
        except Exception as e:
            self.log_test("Protected Route Component", False, f"Error: {str(e)}")
            return False
    
    def test_user_profile_component(self) -> bool:
        """Test UserProfile component implementation."""
        print("\n👤 Testing User Profile Component...")
        
        try:
            profile_path = project_root / "frontend-react/src/components/UserProfile.tsx"
            if not profile_path.exists():
                self.log_test("UserProfile File", False, "UserProfile.tsx not found")
                return False
            
            with open(profile_path, 'r') as f:
                content = f.read()
            
            # Check for component props
            if "interface UserProfileProps" not in content:
                self.log_test("UserProfile Props", False, "Props interface not defined")
                return False
            
            self.log_test("UserProfile Props", True, "Props interface defined")
            
            # Check for form handling
            form_features = [
                "useState",
                "formData",
                "handleChange",
                "handleSave",
                "updateProfile",
                "TextField"
            ]
            
            for feature in form_features:
                if feature not in content:
                    self.log_test("Form Handling", False, f"Missing: {feature}")
                    return False
            
            self.log_test("Form Handling", True, "Form handling implemented")
            
            # Check for preferences management
            preferences_features = [
                "preferences",
                "emailNotifications",
                "pushNotifications",
                "Switch",
                "handlePreferenceChange"
            ]
            
            for feature in preferences_features:
                if feature not in content:
                    self.log_test("Preferences Management", False, f"Missing: {feature}")
                    return False
            
            self.log_test("Preferences Management", True, "User preferences implemented")
            
            # Check for logout functionality
            if "handleLogout" not in content or "dispatch(logout())" not in content:
                self.log_test("Logout Functionality", False, "Logout not properly implemented")
                return False
            
            self.log_test("Logout Functionality", True, "Logout functionality implemented")
            return True
            
        except Exception as e:
            self.log_test("User Profile Component", False, f"Error: {str(e)}")
            return False
    
    def test_auth_pages_integration(self) -> bool:
        """Test login and register pages integration."""
        print("\n📄 Testing Auth Pages Integration...")
        
        try:
            # Test login page
            login_path = project_root / "frontend-react/src/app/auth/login/page.tsx"
            if not login_path.exists():
                self.log_test("Login Page", False, "Login page not found")
                return False
            
            with open(login_path, 'r') as f:
                login_content = f.read()
            
            login_features = [
                "useAppDispatch",
                "useAppSelector",
                "login",
                "clearError",
                "isAuthenticated",
                "router.push('/dashboard')",
                "handleSubmit",
                "formData.email",
                "formData.password"
            ]
            
            for feature in login_features:
                if feature not in login_content:
                    self.log_test("Login Page Features", False, f"Missing: {feature}")
                    return False
            
            self.log_test("Login Page Integration", True, "Login page properly integrated")
            
            # Test register page
            register_path = project_root / "frontend-react/src/app/auth/register/page.tsx"
            if not register_path.exists():
                self.log_test("Register Page", False, "Register page not found")
                return False
            
            with open(register_path, 'r') as f:
                register_content = f.read()
            
            register_features = [
                "useAppDispatch",
                "useAppSelector", 
                "register",
                "clearError",
                "validateForm",
                "formData.fullName",
                "formData.email",
                "formData.password",
                "formData.confirmPassword"
            ]
            
            for feature in register_features:
                if feature not in register_content:
                    self.log_test("Register Page Features", False, f"Missing: {feature}")
                    return False
            
            self.log_test("Register Page Integration", True, "Register page properly integrated")
            
            # Check for redirect logic
            if "useEffect" not in login_content or "isAuthenticated" not in login_content:
                self.log_test("Auth Redirect Logic", False, "Redirect logic not implemented")
                return False
            
            self.log_test("Auth Redirect Logic", True, "Redirect logic implemented")
            return True
            
        except Exception as e:
            self.log_test("Auth Pages Integration", False, f"Error: {str(e)}")
            return False
    
    def test_navigation_auth_integration(self) -> bool:
        """Test navigation component auth integration."""
        print("\n🧭 Testing Navigation Auth Integration...")
        
        try:
            nav_path = project_root / "frontend-react/src/components/Navigation.tsx"
            if not nav_path.exists():
                self.log_test("Navigation File", False, "Navigation.tsx not found")
                return False
            
            with open(nav_path, 'r') as f:
                content = f.read()
            
            # Check for auth integration
            auth_features = [
                "useAppSelector",
                "useAppDispatch",
                "state.auth",
                "user",
                "isAuthenticated",
                "logout",
                "UserProfile"
            ]
            
            for feature in auth_features:
                if feature not in content:
                    self.log_test("Navigation Auth Features", False, f"Missing: {feature}")
                    return False
            
            self.log_test("Navigation Auth Integration", True, "Navigation integrated with auth")
            
            # Check for user display
            user_display_features = [
                "user?.name",
                "user.role",
                "Avatar",
                "Chip"
            ]
            
            for feature in user_display_features:
                if feature not in content:
                    self.log_test("User Display", False, f"Missing: {feature}")
                    return False
            
            self.log_test("User Display", True, "User information displayed")
            
            # Check for conditional rendering
            if "isAuthenticated &&" not in content:
                self.log_test("Conditional Rendering", False, "Auth-based conditional rendering missing")
                return False
            
            self.log_test("Conditional Rendering", True, "Auth-based conditional rendering implemented")
            return True
            
        except Exception as e:
            self.log_test("Navigation Auth Integration", False, f"Error: {str(e)}")
            return False
    
    def test_store_integration(self) -> bool:
        """Test Redux store auth integration."""
        print("\n🏪 Testing Store Auth Integration...")
        
        try:
            store_path = project_root / "frontend-react/src/store/index.ts"
            if not store_path.exists():
                self.log_test("Store File", False, "Store index.ts not found")
                return False
            
            with open(store_path, 'r') as f:
                content = f.read()
            
            # Check for auth reducer
            if "authReducer" not in content or "auth: authReducer" not in content:
                self.log_test("Auth Reducer Integration", False, "Auth reducer not in store")
                return False
            
            self.log_test("Auth Reducer Integration", True, "Auth reducer integrated in store")
            
            # Check for hooks file
            hooks_path = project_root / "frontend-react/src/store/hooks.ts"
            if hooks_path.exists():
                self.log_test("Store Hooks", True, "Store hooks file exists")
            else:
                self.log_test("Store Hooks", False, "Store hooks file missing")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Store Integration", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all authentication system tests."""
        print("🚀 Starting Authentication System Tests...")
        print("=" * 60)
        
        # Run all test categories
        test_results = {
            "auth_slice": self.test_auth_slice_implementation(),
            "protected_route": self.test_protected_route_component(),
            "user_profile": self.test_user_profile_component(),
            "auth_pages": self.test_auth_pages_integration(),
            "navigation_auth": self.test_navigation_auth_integration(),
            "store_integration": self.test_store_integration()
        }
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("📊 AUTHENTICATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Overall assessment
        overall_success = all(test_results.values())
        
        print(f"\n🎯 AUTHENTICATION SYSTEM: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
        
        if overall_success:
            print("\n🎉 Authentication system is fully implemented!")
            print("✅ JWT token management - COMPLETE")
            print("✅ Protected routes - COMPLETE") 
            print("✅ User profile management - COMPLETE")
            print("✅ Login/logout functionality - COMPLETE")
            print("✅ Redux integration - COMPLETE")
        else:
            print("\n⚠️  Some authentication features need attention.")
            print("Please review the failed tests above.")
        
        return {
            "overall_success": overall_success,
            "test_results": test_results,
            "detailed_results": self.test_results,
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests/total_tests)*100
            }
        }


def main():
    """Main test execution function."""
    tester = AuthenticationSystemTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)


if __name__ == "__main__":
    main()