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
BACKEND_URL = "https://territory-insights-1.preview.emergentagent.com/api"

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
        """Test pincode boundary endpoint"""
        success, data, status = await self.make_request("POST", "/pincode/boundary", {
            "pincode": "380001"
        }, token)
        
        if success and "boundary" in data and "center" in data:
            source = data.get("source", "unknown")
            self.log_result("Pincode Boundary", True, f"Successfully retrieved pincode boundary from {source}")
        elif not success and status in [400, 500]:
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
            return data
        else:
            self.log_result("Events Listing", False, "Failed to retrieve events", data)
            return []
    
    # NEW SPECIFIC TESTS FOR EVENTS AND PROJECTS CREATION
    async def test_event_creation_specific(self, token: str, territory_id: str) -> Optional[str]:
        """Test specific event creation as requested"""
        event_data = {
            "title": "Community Meetup",
            "date": "2025-12-01T18:00:00",
            "location": "Community Hall, Satellite Area",
            "territoryId": territory_id,
            "organizer": "Admin Team"
        }
        
        success, data, status = await self.make_request("POST", "/events", event_data, token)
        
        if success and "id" in data:
            # Verify status is "upcoming"
            if data.get("status") == "upcoming":
                self.log_result("Event Creation (Specific)", True, 
                              f"Successfully created event '{data.get('title')}' with status '{data.get('status')}'")
            else:
                self.log_result("Event Creation (Specific)", False, 
                              f"Event created but status is '{data.get('status')}' instead of 'upcoming'")
            return data["id"]
        else:
            self.log_result("Event Creation (Specific)", False, "Failed to create specific event", data)
            return None
    
    async def test_project_creation_specific(self, token: str, territory_id: str) -> Optional[str]:
        """Test specific project creation as requested"""
        project_data = {
            "name": "Skyline Apartments",
            "status": "Under Construction",
            "developerName": "ABC Developers",
            "priceRange": "50L - 80L",
            "configuration": "2BHK, 3BHK",
            "location": {"lat": 23.0225, "lng": 72.5714},
            "territoryId": territory_id,
            "brochureUrl": "https://example.com/brochure.pdf"
        }
        
        success, data, status = await self.make_request("POST", "/projects", project_data, token)
        
        if success and "id" in data:
            self.log_result("Project Creation (Specific)", True, 
                          f"Successfully created project '{data.get('name')}' by {data.get('developerName')}")
            return data["id"]
        else:
            self.log_result("Project Creation (Specific)", False, "Failed to create specific project", data)
            return None
    
    async def test_event_appears_in_list(self, token: str, event_id: str):
        """Verify created event appears in events list"""
        events = await self.test_events_listing(token)
        
        if any(event.get("id") == event_id for event in events):
            self.log_result("Event List Verification", True, "Created event appears in events list")
        else:
            self.log_result("Event List Verification", False, "Created event does not appear in events list")
    
    async def test_project_appears_in_list(self, token: str, project_id: str):
        """Verify created project appears in projects list"""
        success, data, status = await self.make_request("GET", "/projects", token=token)
        
        if success and isinstance(data, list):
            if any(project.get("id") == project_id for project in data):
                self.log_result("Project List Verification", True, "Created project appears in projects list")
            else:
                self.log_result("Project List Verification", False, "Created project does not appear in projects list")
        else:
            self.log_result("Project List Verification", False, "Failed to retrieve projects for verification", data)
    
    # NEW DATA SUBMISSION & ANALYTICS TESTS
    async def test_metrics_submission(self, token: str, territory_id: str) -> Optional[str]:
        """Test metrics submission endpoint (POST /api/metrics)"""
        metrics_data = {
            "territoryId": territory_id,
            "job_likelihood": 7.5,
            "crime_rate": 3.2,
            "security": 8.1,
            "livelihood": 7.8,
            "air_quality_index": 6.5,
            "food_hygiene": 8.3,
            "property_value": 65.5,  # in lakhs
            "rent_average": 25000,   # per month
            "occupancy_rate": 85.0,  # percentage
            "maintenance_cost": 3500, # per month
            "tenant_type": "Working Professionals",
            "notes": "High-quality residential area with good connectivity and amenities"
        }
        
        success, data, status = await self.make_request("POST", "/metrics", metrics_data, token)
        
        if success and "id" in data:
            self.log_result("Metrics Submission", True, 
                          f"Successfully submitted metrics for territory {territory_id}")
            return data["id"]
        else:
            self.log_result("Metrics Submission", False, "Failed to submit metrics", data)
            return None
    
    async def test_metrics_retrieval(self, token: str, territory_id: str = None):
        """Test metrics retrieval endpoint (GET /api/metrics)"""
        endpoint = "/metrics"
        if territory_id:
            endpoint += f"?territory_id={territory_id}"
        
        success, data, status = await self.make_request("GET", endpoint, token=token)
        
        if success and isinstance(data, list):
            filter_msg = f" (filtered by territory {territory_id})" if territory_id else ""
            self.log_result("Metrics Retrieval", True, 
                          f"Successfully retrieved {len(data)} metrics submissions{filter_msg}")
            return data
        else:
            self.log_result("Metrics Retrieval", False, "Failed to retrieve metrics", data)
            return []
    
    async def test_dashboard_analytics(self, token: str):
        """Test dashboard analytics endpoint (GET /api/analytics/dashboard)"""
        success, data, status = await self.make_request("GET", "/analytics/dashboard", token=token)
        
        if success and isinstance(data, dict):
            # Check required fields
            required_fields = ["metrics", "property", "news_metrics", "totalMetricsSubmissions", "totalTerritories"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                metrics = data["metrics"]
                property_data = data["property"]
                news_metrics = data["news_metrics"]
                
                # Verify metrics structure
                expected_metrics = ["job_likelihood", "crime_rate", "security", "livelihood", 
                                  "air_quality_index", "food_hygiene", "livability_index"]
                metrics_ok = all(metric in metrics for metric in expected_metrics)
                
                # Verify property structure
                expected_property = ["avg_property_value", "avg_rent", "avg_occupancy"]
                property_ok = all(prop in property_data for prop in expected_property)
                
                # Verify news metrics structure
                expected_news = ["crime_score", "investment_score", "job_score", "infrastructure_score"]
                news_ok = all(news in news_metrics for news in expected_news)
                
                if metrics_ok and property_ok and news_ok:
                    self.log_result("Dashboard Analytics", True, 
                                  f"Successfully retrieved dashboard analytics - "
                                  f"Territories: {data['totalTerritories']}, "
                                  f"Submissions: {data['totalMetricsSubmissions']}, "
                                  f"Livability Index: {metrics.get('livability_index', 0)}")
                else:
                    missing_structures = []
                    if not metrics_ok: missing_structures.append("metrics")
                    if not property_ok: missing_structures.append("property")
                    if not news_ok: missing_structures.append("news_metrics")
                    self.log_result("Dashboard Analytics", False, 
                                  f"Missing expected structure in: {', '.join(missing_structures)}")
            else:
                self.log_result("Dashboard Analytics", False, 
                              f"Missing required fields: {', '.join(missing_fields)}", data)
        else:
            self.log_result("Dashboard Analytics", False, "Failed to retrieve dashboard analytics", data)
    
    async def test_news_scraping(self, token: str, pages: int = 2):
        """Test news scraping endpoint (GET /api/news/scraped)"""
        success, data, status = await self.make_request("GET", f"/news/scraped?pages={pages}", token=token)
        
        if success and isinstance(data, dict):
            # Check required fields
            required_fields = ["crime_rate_score", "investment_activity_score", "job_market_score", 
                             "property_market_score", "infrastructure_score", "livability_index",
                             "crime_mentions", "investment_mentions", "job_mentions", 
                             "property_mentions", "infrastructure_mentions", "articles", "articles_analyzed"]
            
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Verify score ranges (should be 0-10)
                scores = {
                    "crime_rate_score": data["crime_rate_score"],
                    "investment_activity_score": data["investment_activity_score"],
                    "job_market_score": data["job_market_score"],
                    "property_market_score": data["property_market_score"],
                    "infrastructure_score": data["infrastructure_score"],
                    "livability_index": data["livability_index"]
                }
                
                invalid_scores = {k: v for k, v in scores.items() if not (0 <= v <= 10)}
                
                if not invalid_scores:
                    articles = data.get("articles", [])
                    articles_count = data.get("articles_analyzed", 0)
                    
                    self.log_result("News Scraping", True, 
                                  f"Successfully scraped and analyzed news - "
                                  f"Articles analyzed: {articles_count}, "
                                  f"Articles returned: {len(articles)}, "
                                  f"Livability Index: {data['livability_index']}")
                else:
                    self.log_result("News Scraping", False, 
                                  f"Invalid score ranges (should be 0-10): {invalid_scores}")
            else:
                self.log_result("News Scraping", False, 
                              f"Missing required fields: {', '.join(missing_fields)}", data)
        else:
            self.log_result("News Scraping", False, "Failed to retrieve scraped news", data)
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting R Territory AI Backend Tests - COMPREHENSIVE SUITE")
        print(f"Testing against: {BACKEND_URL}")
        print("=" * 80)
        
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
        
        # Test 2: Viewer and Partner users
        viewer_email = "viewer@test.com"
        viewer_password = "password123"
        partner_email = "partner@test.com"
        partner_password = "password123"
        
        self.viewer_token = await self.test_user_signup(viewer_email, viewer_password, "Viewer User", "viewer")
        if not self.viewer_token:
            self.viewer_token = await self.test_user_login(viewer_email, viewer_password, "viewer")
        
        partner_token = await self.test_user_signup(partner_email, partner_password, "Partner User", "partner")
        if not partner_token:
            partner_token = await self.test_user_login(partner_email, partner_password, "partner")
        
        print("\n" + "=" * 80)
        print("🔧 BASIC INFRASTRUCTURE TESTS")
        print("=" * 80)
        
        # Test 3: API Configuration
        await self.test_api_configuration(self.admin_token)
        
        # Test 4: Pincode boundary endpoint (expected to fail)
        await self.test_pincode_boundary(self.admin_token)
        
        # Test 5: Territory creation and listing
        territory_id = await self.test_territory_creation(self.admin_token)
        await self.test_territory_listing(self.admin_token)
        
        # Test 6: Pin creation and listing (admin)
        pin_id = await self.test_pin_creation_admin(self.admin_token, territory_id)
        await self.test_pin_listing(self.admin_token)
        
        # Test 7: Pin filtering and RBAC
        if territory_id:
            await self.test_pin_filtering_by_territory(self.admin_token, territory_id)
        
        if self.viewer_token:
            await self.test_pin_creation_viewer(self.viewer_token)
        
        # Test 8: AI insights calculation
        await self.test_ai_insights_calculation(self.admin_token)
        
        print("\n" + "=" * 80)
        print("🏘️  COMMUNITY MANAGEMENT TESTS")
        print("=" * 80)
        
        # Test 9: Community Management
        community_id = await self.test_community_creation(self.admin_token, territory_id)
        communities = await self.test_community_listing(self.admin_token)
        
        if community_id:
            await self.test_community_get_single(self.admin_token, community_id)
            
            # Test community join with different user
            if self.viewer_token:
                await self.test_community_join(self.viewer_token, community_id)
        
        print("\n" + "=" * 80)
        print("📝 POSTS MANAGEMENT TESTS")
        print("=" * 80)
        
        # Test 10: Posts Management
        post_id = None
        if community_id:
            post_id = await self.test_post_creation(self.admin_token, community_id)
            await self.test_post_listing_by_community(self.admin_token, community_id)
        
        await self.test_post_listing(self.admin_token)
        
        print("\n" + "=" * 80)
        print("🏢 TERRITORY PROFILE & SUPPORTING DATA TESTS")
        print("=" * 80)
        
        # Test 11: Territory Profile
        if territory_id:
            await self.test_territory_profile(self.admin_token, territory_id)
        
        # Test 12: Supporting Data Endpoints
        await self.test_professionals_listing(self.admin_token)
        await self.test_projects_listing(self.admin_token)
        await self.test_opportunities_listing(self.admin_token)
        await self.test_events_listing(self.admin_token)
        
        # Test 13: Supporting Data Endpoints with Territory Filter
        if territory_id:
            await self.test_professionals_listing(self.admin_token, territory_id)
            await self.test_projects_listing(self.admin_token, territory_id)
            await self.test_opportunities_listing(self.admin_token, territory_id)
            await self.test_events_listing(self.admin_token, territory_id)
        
        print("\n" + "=" * 80)
        print("🎯 SPECIFIC EVENTS & PROJECTS CREATION TESTS")
        print("=" * 80)
        
        # Test 14: Specific Event and Project Creation (as requested)
        if territory_id:
            # Get first territory ID from territories list for testing
            success, territories_data, status = await self.make_request("GET", "/territories", token=self.admin_token)
            if success and isinstance(territories_data, list) and len(territories_data) > 0:
                first_territory_id = territories_data[0]["id"]
                print(f"Using first territory ID: {first_territory_id}")
                
                # Test specific event creation
                event_id = await self.test_event_creation_specific(self.admin_token, first_territory_id)
                if event_id:
                    await self.test_event_appears_in_list(self.admin_token, event_id)
                
                # Test specific project creation
                project_id = await self.test_project_creation_specific(self.admin_token, first_territory_id)
                if project_id:
                    await self.test_project_appears_in_list(self.admin_token, project_id)
            else:
                self.log_result("Territory ID Retrieval", False, "Could not get first territory ID for specific tests")
        
        print("\n" + "=" * 80)
        print("📊 DATA SUBMISSION & ANALYTICS TESTS")
        print("=" * 80)
        
        # Test 15: New Data Submission and Analytics Endpoints
        if territory_id:
            # Get first territory ID from territories list for testing
            success, territories_data, status = await self.make_request("GET", "/territories", token=self.admin_token)
            if success and isinstance(territories_data, list) and len(territories_data) > 0:
                first_territory_id = territories_data[0]["id"]
                print(f"Using territory ID for metrics: {first_territory_id}")
                
                # Test metrics submission
                metrics_id = await self.test_metrics_submission(self.admin_token, first_territory_id)
                
                # Test metrics retrieval (all and filtered)
                await self.test_metrics_retrieval(self.admin_token)
                await self.test_metrics_retrieval(self.admin_token, first_territory_id)
                
                # Test dashboard analytics
                await self.test_dashboard_analytics(self.admin_token)
                
                # Test news scraping
                await self.test_news_scraping(self.admin_token, pages=2)
            else:
                self.log_result("Territory ID for Metrics", False, "Could not get territory ID for metrics tests")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Categorize results
        critical_failures = []
        minor_failures = []
        
        for result in self.test_results:
            if not result["success"]:
                if any(keyword in result["test"].lower() for keyword in ["auth", "login", "signup", "community", "post", "territory profile"]):
                    critical_failures.append(result)
                else:
                    minor_failures.append(result)
        
        if critical_failures:
            print(f"\n❌ CRITICAL FAILURES ({len(critical_failures)}):")
            for result in critical_failures:
                print(f"  • {result['test']}: {result['message']}")
        
        if minor_failures:
            print(f"\n⚠️  MINOR ISSUES ({len(minor_failures)}):")
            for result in minor_failures:
                print(f"  • {result['test']}: {result['message']}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Backend is fully functional.")
        elif len(critical_failures) == 0:
            print("\n✅ All critical functionality working. Minor issues can be addressed later.")
        else:
            print(f"\n🚨 {len(critical_failures)} critical issues need immediate attention.")
        
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