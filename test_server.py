#!/usr/bin/env python3
"""
Quick test script to verify the FastAPI server can start.
"""

import asyncio
import sys
from contextlib import asynccontextmanager


async def test_server_startup():
    """Test that the server can start up properly."""
    try:
        from app.main import app

        print("✅ FastAPI app imported successfully")

        # Test that we can create a test client
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Test basic endpoints
        response = client.get("/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False

        response = client.get("/api/v1/health")
        if response.status_code == 200:
            print("✅ Health check endpoint working")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False

        print("✅ All basic tests passed!")
        print("\nTo start the development server, run:")
        print("  uvicorn app.main:app --reload")
        print("\nOr with the provided script:")
        print("  python app/main.py")

        return True

    except Exception as e:
        print(f"❌ Error during server test: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_server_startup())
    sys.exit(0 if success else 1)
