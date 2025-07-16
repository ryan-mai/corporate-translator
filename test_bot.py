#!/usr/bin/env python3
"""
Test script for Corporate Translator Bot
This script helps debug potential issues with the bot functionality.
"""

import os
import sys
from translator import generate

def test_environment_variables():
    """Test if all required environment variables are set."""
    print("🔍 Checking environment variables...")
    
    required_vars = ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET", "GEMINI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)} (length: {len(value)})")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("\n✅ All environment variables are set")
        return True

def test_translator():
    """Test the translator function."""
    print("\n🔍 Testing translator function...")
    
    try:
        # Test with a simple message
        test_message = "I want a raise"
        print(f"Testing with message: '{test_message}'")
        
        result = generate(test_message, 0)
        print(f"✅ Translator result: '{result}'")
        return True
        
    except Exception as e:
        print(f"❌ Translator error: {str(e)}")
        return False

def test_slack_imports():
    """Test if all Slack-related imports work."""
    print("\n🔍 Testing Slack imports...")
    
    try:
        from slack_bolt import App
        from slack_bolt.adapter.flask import SlackRequestHandler
        from slack_sdk import WebClient
        from slackeventsapi import SlackEventAdapter
        print("✅ All Slack imports successful")
        return True
    except ImportError as e:
        print(f"❌ Slack import error: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🤖 Corporate Translator Bot - Diagnostic Test")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Slack Imports", test_slack_imports),
        ("Translator Function", test_translator),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    print(f"\n{'='*50}")
    print("📊 Test Results:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All tests passed! The bot should work correctly.")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 