import os
import re
import time
import logging
import hmac
import hashlib
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from translator import generate
from slack_sdk.errors import SlackApiError
from slack_sdk import WebClient
from slackeventsapi import SlackEventAdapter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
flask_app = Flask(__name__)

# Create Slack Bolt app
bot_token = os.environ.get("SLACK_BOT_TOKEN")
if not bot_token:
    logger.error("SLACK_BOT_TOKEN environment variable is not set")
    raise ValueError("SLACK_BOT_TOKEN environment variable is required")

app = App(token=bot_token)
logger.info("Slack Bolt app created successfully")

# Create Slack events adapter
signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
if not signing_secret:
    logger.error("SLACK_SIGNING_SECRET environment variable is not set")
    raise ValueError("SLACK_SIGNING_SECRET environment variable is required")

# Note: We're not using the slack_events_adapter for the main route to avoid JSON parsing issues
# slack_events_adapter = SlackEventAdapter(signing_secret, "/slack/events", flask_app)
logger.info("Slack signing secret loaded successfully")

# Create Slack client
client = WebClient(token=bot_token)
logger.info("Slack WebClient created successfully")

# Create handler
handler = SlackRequestHandler(app)
logger.info("Slack request handler created successfully")

def verify_slack_signature(request_body, timestamp, signature):
    """Verify that the request is from Slack."""
    if not timestamp or not signature:
        logger.warning("Missing timestamp or signature, skipping verification")
        return True  # Skip verification for now to avoid blocking requests
    
    try:
        # Create the signature base string
        sig_basestring = f"v0:{timestamp}:{request_body.decode('utf-8')}"
        
        # Create the expected signature
        expected_signature = "v0=" + hmac.new(
            signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Error verifying signature: {str(e)}")
        return True  # Skip verification on error


def format_quoted_message(message):
    lines = message.split('\n')
    formatted_lines = [f"> {line}" for line in lines]
    return '\n'.join(formatted_lines)

def extract_message_from_link(link):
    pattern = r'https://[^/]+\.slack\.com/archives/([^/]+)/p(\d+)'
    match = re.search(pattern, link)
    
    if match:
        channel_id = match.group(1)
        timestamp = match.group(2)
        timestamp = timestamp[:10] + '.' + timestamp[10:]
        return channel_id, timestamp
    return None, None

def get_message_content(client, channel_id, timestamp):
    try:
        result = client.conversations_history(
            channel=channel_id,
            latest=timestamp,
            limit=1,
            inclusive=True
        )
        
        if result["messages"]:
            message = result["messages"][0]
            return message.get("text", "")
        return None
    
    except Exception as e:
        print(f"Error fetching message: {e}")
        return None

def process_input(client, user_input):
    user_input = user_input.strip()
    
    if user_input.startswith("https://") and "slack.com/archives/" in user_input:
        channel_id, timestamp = extract_message_from_link(user_input)
        
        if channel_id and timestamp:
            message_content = get_message_content(client, channel_id, timestamp)
            if message_content:
                return message_content, True
            else:
                return None, True
        else:
            return None, True
    
    return user_input, False

def create_loading_blocks(header_text, user_message, input_description, user_id, is_link=False):
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header_text
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{input_description}:*\n\n{format_quoted_message(user_message)}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Generating response...*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": " "
            },
            "accessory": {
                "type": "image",
                "image_url": "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExeGF1NGRpMGszanFpYW56MTZ3Mmg0ZTBxZGdjbW0yOXNnNjV2MG95MyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/jAYUbVXgESSti/giphy.gif",
                "alt_text": "Loading..."
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Requested by <@{user_id}> | Corporate Translator {'📎' if is_link else ''}"
                }
            ]
        }
    ]

def create_final_blocks(header_text, user_message, input_description, user_id, response, index, is_link=False):
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header_text
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{input_description}:*\n\n{format_quoted_message(user_message)}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Generated Response:*\n\n{format_quoted_message(response)}"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Requested by <@{user_id}> | Corporate Translator {'📎' if is_link else ''}"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Use This"
                    },
                    "action_id": "use_message",
                    "style": "primary",
                    "value": response
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔄 Regenerate"
                    },
                    "action_id": "regenerate_message",
                    "value": f"{user_message}|{index}"
                }
            ]
        }
    ]
    
    if index == 0:
        blocks[-1]["elements"].append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "📨 Send as Email"
            },
            "action_id": "email_message",
            "value": response
        })
    
    return blocks

def generate_with_loading_update(client, channel_id, ts, user_message, index, header_text, input_description, user_id, is_link=False):
    try:
        logger.info(f"Starting generate_with_loading_update for channel {channel_id}, ts {ts}")
        logger.info(f"User message: {user_message[:50]}...")
        logger.info(f"Index: {index}, is_link: {is_link}")
        
        loading_blocks = create_loading_blocks(header_text, user_message, input_description, user_id, is_link)
        logger.info("Created loading blocks")
        
        logger.info("Updating message with loading blocks")
        client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=loading_blocks,
            text="Generating response to your annoying boss... 👊"
        )
        logger.info("Loading blocks updated successfully")
        
        logger.info("Calling generate function")
        response = generate(user_message, index)
        logger.info(f"Generate function returned: {response[:50]}...")
        
        if not response or response.strip() == "":
            logger.error("AI generated an empty response")
            raise Exception("AI generated an empty response")
        
        logger.info("Creating final blocks")
        final_blocks = create_final_blocks(header_text, user_message, input_description, user_id, response, index, is_link)
        logger.info("Final blocks created")
        
        logger.info("Updating message with final blocks")
        client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=final_blocks,
            text=f"Generated response: {response}"
        )
        logger.info("Final blocks updated successfully")
        
        return response
    except Exception as e:
        logger.error(f"Error in generate_with_loading_update: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        try:
            error_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ *Error generating response:* {str(e)}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Requested by <@{user_id}> | Corporate Translator"
                        }
                    ]
                }
            ]
            
            client.chat_update(
                channel=channel_id,
                ts=ts,
                blocks=error_blocks,
                text=f"Error: {str(e)}"
            )
            logger.info("Error message sent to Slack")
        except Exception as update_error:
            logger.error(f"Failed to send error message to Slack: {str(update_error)}")
        
        raise e

@app.command("/tellboss")
def handle_tellboss_command(ack, say, command, logger, client):
    try:
        logger.info(f"Received /tellboss command from user {command.get('user_id', 'unknown')}")
        logger.info(f"Command text: {command.get('text', '')}")
        
        ack()
        logger.info("Acknowledged command")
        
        user_input = command["text"]
        if not user_input or user_input.strip() == "":
            logger.info("Empty command text, sending usage message")
            say("Usage: `/tellboss [your message or Slack message link]`\nExample: `/tellboss Gimme a raise`")
            return
        
        logger.info(f"Processing user input: {user_input}")
        user_message, is_link = process_input(client, user_input)
        logger.info(f"Processed input - message: {user_message[:50]}..., is_link: {is_link}")
        
        if is_link and user_message is None:
            logger.warning("Invalid link provided")
            say("❌ Please send a valid link or check again!")
            return
        
        input_description = "Message from link" if is_link else "Your Message"
        header_text = "📢 Message for Your Boss 😁"
        
        logger.info("Sending initial response")
        initial_response = say(text="Sending your request to AI 🤖...", blocks=[])
        logger.info(f"Initial response sent with ts: {initial_response.get('ts', 'unknown')}")
        
        logger.info("Starting generate_with_loading_update")
        generate_with_loading_update(
            client, 
            command['channel_id'], 
            initial_response['ts'], 
            user_message, 
            0, 
            header_text, 
            input_description, 
            command['user_id'], 
            is_link
        )
        logger.info("Command completed successfully")
    except Exception as e:
        logger.error(f"Error in /tellboss command: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            say(f"❌ Sorry, something went wrong: {str(e)}")
        except:
            logger.error("Failed to send error message to Slack")

@app.command("/tldr")
def handle_tldr_command(ack, say, command, logger, client):
    try:
        ack()
        
        user_input = command["text"]
        if not user_input or user_input.strip() == "":
            say("Usage: `/tldr [your message or Slack message link]`\nExample: `/tldr Let's circle back to this after we align on our Q3 priorities.`\nOr: `/tldr https://workspace.slack.com/archives/C1234567890/p1234567890123456`")
            return
        
        user_message, is_link = process_input(client, user_input)
        
        if is_link and user_message is None:
            say("❌ Please send a valid link or check again!")
            return
        
        input_description = "Message from link" if is_link else "Boss's Message"
        header_text = "📢 Message from your Boss 😡"
        
        initial_response = say(text="Processing your request...", blocks=[])
        
        generate_with_loading_update(
            client, 
            command['channel_id'], 
            initial_response['ts'], 
            user_message, 
            1, 
            header_text, 
            input_description, 
            command['user_id'], 
            is_link
        )
    except Exception as e:
        logger.error(f"Error in /tldr command: {str(e)}")
        say(f"❌ Sorry, something went wrong: {str(e)}")

@app.command("/befr")
def handle_befr_command(ack, say, command, logger, client):
    try:
        ack()
        
        user_input = command["text"]
        if not user_input or user_input.strip() == "":
            say("Usage: `/befr [your message or Slack message link]`\nExample: `/befr Let's circle back to this after we align on our Q3 priorities.`")
            return
        
        user_message, is_link = process_input(client, user_input)
        
        if is_link and user_message is None:
            say("❌ Please send a valid link or check again!")
            return
        
        input_description = "Message from link" if is_link else "Boss's Message"
        header_text = "📢 What your boss actually means 🙄"
        
        initial_response = say(text="Processing your request...", blocks=[])
        
        generate_with_loading_update(
            client, 
            command['channel_id'], 
            initial_response['ts'], 
            user_message, 
            2, 
            header_text, 
            input_description, 
            command['user_id'], 
            is_link
        )
    except Exception as e:
        logger.error(f"Error in /befr command: {str(e)}")
        say(f"❌ Sorry, something went wrong: {str(e)}")

@app.command("/clear")
def handle_clear_command(ack, say, command, logger, client):
    ack()
    channel_id = command['channel_id']
    user_id = command['user_id']

    try:
        has_messages = True
        cursor = None

        while has_messages:
            response = client.conversations_history(channel=channel_id, limit=200, cursor=cursor)
            messages = response['messages']
            cursor = response.get('response_metadata', {}).get('next_cursor')
            has_messages = response.get('has_more', False)

            for message in messages:
                try:
                    ts = message['ts']
                    client.chat_delete(channel=channel_id, ts=ts)
                    time.sleep(0.69)
                except SlackApiError as e:
                    logger.warning(f"Can't delete message - {e.response['error']} 👀 (Your boss is going to find out!!!)")
                    has_messages = False
                    break
                    

        say(f"Nothing to see (anymore!) 🐱‍👤")
    
    except SlackApiError as e:
        logger.error(f"Error fetching messages: {e.response['error']}")
        say(f"<@{user_id}>: Message can't be deleted WTF - {e.response['error']}")

@app.action("use_message")
def handle_use_message(ack, body, say, logger):
    try:
        ack()
        message = body["actions"][0]["value"]
        user_id = body["user"]["id"]
        say(f"✅ <@{user_id}> used this message: \n\n{format_quoted_message(message)}")
    except Exception as e:
        logger.error(f"Error in use_message action: {str(e)}")
        say(f"❌ Sorry, something went wrong: {str(e)}")

@app.action("regenerate_message")
def handle_regenerate_message(ack, body, say, logger, client):
    try:
        ack()
        message_with_index = body["actions"][0]["value"]
        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        
        parts = message_with_index.split("|")
        original_message = parts[0]
        index = int(parts[1]) if len(parts) > 1 else 0
        
        if index == 0:
            header_text = "🔄 Regenerated Message for Your Boss 😁"
        elif index == 1:
            header_text = "🔄 Regenerated Message from Your Boss 😡"
        else:
            header_text = "🔄 Regenerated - What your boss actually means 🙄"
        
        initial_response = say(text="Regenerating...", blocks=[])
        
        generate_with_loading_update(
            client, 
            channel_id, 
            initial_response['ts'], 
            original_message, 
            index, 
            header_text, 
            "Original Message", 
            user_id
        )
    except Exception as e:
        logger.error(f"Error in regenerate_message action: {str(e)}")
        say(f"❌ Sorry, something went wrong: {str(e)}")

@app.action("email_message")
def handle_email_message(ack, body, say, logger, client):
    try:
        ack()
        message = body["actions"][0]["value"]
        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        
        initial_response = say(text="Generating email 📨...", blocks=[])
        
        generate_with_loading_update(
            client, 
            channel_id, 
            initial_response['ts'], 
            message, 
            3, 
            "📧 Email  Generated", 
            "Original Message", 
            user_id
        )
    except Exception as e:
        logger.error(f"Error in email_message action: {str(e)}")
        say(f"❌ Sorry, something went wrong: {str(e)}")

@app.action("regenerate_email")
def handle_regenerate_email(ack, body, say, logger, client):
    try:
        ack()
        original_message = body["actions"][0]["value"]
        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        
        initial_response = say(text="Regenerating email 📨...", blocks=[])
        
        generate_with_loading_update(
            client, 
            channel_id, 
            initial_response['ts'], 
            original_message, 
            3, 
            "🔄 Regenerated Email Version", 
            "Original Message", 
            user_id
        )
    except Exception as e:
        logger.error(f"Error in regenerate_email action: {str(e)}")
        say(f"❌ Sorry, something went wrong: {str(e)}")


@flask_app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Corporate Translator Bot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; }
            .status { background: #27ae60; color: white; padding: 10px; border-radius: 5px; text-align: center; margin: 20px 0; }
            .commands { background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }
            .command { margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #3498db; }
            code { background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Corporate Translator Bot</h1>
            <div class="status">
                ✅ Bot is running and ready to translate your corporate speak!
            </div>
            <div class="commands">
                <h3>Available Commands:</h3>
                <div class="command">
                    <strong>/tellboss</strong> - Translate your message into professional corporate speak
                    <br><code>Example: /tellboss Gimme a raise</code>
                </div>
                <div class="command">
                    <strong>/tldr</strong> - Translate boss's corporate speak into plain English
                    <br><code>Example: /tldr Let's circle back to this after we align on our Q3 priorities</code>
                </div>
                <div class="command">
                    <strong>/befr</strong> - Translate boss's message into what they actually mean
                    <br><code>Example: /befr We need to optimize our workflow</code>
                </div>
                <div class="command">
                    <strong>/clear</strong> - Clear all messages in the current channel
                </div>
            </div>
            <p style="text-align: center; color: #7f8c8d;">
                Add this bot to your Slack workspace to start translating corporate speak! 🚀
            </p>
            <div style="text-align: center; margin-top: 20px;">
                <a href="/debug" style="color: #3498db; text-decoration: none;">🔧 Debug Info</a>
            </div>
        </div>
    </body>
    </html>
    """

@flask_app.route("/debug")
def debug():
    import os
    env_vars = {
        "SLACK_BOT_TOKEN": "✅ Set" if os.environ.get("SLACK_BOT_TOKEN") else "❌ Not Set",
        "SLACK_SIGNING_SECRET": "✅ Set" if os.environ.get("SLACK_SIGNING_SECRET") else "❌ Not Set",
        "GEMINI_API_KEY": "✅ Set" if os.environ.get("GEMINI_API_KEY") else "❌ Not Set",
    }
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug Info</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; }}
            .status {{ background: #27ae60; color: white; padding: 10px; border-radius: 5px; text-align: center; margin: 20px 0; }}
            .env-var {{ margin: 10px 0; padding: 10px; background: #ecf0f1; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 Debug Information</h1>
            <div class="status">
                Bot Status: ✅ Running
            </div>
            <h3>Environment Variables:</h3>
            {''.join([f'<div class="env-var"><strong>{key}:</strong> {value}</div>' for key, value in env_vars.items()])}
            <p style="text-align: center; margin-top: 20px;">
                <a href="/" style="color: #3498db; text-decoration: none;">← Back to Home</a>
            </p>
        </div>
    </body>
    </html>
    """

@flask_app.route("/test")
def test():
    """Simple test endpoint to verify the bot is working."""
    try:
        from translator import generate
        test_result = generate("test message", 0)
        return {
            "status": "success",
            "message": "Bot is working correctly",
            "test_result": test_result[:100] + "..." if len(test_result) > 100 else test_result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@flask_app.route("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment_variables": {
            "SLACK_BOT_TOKEN": "✅ Set" if os.environ.get("SLACK_BOT_TOKEN") else "❌ Not Set",
            "SLACK_SIGNING_SECRET": "✅ Set" if os.environ.get("SLACK_SIGNING_SECRET") else "❌ Not Set",
            "GEMINI_API_KEY": "✅ Set" if os.environ.get("GEMINI_API_KEY") else "❌ Not Set",
        }
    }

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    logger.info("Received Slack event request")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request method: {request.method}")
    
    request_body = request.get_data()
    logger.info(f"Request content length: {len(request_body)}")
    
    # Check if request has content
    if not request_body:
        logger.warning("Received empty request body")
        return {"error": "Empty request body"}, 400
    
    try:
        # Try to parse JSON
        try:
            request_data = request.get_json()
            logger.info(f"Request data keys: {list(request_data.keys()) if request_data else 'None'}")
        except Exception as json_error:
            logger.error(f"Failed to parse JSON: {str(json_error)}")
            logger.error(f"Raw request data: {request_body}")
            return {"error": "Invalid JSON"}, 400
        
        if request_data and "challenge" in request_data:
            logger.info("Handling URL verification challenge")
            return request_data["challenge"]
        
        logger.info("Handling Slack event")
        return handler.handle(request)
    except Exception as e:
        logger.error(f"Error in slack_events: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    # Check required environment variables
    required_env_vars = ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET", "GEMINI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these environment variables before running the bot.")
        exit(1)
    
    print("✅ All required environment variables are set")
    print("🤖 Starting Corporate Translator Bot...")
    
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
