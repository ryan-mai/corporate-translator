import os
import re
import time
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from translator import generate
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier

app = App(token=os.environ["SLACK_BOT_TOKEN"])
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

signature_verifier = SignatureVerifier(os.environ.get("SLACK_SIGNING_SECRET", ""))

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
    loading_blocks = create_loading_blocks(header_text, user_message, input_description, user_id, is_link)
    
    client.chat_update(
        channel=channel_id,
        ts=ts,
        blocks=loading_blocks,
        text="Generating response to your annoying boss... 👊"
    )
    
    response = generate(user_message, index)
    
    final_blocks = create_final_blocks(header_text, user_message, input_description, user_id, response, index, is_link)
    
    client.chat_update(
        channel=channel_id,
        ts=ts,
        blocks=final_blocks,
        text=f"Generated response: {response}"
    )
    
    return response

@app.command("/tellboss")
def handle_tellboss_command(ack, say, command, logger, client):
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

@app.command("/tldr")
def handle_tldr_command(ack, say, command, logger, client):
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

@app.command("/befr")
def handle_befr_command(ack, say, command, logger, client):
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
            has_messages = response.get('has_messages', False)

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
    ack()
    message = body["actions"][0]["value"]
    user_id = body["user"]["id"]
    say(f"✅ <@{user_id}> used this message: \n\n{format_quoted_message(message)}")

@app.action("regenerate_message")
def handle_regenerate_message(ack, body, say, logger, client):
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

@app.action("email_message")
def handle_email_message(ack, body, say, logger, client):
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

@app.action("regenerate_email")
def handle_regenerate_email(ack, body, say, logger, client):
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


@flask_app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Corporate Translator Status</title>
    </head>
    <body>
        <h1>Corporate Translator Bot is up and alive and saving you from your corporate boss! 🟢</h1>
    </body>
    </html>
    """


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    if request.json and "challenge" in request.json:
        return request.json["challenge"]
    
    if not signature_verifier.is_valid(
        request.headers.get("X-Slack-Request-Timestamp", ""),
        request.headers.get("X-Slack-Signature", ""),
        request.get_data().decode("utf-8")
    ):
        return "Unauthorized", 401
    
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
