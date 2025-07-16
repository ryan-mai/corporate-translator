# Troubleshooting Guide

## Common Issues and Solutions

### 1. "dispatch_failed" Error

This error typically occurs when there's an unhandled exception in the Slack command handler. Here are the most common causes and solutions:

#### Environment Variables
Make sure all required environment variables are set:
```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_SIGNING_SECRET="your-signing-secret"
export GEMINI_API_KEY="your-gemini-api-key"
```

#### Test Environment Variables
Run the test script to check if everything is set up correctly:
```bash
python test_bot.py
```

#### Check Bot Permissions
Ensure your Slack bot has the following scopes:
- `commands` - for slash commands
- `chat:write` - to send messages
- `channels:history` - to read message history
- `groups:history` - to read private channel history

#### Check Command Registration
Make sure the `/tellboss` command is properly registered in your Slack app settings:
1. Go to your Slack app settings
2. Navigate to "Slash Commands"
3. Ensure `/tellboss` is registered with the correct request URL

### 2. API Key Issues

#### Gemini API Key
- Verify your Gemini API key is valid
- Check if you have sufficient quota
- Test the API key directly:
```python
from translator import generate
result = generate("test message", 0)
print(result)
```

### 3. Network Issues

#### Check Connectivity
- Ensure your bot can reach Slack's API
- Check if your server can reach Google's Gemini API
- Verify firewall settings

### 4. Logs and Debugging

#### Enable Debug Logging
The bot now includes comprehensive error handling and logging. Check the logs for specific error messages.

#### Common Error Messages

**"GEMINI_API_KEY environment variable is not set"**
- Set the `GEMINI_API_KEY` environment variable

**"AI generated an empty response"**
- The Gemini API returned an empty response
- Try regenerating the message

**"Invalid index"**
- Internal error in the bot logic
- Contact support

### 5. Testing Steps

1. **Run the test script:**
   ```bash
   python test_bot.py
   ```

2. **Test the translator directly:**
   ```bash
   python translator.py
   ```

3. **Check environment variables:**
   ```bash
   echo $SLACK_BOT_TOKEN
   echo $SLACK_SIGNING_SECRET
   echo $GEMINI_API_KEY
   ```

### 6. Recent Fixes

The following improvements have been made to prevent "dispatch_failed" errors:

- ✅ Added comprehensive error handling to all command handlers
- ✅ Added error handling to the `generate_with_loading_update` function
- ✅ Added error handling to the `generate` function in translator.py
- ✅ Added environment variable validation
- ✅ Added startup logging for better debugging
- ✅ Created a test script for diagnostics

### 7. Still Having Issues?

If you're still experiencing the "dispatch_failed" error:

1. Check the bot logs for specific error messages
2. Run `python test_bot.py` and share the output
3. Verify all environment variables are set correctly
4. Test the `/tellboss` command with a simple message first

### 8. Emergency Fallback

If the bot is completely broken, you can temporarily disable the AI functionality by commenting out the `generate` call in the `generate_with_loading_update` function and returning a static message for testing. 