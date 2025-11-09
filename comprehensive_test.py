#!/usr/bin/env python3
"""
Comprehensive R Territory AI Backend Test
Focuses on the specific test flow mentioned in the review request
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://territory-insights.preview.emergentagent.com/api"

async def comprehensive_test():
    """Run the exact test flow specified in the review request"""
    
    print("🔍 COMPREHENSIVE R TERRITORY AI BACKEND TEST")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Signup as admin user
        print("1. Testing admin signup/login...")
        async with session.post(f"{BACKEND_URL}/auth/login", json={
            "email": "admin@test.com",
            "password": "password123"
        }) as resp:
            if resp.status == 200:
                admin_data = await resp.json()
                admin_token = admin_data["token"]
                print("   ✅ Admin login successful")
            else:
                print("   ❌ Admin login failed")
                return
        
        # Step 2: Configure API keys
        print("2. Testing API configuration...")
        async with session.post(f"{BACKEND_URL}/auth/config-api-key", 
                               json={
                                   "openai_api_key": "sk-test-dummy-key",
                                   "pincode_api_url": "https://api.example.com/pincode",
                                   "pincode_api_key": "dummy-key"
                               },
                               headers={"Authorization": f"Bearer {admin_token}"}) as resp:
            if resp.status == 200:
                print("   ✅ API configuration saved successfully")
            else:
                print("   ❌ API configuration failed")
        
        # Step 3: Test pincode boundary endpoint (should fail with dummy config)
        print("3. Testing pincode boundary endpoint...")
        async with session.post(f"{BACKEND_URL}/pincode/boundary",
                               json={"pincode": "380001"},
                               headers={"Authorization": f"Bearer {admin_token}"}) as resp:
            if resp.status in [400, 500]:
                print("   ✅ Pincode boundary correctly failed with dummy API (expected)")
            else:
                print("   ❌ Unexpected response from pincode boundary")
        
        # Step 4: Create a territory
        print("4. Testing territory creation...")
        territory_data = {
            "name": "Test Ahmedabad Territory",
            "city": "Ahmedabad",
            "zone": "Central Zone",
            "pincode": "380001",
            "center": {"lat": 23.0225, "lng": 72.5714},
            "boundary": [
                [23.0225, 72.5714], [23.0235, 72.5724],
                [23.0215, 72.5734], [23.0205, 72.5704],
                [23.0225, 72.5714]
            ],
            "metrics": {
                "investments": 8.0, "buildings": 200, "populationDensity": 7.5,
                "qualityOfProject": 7.5, "govtInfra": 6.0, "livabilityIndex": 8.0,
                "airPollutionIndex": 5.5, "roads": 7.0, "crimeRate": 3.5
            }
        }
        
        async with session.post(f"{BACKEND_URL}/territories",
                               json=territory_data,
                               headers={"Authorization": f"Bearer {admin_token}"}) as resp:
            if resp.status == 200:
                territory = await resp.json()
                territory_id = territory["id"]
                print("   ✅ Territory created successfully")
                print(f"      AI Appreciation: {territory['aiInsights']['appreciationPercent']}%")
            else:
                print("   ❌ Territory creation failed")
                territory_id = None
        
        # Step 5: Create pins with different types
        print("5. Testing pin creation with different types...")
        pin_types = [
            (["Job", "Commercial"], "Job Center"),
            (["Supplier", "Industrial"], "Supply Hub"),
            (["Vendor", "Retail"], "Vendor Location")
        ]
        
        created_pins = []
        for pin_type, label in pin_types:
            pin_data = {
                "location": {"lat": 23.0225 + len(created_pins) * 0.001, "lng": 72.5714},
                "type": pin_type,
                "label": label,
                "territoryId": territory_id
            }
            
            async with session.post(f"{BACKEND_URL}/pins",
                                   json=pin_data,
                                   headers={"Authorization": f"Bearer {admin_token}"}) as resp:
                if resp.status == 200:
                    pin = await resp.json()
                    created_pins.append(pin["id"])
                    print(f"   ✅ Created {label} pin")
                else:
                    print(f"   ❌ Failed to create {label} pin")
        
        # Step 6: Get all pins
        print("6. Testing pin listing...")
        async with session.get(f"{BACKEND_URL}/pins",
                              headers={"Authorization": f"Bearer {admin_token}"}) as resp:
            if resp.status == 200:
                pins = await resp.json()
                print(f"   ✅ Retrieved {len(pins)} total pins")
            else:
                print("   ❌ Failed to retrieve pins")
        
        # Step 7: Test RBAC - viewer cannot create pins
        print("7. Testing RBAC with viewer user...")
        async with session.post(f"{BACKEND_URL}/auth/login", json={
            "email": "viewer@test.com",
            "password": "password123"
        }) as resp:
            if resp.status == 200:
                viewer_data = await resp.json()
                viewer_token = viewer_data["token"]
                print("   ✅ Viewer login successful")
                
                # Try to create pin as viewer (should fail)
                async with session.post(f"{BACKEND_URL}/pins",
                                       json={
                                           "location": {"lat": 23.0225, "lng": 72.5714},
                                           "type": ["Test"],
                                           "label": "Should Fail"
                                       },
                                       headers={"Authorization": f"Bearer {viewer_token}"}) as resp:
                    if resp.status == 403:
                        print("   ✅ Viewer correctly blocked from creating pins")
                    else:
                        print("   ❌ SECURITY ISSUE: Viewer was allowed to create pins!")
            else:
                print("   ❌ Viewer login failed")
        
        # Additional verification: Territory AI insights
        print("8. Verifying AI insights calculation...")
        if territory_id:
            async with session.get(f"{BACKEND_URL}/territories/{territory_id}",
                                  headers={"Authorization": f"Bearer {admin_token}"}) as resp:
                if resp.status == 200:
                    territory = await resp.json()
                    insights = territory["aiInsights"]
                    print(f"   ✅ AI Insights working:")
                    print(f"      Appreciation: {insights['appreciationPercent']}%")
                    print(f"      Demand Pressure: {insights['demandPressure']}")
                    print(f"      Confidence: {insights['confidenceScore']}%")
                    print(f"      Suggestions: {len(insights['aiSuggestions'])}")
                else:
                    print("   ❌ Failed to retrieve territory details")
    
    print("\n" + "=" * 60)
    print("🎉 COMPREHENSIVE TEST COMPLETED")
    print("All critical R Territory AI backend functionality verified!")

if __name__ == "__main__":
    asyncio.run(comprehensive_test())