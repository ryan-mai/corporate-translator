#!/usr/bin/env python3
"""
Test script to verify slash command handling
"""

import requests
import json

def test_slash_command():
    """Test the slash command endpoint with form-encoded data"""
    
    # Simulate a slash command request
    url = "http://localhost:3000/slack/events"
    
    # Form-encoded data (like what Slack sends)
    data = {
        'token': 'test_token',
        'team_id': 'T1234567890',
        'team_domain': 'testworkspace',
        'channel_id': 'C1234567890',
        'channel_name': 'test-channel',
        'user_id': 'U1234567890',
        'user_name': 'testuser',
        'command': '/tellboss',
        'text': 'test message',
        'api_app_id': 'A1234567890',
        'is_enterprise_install': 'false',
        'response_url': 'https://hooks.slack.com/commands/T1234567890/1234567890/test',
        'trigger_id': '1234567890.1234567890.test'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Slack-Request-Timestamp': '1234567890',
        'X-Slack-Signature': 'v0=test_signature'
    }
    
    try:
        response = requests.post(url, data=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing slash command handling...")
    success = test_slash_command()
    if success:
        print("✅ Test passed - slash command handling works!")
    else:
        print("❌ Test failed - check the logs for details") 