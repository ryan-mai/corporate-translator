# Debug Guide for "dispatch_failed" Error

## 🔍 Step-by-Step Debugging Process

### 1. Check Bot Status
Visit these URLs to verify your bot is running:
- **Homepage**: `https://corporate-translator-ooco.onrender.com/`
- **Debug Info**: `https://corporate-translator-ooco.onrender.com/debug`
- **Test Endpoint**: `https://corporate-translator-ooco.onrender.com/test`

### 2. Verify Slack App Configuration

#### A. Check Request URLs
In your Slack app settings (https://api.slack.com/apps), verify:

**Event Subscriptions:**
- Request URL: `https://corporate-translator-ooco.onrender.com/slack/events`
- Status: ✅ Verified

**Slash Commands:**
- `/tellboss` → `https://corporate-translator-ooco.onrender.com/slack/events`
- `/tldr` → `https://corporate-translator-ooco.onrender.com/slack/events`
- `/befr` → `https://corporate-translator-ooco.onrender.com/slack/events`
- `/clear` → `https://corporate-translator-ooco.onrender.com/slack/events`

**Interactive Components:**
- Request URL: `https://corporate-translator-ooco.onrender.com/slack/events`

#### B. Check Bot Token Scopes
Your bot needs these scopes:
- `commands` - for slash commands
- `chat:write` - to send messages
- `channels:history` - to read message history
- `groups:history` - to read private channel history

### 3. Test the Bot Locally

Run the test script to verify everything works locally:
```bash
python test_bot.py
```

### 4. Check Logs

The bot now has comprehensive logging. Look for these log messages when you run `/tellboss`:

**Expected Log Flow:**
```
INFO - Received Slack event request
INFO - Received /tellboss command from user U123456789
INFO - Acknowledged command
INFO - Processing user input: your message here
INFO - Processed input - message: your message here..., is_link: False
INFO - Sending initial response
INFO - Initial response sent with ts: 1234567890.123456
INFO - Starting generate_with_loading_update
INFO - Starting generate_with_loading_update for channel C123456789, ts 1234567890.123456
INFO - Created loading blocks
INFO - Updating message with loading blocks
INFO - Loading blocks updated successfully
INFO - Calling generate function
INFO - Generate function returned: As an esteemed stakeholder...
INFO - Creating final blocks
INFO - Final blocks created
INFO - Updating message with final blocks
INFO - Final blocks updated successfully
INFO - Command completed successfully
```

### 5. Common Issues and Solutions

#### Issue: "dispatch_failed" with no specific error
**Cause**: Unhandled exception in command handler
**Solution**: The bot now has comprehensive error handling and logging

#### Issue: Bot doesn't respond to commands
**Check**:
1. Bot is installed in your workspace
2. Bot has the correct permissions
3. Request URLs are correct
4. Environment variables are set

#### Issue: "Invalid token" error
**Solution**: 
1. Regenerate your bot token
2. Update the `SLACK_BOT_TOKEN` environment variable

#### Issue: "Invalid signing secret" error
**Solution**:
1. Copy the correct signing secret from your Slack app settings
2. Update the `SLACK_SIGNING_SECRET` environment variable

### 6. Manual Testing

#### Test the Translator Directly
```python
from translator import generate
result = generate("I want a raise", 0)
print(result)
```

#### Test Slack API Connection
```python
from slack_sdk import WebClient
import os

client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
response = client.auth_test()
print(response)
```

### 7. Emergency Debugging

If the bot is completely broken, you can temporarily disable AI generation:

```python
# In generate_with_loading_update function, replace:
# response = generate(user_message, index)
# with:
response = "This is a test response. AI generation temporarily disabled."
```

### 8. Check Render.com Logs

1. Go to your Render.com dashboard
2. Select your Corporate Translator service
3. Go to the "Logs" tab
4. Look for error messages when you run `/tellboss`

### 9. Verify Environment Variables

The bot will now check environment variables on startup. Make sure these are set in Render.com:

- `SLACK_BOT_TOKEN`
- `SLACK_SIGNING_SECRET` 
- `GEMINI_API_KEY`

### 10. Test Commands

Try these test commands in Slack:
- `/tellboss test message`
- `/tldr test message`
- `/befr test message`

### 11. Still Having Issues?

If you're still getting "dispatch_failed":

1. **Check the logs** - Look for specific error messages
2. **Test the endpoints** - Visit the debug URLs above
3. **Verify Slack app settings** - Double-check all URLs and permissions
4. **Try a simple message first** - Use `/tellboss hello` instead of complex text

### 12. Contact Support

If none of the above works, provide:
1. The exact error message from logs
2. Your Slack app configuration screenshots
3. The output from `python test_bot.py`
4. The response from `https://corporate-translator-ooco.onrender.com/test` 