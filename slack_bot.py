import os
import re
import time
import logging
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

slack_events_adapter = SlackEventAdapter(signing_secret, "/slack/events", flask_app)
logger.info("Slack events adapter created successfully")

# Create Slack client
client = WebClient(token=bot_token)
logger.info("Slack WebClient created successfully")

# Create handler
handler = SlackRequestHandler(app)
logger.info("Slack request handler created successfully")


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
        loading_blocks = create_loading_blocks(header_text, user_message, input_description, user_id, is_link)
        
        client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=loading_blocks,
            text="Generating response to your annoying boss... 👊"
        )
        
        response = generate(user_message, index)
        
        if not response or response.strip() == "":
            raise Exception("AI generated an empty response")
        
        final_blocks = create_final_blocks(header_text, user_message, input_description, user_id, response, index, is_link)
        
        client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=final_blocks,
            text=f"Generated response: {response}"
        )
        
        return response
    except Exception as e:
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
        raise e

@app.command("/tellboss")
def handle_tellboss_command(ack, say, command, logger, client):
    try:
        ack()
        
        user_input = command["text"]
        if not user_input or user_input.strip() == "":
            say("Usage: `/tellboss [your message or Slack message link]`\nExample: `/tellboss Gimme a raise`")
            return
        
        user_message, is_link = process_input(client, user_input)
        
        if is_link and user_message is None:
            say("❌ Please send a valid link or check again!")
            return
        
        input_description = "Message from link" if is_link else "Your Message"
        header_text = "📢 Message for Your Boss 😁"
        
        initial_response = say(text="Sending your request to AI 🤖...", blocks=[])
        
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
    except Exception as e:
        logger.error(f"Error in /tellboss command: {str(e)}")
        say(f"❌ Sorry, something went wrong: {str(e)}")

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
        </div>
    </body>
    </html>
    """

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    if request.json and "challenge" in request.json:
        return request.json["challenge"]
    
    return handler.handle(request)

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
