# Deployment Guide

## 🚀 Deploying the Fixed Bot

### 1. Update Your Code

The bot has been updated with comprehensive error handling and logging. The main fixes include:

- ✅ **Fixed JSON parsing errors** - Now handles empty and malformed requests gracefully
- ✅ **Added detailed logging** - Every step is now logged for debugging
- ✅ **Improved error handling** - Better error messages and recovery
- ✅ **Added health check endpoints** - For monitoring bot status

### 2. Deploy to Render.com

#### Option A: Using Git (Recommended)
```bash
# Add your changes
git add .
git commit -m "Fix dispatch_failed error with improved error handling"
git push origin main
```

#### Option B: Manual Upload
1. Go to your Render.com dashboard
2. Select your Corporate Translator service
3. Go to "Settings" → "Build & Deploy"
4. Click "Manual Deploy" → "Deploy latest commit"

### 3. Verify Deployment

After deployment, check these endpoints:

- **Health Check**: `https://corporate-translator-ooco.onrender.com/health`
- **Test Endpoint**: `https://corporate-translator-ooco.onrender.com/test`
- **Debug Info**: `https://corporate-translator-ooco.onrender.com/debug`

### 4. Test the Bot

Once deployed, try these commands in Slack:

```
/tellboss hello
/tldr test message
/befr test message
```

### 5. Check Logs

Monitor the logs in Render.com:
1. Go to your service dashboard
2. Click "Logs" tab
3. Look for the detailed logging messages

**Expected Log Flow:**
```
INFO - Received Slack event request
INFO - Request content length: 1234
INFO - Request data keys: ['type', 'event', 'team_id', ...]
INFO - Received /tellboss command from user U123456789
INFO - Acknowledged command
INFO - Processing user input: hello
INFO - Processed input - message: hello..., is_link: False
INFO - Sending initial response
INFO - Initial response sent with ts: 1234567890.123456
INFO - Starting generate_with_loading_update
INFO - Created loading blocks
INFO - Loading blocks updated successfully
INFO - Calling generate function
INFO - Generate function returned: As an esteemed stakeholder...
INFO - Creating final blocks
INFO - Final blocks created
INFO - Updating message with final blocks
INFO - Final blocks updated successfully
INFO - Command completed successfully
```

### 6. Troubleshooting

#### If you still get "dispatch_failed":

1. **Check the logs** - Look for specific error messages
2. **Verify Slack app settings** - Ensure all URLs point to `/slack/events`
3. **Test the endpoints** - Visit the health and test URLs
4. **Check environment variables** - Verify all are set in Render.com

#### Common Issues:

**Issue**: Bot doesn't respond
- **Solution**: Check if the bot is installed in your workspace

**Issue**: "Invalid token" error
- **Solution**: Regenerate your bot token and update the environment variable

**Issue**: Empty responses
- **Solution**: Check your Gemini API key and quota

### 7. Environment Variables

Make sure these are set in Render.com:

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
GEMINI_API_KEY=your-gemini-api-key
```

### 8. Slack App Configuration

Verify these settings in your Slack app:

**Event Subscriptions:**
- Request URL: `https://corporate-translator-ooco.onrender.com/slack/events`

**Slash Commands:**
- `/tellboss` → `https://corporate-translator-ooco.onrender.com/slack/events`
- `/tldr` → `https://corporate-translator-ooco.onrender.com/slack/events`
- `/befr` → `https://corporate-translator-ooco.onrender.com/slack/events`
- `/clear` → `https://corporate-translator-ooco.onrender.com/slack/events`

**Bot Token Scopes:**
- `commands`
- `chat:write`
- `channels:history`
- `groups:history`

### 9. Success Indicators

You'll know the fix worked when:

- ✅ `/tellboss hello` returns a corporate-speak response
- ✅ No more "dispatch_failed" errors
- ✅ Detailed logs show the command flow
- ✅ Health check endpoint returns "healthy"

### 10. Need Help?

If you're still having issues:

1. Check the logs for specific error messages
2. Run `python test_bot.py` locally to verify everything works
3. Test the webhook endpoints manually
4. Verify all environment variables are set correctly

The updated bot should now handle the JSON parsing errors gracefully and provide much better debugging information! 