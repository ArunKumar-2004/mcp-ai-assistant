"""
Test script for multi-database support (PostgreSQL, MySQL, MongoDB).
Tests connectivity checks and migration verification for all three database types.
"""
import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from services.drivers.health_driver import DatabaseDriver

async def test_database_driver():
    print("=" * 70)
    print("MULTI-DATABASE SUPPORT TEST")
    print("=" * 70)
    
    # Test connection strings for each database type
    test_cases = [
        {
            "name": "PostgreSQL",
            "url": "postgresql://user:pass@localhost:5432/testdb",
            "expected_type": "postgresql"
        },
        {
            "name": "MySQL",
            "url": "mysql://user:pass@localhost:3306/testdb",
            "expected_type": "mysql"
        },
        {
            "name": "MongoDB",
            "url": "mongodb://user:pass@localhost:27017/testdb",
            "expected_type": "mongodb"
        },
        {
            "name": "MongoDB (SRV)",
            "url": "mongodb+srv://user:pass@cluster.mongodb.net/testdb",
            "expected_type": "mongodb"
        }
    ]
    
    print("\n📋 TEST 1: Database Type Auto-Detection")
    print("=" * 70)
    for test in test_cases:
        try:
            driver = DatabaseDriver(db_url=test["url"])
            detected = driver.db_type
            status = "✅" if detected == test["expected_type"] else "❌"
            print(f"{status} {test['name']}: {detected} (expected: {test['expected_type']})")
        except Exception as e:
            print(f"❌ {test['name']}: Error - {e}")
    
    # Test with actual database URL from environment
    print("\n📋 TEST 2: Real Database Connectivity Check")
    print("=" * 70)
    
    db_url = os.environ.get("TARGET_DB_URL")
    if not db_url:
        print("⚠️  TARGET_DB_URL not set in environment")
        print("   Set it in .env to test real database connectivity")
        print("\n   Examples:")
        print("   TARGET_DB_URL=postgresql://user:pass@localhost:5432/dbname")
        print("   TARGET_DB_URL=mysql://user:pass@localhost:3306/dbname")
        print("   TARGET_DB_URL=mongodb://user:pass@localhost:27017/dbname")
    else:
        driver = DatabaseDriver(db_url=db_url)
        print(f"\n🔍 Detected database type: {driver.db_type}")
        print(f"🔗 Connection string: {db_url[:30]}...")
        
        print("\n🔄 Testing connectivity...")
        try:
            result = await driver.check_connectivity()
            
            if result["status"] == "CONNECTED":
                print(f"✅ Connection successful!")
                print(f"   Latency: {result['latency_ms']}ms")
            else:
                print(f"❌ Connection failed!")
                print(f"   Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Exception during connectivity check: {e}")
        
        print("\n🔄 Testing migration check...")
        try:
            result = await driver.check_migrations()
            
            print(f"   Migrations match: {result.get('match', False)}")
            if 'current_version' in result:
                print(f"   Current version: {result['current_version']}")
            if 'note' in result:
                print(f"   Note: {result['note']}")
        except Exception as e:
            print(f"❌ Exception during migration check: {e}")
    
    print("\n" + "=" * 70)
    print("TESTS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_database_driver())
