#!/usr/bin/env python3
"""
R Territory AI Backend Testing Suite
Tests all critical backend functionality including auth, API config, territories, and pins
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any, Optional

# Backend URL from frontend/.env
BACKEND_URL = "https://territory-insights.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.viewer_token = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, message: str, details: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        })
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None, token: str = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{BACKEND_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            async with self.session.request(method, url, json=data, headers=headers) as response:
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                return response.status < 400, response_data, response.status
        except Exception as e:
            return False, str(e), 0
    
    async def test_user_signup(self, email: str, password: str, name: str, role: str) -> Optional[str]:
        """Test user signup and return token if successful"""
        success, data, status = await self.make_request("POST", "/auth/signup", {
            "email": email,
            "password": password,
            "name": name,
            "role": role
        })
        
        if success and "token" in data:
            self.log_result(f"User Signup ({role})", True, f"Successfully created {role} user")
            return data["token"]
        elif not success and "already registered" in str(data).lower():
            self.log_result(f"User Signup ({role})", True, f"User already exists (expected)")
            return None
        else:
            self.log_result(f"User Signup ({role})", False, f"Failed to create user", data)
            return None
    
    async def test_user_login(self, email: str, password: str, role: str) -> Optional[str]:
        """Test user login and return token if successful"""
        success, data, status = await self.make_request("POST", "/auth/login", {
            "email": email,
            "password": password
        })
        
        if success and "token" in data:
            self.log_result(f"User Login ({role})", True, f"Successfully logged in {role} user")
            return data["token"]
        else:
            self.log_result(f"User Login ({role})", False, f"Failed to login", data)
            return None
    
    async def test_api_configuration(self, token: str):
        """Test API key configuration endpoint"""
        config_data = {
            "openai_api_key": "sk-test-dummy-openai-key-12345",
            "pincode_api_url": "https://api.example.com/pincode",
            "pincode_api_key": "dummy-pincode-api-key-67890"
        }
        
        success, data, status = await self.make_request("POST", "/auth/config-api-key", config_data, token)
        
        if success:
            self.log_result("API Configuration", True, "Successfully configured API keys")
        else:
            self.log_result("API Configuration", False, "Failed to configure API keys", data)
    
    async def test_pincode_boundary(self, token: str):
        """Test pincode boundary endpoint (expected to fail without real API)"""
        success, data, status = await self.make_request("POST", "/pincode/boundary", {
            "pincode": "380001"
        }, token)
        
        # This should fail because we're using dummy API config
        if not success and status in [400, 500]:
            self.log_result("Pincode Boundary", True, "Correctly failed with dummy API config (expected behavior)")
        elif not success and "not configured" in str(data).lower():
            self.log_result("Pincode Boundary", True, "Correctly requires API configuration")
        else:
            self.log_result("Pincode Boundary", False, "Unexpected response", data)
    
    async def test_territory_creation(self, token: str):
        """Test territory creation with validation"""
        territory_data = {
            "name": "Test Territory Ahmedabad",
            "city": "Ahmedabad",
            "zone": "West Zone",
            "pincode": "380001",
            "center": {"lat": 23.0225, "lng": 72.5714},
            "radius": 5000,
            "boundary": [
                [23.0225, 72.5714],
                [23.0235, 72.5724],
                [23.0215, 72.5734],
                [23.0205, 72.5704],
                [23.0225, 72.5714]
            ],
            "metrics": {
                "investments": 7.5,
                "buildings": 150,
                "populationDensity": 8.2,
                "qualityOfProject": 7.0,
                "govtInfra": 6.5,
                "livabilityIndex": 7.8,
                "airPollutionIndex": 6.0,
                "roads": 7.2,
                "crimeRate": 4.5
            },
            "restrictions": {
                "rentFamilyOnly": False,
                "pgAllowed": True
            }
        }
        
        success, data, status = await self.make_request("POST", "/territories", territory_data, token)
        
        if success and "id" in data:
            self.log_result("Territory Creation", True, "Successfully created territory with validation")
            return data["id"]
        else:
            self.log_result("Territory Creation", False, "Failed to create territory", data)
            return None
    
    async def test_territory_listing(self, token: str):
        """Test territory listing"""
        success, data, status = await self.make_request("GET", "/territories", token=token)
        
        if success and isinstance(data, list):
            self.log_result("Territory Listing", True, f"Successfully retrieved {len(data)} territories")
        else:
            self.log_result("Territory Listing", False, "Failed to retrieve territories", data)
    
    async def test_pin_creation_admin(self, token: str, territory_id: str = None):
        """Test pin creation with admin user"""
        pin_data = {
            "location": {"lat": 23.0225, "lng": 72.5714},
            "type": ["Job", "Commercial"],
            "label": "Test Job Center",
            "description": "A test job center for backend testing",
            "address": "Test Address, Ahmedabad",
            "hasGeofence": True,
            "geofenceRadius": 500,
            "territoryId": territory_id,
            "generateAIInsights": False
        }
        
        success, data, status = await self.make_request("POST", "/pins", pin_data, token)
        
        if success and "id" in data:
            self.log_result("Pin Creation (Admin)", True, "Successfully created pin as admin")
            return data["id"]
        else:
            self.log_result("Pin Creation (Admin)", False, "Failed to create pin as admin", data)
            return None
    
    async def test_pin_creation_viewer(self, token: str):
        """Test pin creation with viewer user (should fail)"""
        pin_data = {
            "location": {"lat": 23.0225, "lng": 72.5714},
            "type": ["Supplier"],
            "label": "Test Supplier",
            "description": "Should fail - viewer cannot create pins"
        }
        
        success, data, status = await self.make_request("POST", "/pins", pin_data, token)
        
        if not success and status == 403:
            self.log_result("Pin RBAC (Viewer)", True, "Correctly blocked viewer from creating pins")
        else:
            self.log_result("Pin RBAC (Viewer)", False, "Viewer was allowed to create pins (security issue!)", data)
    
    async def test_pin_listing(self, token: str):
        """Test pin listing"""
        success, data, status = await self.make_request("GET", "/pins", token=token)
        
        if success and isinstance(data, list):
            self.log_result("Pin Listing", True, f"Successfully retrieved {len(data)} pins")
        else:
            self.log_result("Pin Listing", False, "Failed to retrieve pins", data)
    
    async def test_pin_filtering_by_territory(self, token: str, territory_id: str):
        """Test pin filtering by territory"""
        success, data, status = await self.make_request("GET", f"/pins?territory_id={territory_id}", token=token)
        
        if success and isinstance(data, list):
            self.log_result("Pin Filtering", True, f"Successfully filtered pins by territory ({len(data)} pins)")
        else:
            self.log_result("Pin Filtering", False, "Failed to filter pins by territory", data)
    
    async def test_ai_insights_calculation(self, token: str):
        """Test AI insights are calculated correctly"""
        # This is tested implicitly during territory creation
        # We can verify by checking if aiInsights field exists in territory response
        success, data, status = await self.make_request("GET", "/territories", token=token)
        
        if success and isinstance(data, list) and len(data) > 0:
            territory = data[0]
            if "aiInsights" in territory and "appreciationPercent" in territory["aiInsights"]:
                self.log_result("AI Insights Calculation", True, "AI insights properly calculated for territories")
            else:
                self.log_result("AI Insights Calculation", False, "AI insights missing from territory data")
        else:
            self.log_result("AI Insights Calculation", False, "Could not verify AI insights - no territories found")
    
    # NEW COMMUNITY MANAGEMENT TESTS
    async def test_community_creation(self, token: str, territory_id: str = None) -> Optional[str]:
        """Test community creation"""
        community_data = {
            "name": "Tech Innovators Hub",
            "description": "A community for technology professionals and innovators in the area",
            "territoryId": territory_id or "test-territory-id",
            "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "canJoin": True
        }
        
        success, data, status = await self.make_request("POST", "/communities", community_data, token)
        
        if success and "id" in data:
            self.log_result("Community Creation", True, f"Successfully created community: {data.get('name', 'Unknown')}")
            return data["id"]
        else:
            self.log_result("Community Creation", False, "Failed to create community", data)
            return None
    
    async def test_community_listing(self, token: str):
        """Test community listing"""
        success, data, status = await self.make_request("GET", "/communities", token=token)
        
        if success and isinstance(data, list):
            self.log_result("Community Listing", True, f"Successfully retrieved {len(data)} communities")
            return data
        else:
            self.log_result("Community Listing", False, "Failed to retrieve communities", data)
            return []
    
    async def test_community_get_single(self, token: str, community_id: str):
        """Test getting single community"""
        success, data, status = await self.make_request("GET", f"/communities/{community_id}", token=token)
        
        if success and "id" in data:
            self.log_result("Community Get Single", True, f"Successfully retrieved community: {data.get('name', 'Unknown')}")
        else:
            self.log_result("Community Get Single", False, "Failed to retrieve single community", data)
    
    async def test_community_join(self, token: str, community_id: str):
        """Test joining a community"""
        success, data, status = await self.make_request("POST", f"/communities/{community_id}/join", {}, token)
        
        if success:
            self.log_result("Community Join", True, "Successfully joined community")
        else:
            self.log_result("Community Join", False, "Failed to join community", data)
    
    # NEW POSTS MANAGEMENT TESTS
    async def test_post_creation(self, token: str, community_id: str) -> Optional[str]:
        """Test post creation"""
        post_data = {
            "communityId": community_id,
            "text": "Exciting new development project coming to our territory! Great opportunities for local businesses and residents. #TerritoryDevelopment #Community",
            "location": {"lat": 23.0225, "lng": 72.5714},
            "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
        }
        
        success, data, status = await self.make_request("POST", "/posts", post_data, token)
        
        if success and "id" in data:
            self.log_result("Post Creation", True, f"Successfully created post in community")
            return data["id"]
        else:
            self.log_result("Post Creation", False, "Failed to create post", data)
            return None
    
    async def test_post_listing(self, token: str):
        """Test post listing (all posts)"""
        success, data, status = await self.make_request("GET", "/posts", token=token)
        
        if success and isinstance(data, list):
            self.log_result("Post Listing (All)", True, f"Successfully retrieved {len(data)} posts")
        else:
            self.log_result("Post Listing (All)", False, "Failed to retrieve posts", data)
    
    async def test_post_listing_by_community(self, token: str, community_id: str):
        """Test post listing filtered by community"""
        success, data, status = await self.make_request("GET", f"/posts?community_id={community_id}", token=token)
        
        if success and isinstance(data, list):
            self.log_result("Post Listing (By Community)", True, f"Successfully retrieved {len(data)} posts for community")
        else:
            self.log_result("Post Listing (By Community)", False, "Failed to retrieve posts by community", data)
    
    # NEW TERRITORY PROFILE TESTS
    async def test_territory_profile(self, token: str, territory_id: str):
        """Test territory profile endpoint"""
        success, data, status = await self.make_request("GET", f"/territories/{territory_id}/profile", token=token)
        
        if success and "territory" in data and "stats" in data:
            stats = data["stats"]
            territory = data["territory"]
            self.log_result("Territory Profile", True, 
                          f"Successfully retrieved territory profile for {territory.get('name', 'Unknown')} - "
                          f"Stats: {stats.get('professionals', 0)} professionals, {stats.get('projects', 0)} projects, "
                          f"{stats.get('opportunities', 0)} opportunities, {stats.get('posts', 0)} posts")
        else:
            self.log_result("Territory Profile", False, "Failed to retrieve territory profile", data)
    
    # NEW SUPPORTING DATA ENDPOINTS TESTS
    async def test_professionals_listing(self, token: str, territory_id: str = None):
        """Test professionals listing"""
        endpoint = "/professionals"
        if territory_id:
            endpoint += f"?territory_id={territory_id}"
        
        success, data, status = await self.make_request("GET", endpoint, token=token)
        
        if success and isinstance(data, list):
            filter_msg = f" (filtered by territory {territory_id})" if territory_id else ""
            self.log_result("Professionals Listing", True, f"Successfully retrieved {len(data)} professionals{filter_msg}")
        else:
            self.log_result("Professionals Listing", False, "Failed to retrieve professionals", data)
    
    async def test_projects_listing(self, token: str, territory_id: str = None):
        """Test projects listing"""
        endpoint = "/projects"
        if territory_id:
            endpoint += f"?territory_id={territory_id}"
        
        success, data, status = await self.make_request("GET", endpoint, token=token)
        
        if success and isinstance(data, list):
            filter_msg = f" (filtered by territory {territory_id})" if territory_id else ""
            self.log_result("Projects Listing", True, f"Successfully retrieved {len(data)} projects{filter_msg}")
        else:
            self.log_result("Projects Listing", False, "Failed to retrieve projects", data)
    
    async def test_opportunities_listing(self, token: str, territory_id: str = None):
        """Test opportunities listing"""
        endpoint = "/opportunities"
        if territory_id:
            endpoint += f"?territory_id={territory_id}"
        
        success, data, status = await self.make_request("GET", endpoint, token=token)
        
        if success and isinstance(data, list):
            filter_msg = f" (filtered by territory {territory_id})" if territory_id else ""
            self.log_result("Opportunities Listing", True, f"Successfully retrieved {len(data)} opportunities{filter_msg}")
        else:
            self.log_result("Opportunities Listing", False, "Failed to retrieve opportunities", data)
    
    async def test_events_listing(self, token: str, territory_id: str = None):
        """Test events listing"""
        endpoint = "/events"
        if territory_id:
            endpoint += f"?territory_id={territory_id}"
        
        success, data, status = await self.make_request("GET", endpoint, token=token)
        
        if success and isinstance(data, list):
            filter_msg = f" (filtered by territory {territory_id})" if territory_id else ""
            self.log_result("Events Listing", True, f"Successfully retrieved {len(data)} events{filter_msg}")
        else:
            self.log_result("Events Listing", False, "Failed to retrieve events", data)
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting R Territory AI Backend Tests")
        print(f"Testing against: {BACKEND_URL}")
        print("=" * 60)
        
        # Test 1: Admin user signup and login
        admin_email = "admin@test.com"
        admin_password = "password123"
        
        # Try signup first, if it fails (user exists), try login
        self.admin_token = await self.test_user_signup(admin_email, admin_password, "Admin User", "admin")
        if not self.admin_token:
            self.admin_token = await self.test_user_login(admin_email, admin_password, "admin")
        
        if not self.admin_token:
            print("❌ CRITICAL: Cannot proceed without admin authentication")
            return
        
        # Test 2: API Configuration
        await self.test_api_configuration(self.admin_token)
        
        # Test 3: Pincode boundary endpoint (expected to fail)
        await self.test_pincode_boundary(self.admin_token)
        
        # Test 4: Territory creation and listing
        territory_id = await self.test_territory_creation(self.admin_token)
        await self.test_territory_listing(self.admin_token)
        
        # Test 5: Pin creation and listing (admin)
        pin_id = await self.test_pin_creation_admin(self.admin_token, territory_id)
        await self.test_pin_listing(self.admin_token)
        
        # Test 6: Pin filtering
        if territory_id:
            await self.test_pin_filtering_by_territory(self.admin_token, territory_id)
        
        # Test 7: AI insights calculation
        await self.test_ai_insights_calculation(self.admin_token)
        
        # Test 8: Viewer user RBAC
        viewer_email = "viewer@test.com"
        viewer_password = "password123"
        
        self.viewer_token = await self.test_user_signup(viewer_email, viewer_password, "Viewer User", "viewer")
        if not self.viewer_token:
            self.viewer_token = await self.test_user_login(viewer_email, viewer_password, "viewer")
        
        if self.viewer_token:
            await self.test_pin_creation_viewer(self.viewer_token)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        return self.test_results

async def main():
    """Main test runner"""
    async with BackendTester() as tester:
        results = await tester.run_all_tests()
        
        # Return appropriate exit code
        failed_count = sum(1 for r in results if not r["success"])
        sys.exit(0 if failed_count == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())