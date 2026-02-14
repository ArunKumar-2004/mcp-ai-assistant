"""
Test script for automatic GitHub build log fetching.
Tests the new get_latest_build functionality.
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

from tools.get_latest_build import GetLatestBuildTool

async def test_get_latest_build():
    print("=" * 70)
    print("AUTOMATIC GITHUB BUILD LOG FETCHING TEST")
    print("=" * 70)
    
    # Check configuration
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    
    if not repo:
        print("\n⚠️  GITHUB_REPOSITORY not set in environment")
        print("   Set it in .env to test automatic build fetching")
        print("\n   Example:")
        print("   GITHUB_REPOSITORY=ArunKumar-2004/Wealth-Hub")
        return
    
    if not token:
        print("\n⚠️  GITHUB_TOKEN not set in environment")
        print("   Set it in .env to test automatic build fetching")
        print("\n   Example:")
        print("   GITHUB_TOKEN=ghp_your_token_here")
        return
    
    print(f"\n✅ Configuration loaded:")
    print(f"   Repository: {repo}")
    print(f"   Token: {token[:10]}... (length: {len(token)})")
    
    # Test 1: Get latest build (any workflow)
    print("\n" + "=" * 70)
    print("TEST 1: Get Latest Build (Any Workflow)")
    print("=" * 70)
    
    tool = GetLatestBuildTool()
    
    try:
        result = await tool.execute(
            repo=repo,
            include_log=False  # Don't fetch full log for this test
        )
        
        if result["success"]:
            data = result["data"]
            print(f"\n✅ Latest build found!")
            print(f"   Run ID: {data['run_id']}")
            print(f"   Workflow: {data['workflow_name']}")
            print(f"   Status: {data['status']}")
            print(f"   Conclusion: {data['conclusion']}")
            print(f"   Branch: {data['branch']}")
            print(f"   Created: {data['created_at']}")
            print(f"   Commit: {data['commit']['message'][:60]}...")
            print(f"   URL: {data['html_url']}")
            print(f"\n🤖 AI Explanation:")
            print(f"   {data['explanation']}")
            if data['conclusion'] == 'failure':
                print(f"\n💡 Root Cause:")
                print(f"   {data['root_cause']}")
                print(f"\n🔧 Suggested Fix:")
                print(f"   {data['suggested_fix']}")
        else:
            print(f"\n❌ Failed to get latest build:")
            print(f"   Error: {result['error']['message']}")
            print(f"   Explanation: {result['error']['explanation']}")
            print(f"   Suggested Fix: {result['error']['suggested_fix']}")
    except Exception as e:
        print(f"\n❌ Exception: {e}")
    
    # Test 2: Get latest build with workflow filter
    print("\n" + "=" * 70)
    print("TEST 2: Get Latest Build (Filtered by Workflow Name)")
    print("=" * 70)
    
    workflow_filter = "Next.js"  # Adjust based on your workflows
    print(f"   Filter: workflows containing '{workflow_filter}'")
    
    try:
        result = await tool.execute(
            repo=repo,
            workflow_name=workflow_filter,
            include_log=False
        )
        
        if result["success"]:
            data = result["data"]
            print(f"\n✅ Latest '{workflow_filter}' build found!")
            print(f"   Run ID: {data['run_id']}")
            print(f"   Workflow: {data['workflow_name']}")
            print(f"   Conclusion: {data['conclusion']}")
        else:
            print(f"\n⚠️  No builds found matching filter '{workflow_filter}'")
            print(f"   Try a different workflow name or check your repository")
    except Exception as e:
        print(f"\n❌ Exception: {e}")
    
    # Test 3: Get latest build with branch filter
    print("\n" + "=" * 70)
    print("TEST 3: Get Latest Build (Filtered by Branch)")
    print("=" * 70)
    
    branch_filter = "main"
    print(f"   Filter: branch = '{branch_filter}'")
    
    try:
        result = await tool.execute(
            repo=repo,
            branch=branch_filter,
            include_log=False
        )
        
        if result["success"]:
            data = result["data"]
            print(f"\n✅ Latest build on '{branch_filter}' found!")
            print(f"   Run ID: {data['run_id']}")
            print(f"   Workflow: {data['workflow_name']}")
            print(f"   Conclusion: {data['conclusion']}")
        else:
            print(f"\n⚠️  No builds found on branch '{branch_filter}'")
    except Exception as e:
        print(f"\n❌ Exception: {e}")
    
    print("\n" + "=" * 70)
    print("TESTS COMPLETE")
    print("=" * 70)
    print("\n💡 TIP: Set include_log=True to fetch and analyze full build logs!")

if __name__ == "__main__":
    asyncio.run(test_get_latest_build())
