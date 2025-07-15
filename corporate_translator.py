# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types


def generate(input):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.0-flash-lite"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"Take this casual or workplace sentence and rewrite it using absurdly exaggerated corporate jargon and business buzzwords. Use overly formal, verbose language with excessive complexity, parodying the way executives might speak in a boardroom. Lean into phrases like 'strategic alignment,' 'synergy,' 'value-add,' 'ideation bandwidth,' and 'paradigm shifts.' The result should sound ridiculous but still convey the original meaning. Only output the corporate translation — no explanation or formatting. Original: {input}"),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        max_output_tokens=100,
        response_mime_type="text/plain",
    )

    result = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        result += chunk.text
    return result

if __name__ == "__main__":
    user_input = input("Enter your message to your boss: ")
    generate(user_input)