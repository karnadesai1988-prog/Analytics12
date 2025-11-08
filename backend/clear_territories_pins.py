#!/usr/bin/env python3
"""
Clear territories and pins from R Territory AI Platform database
Keeps users, comments, and other data intact
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def clear_data():
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🗑️  Clearing territories and pins from database...")
    print("=" * 60)
    
    # Count before deletion
    territories_count = await db.territories.count_documents({})
    pins_count = await db.pins.count_documents({})
    
    print(f"\nFound {territories_count} territories and {pins_count} pins")
    
    if territories_count == 0 and pins_count == 0:
        print("\n✓ Database already clean - no territories or pins to remove")
        client.close()
        return
    
    # Delete territories
    territories_result = await db.territories.delete_many({})
    print(f"✓ Deleted {territories_result.deleted_count} territories")
    
    # Delete pins
    pins_result = await db.pins.delete_many({})
    print(f"✓ Deleted {pins_result.deleted_count} pins")
    
    # Optional: Clear related data
    metrics_result = await db.metrics_history.delete_many({})
    print(f"✓ Deleted {metrics_result.deleted_count} metrics history entries")
    
    data_gathering_result = await db.data_gathering.delete_many({})
    print(f"✓ Deleted {data_gathering_result.deleted_count} data gathering entries")
    
    # Keep users and comments intact
    users_count = await db.users.count_documents({})
    comments_count = await db.comments.count_documents({})
    
    print("\n" + "=" * 60)
    print("✅ Database cleanup complete!")
    print(f"\nPreserved:")
    print(f"  • {users_count} users (login credentials intact)")
    print(f"  • {comments_count} comments")
    
    print("\n📝 You can now create fresh territories and pins")
    print("   Use pincode 380001, 380004, 380006, 380009, 380013, 380015, etc.")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(clear_data())
