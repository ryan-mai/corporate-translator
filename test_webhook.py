#!/usr/bin/env python3
"""
Test script for webhook endpoint
This script helps test the /slack/events endpoint
"""

import requests
import json
import time
import hmac
import hashlib

def test_webhook_endpoint():
    """Test the webhook endpoint with various scenarios."""
    
    base_url = "https://corporate-translator-ooco.onrender.com"
    
    print("🧪 Testing Webhook Endpoint")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test 2: Test endpoint
    print("\n2. Testing test endpoint...")
    try:
        response = requests.get(f"{base_url}/test")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test 3: Empty POST to /slack/events
    print("\n3. Testing empty POST to /slack/events...")
    try:
        response = requests.post(f"{base_url}/slack/events", data="")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test 4: Invalid JSON POST to /slack/events
    print("\n4. Testing invalid JSON POST to /slack/events...")
    try:
        response = requests.post(f"{base_url}/slack/events", data="invalid json")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test 5: Valid challenge request
    print("\n5. Testing valid challenge request...")
    try:
        challenge_data = {
            "type": "url_verification",
            "challenge": "test_challenge_123"
        }
        response = requests.post(
            f"{base_url}/slack/events", 
            json=challenge_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ Webhook testing completed!")

if __name__ == "__main__":
    test_webhook_endpoint() 