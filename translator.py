import base64
import os
from google import genai
from google.genai import types

def generate(user_input, index):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY environment variable is not set")
        
        client = genai.Client(api_key=api_key)
        model = "gemini-2.0-flash-lite"

        corporate_prompt = f"""
Take this simple, first-person statement and rewrite it as an overly formal, verbose, and absurdly inflated corporate message spoken from the "I" perspective. 
Use excessive business jargon and buzzwords like "strategic alignment," "synergy," "value-add," "ideation bandwidth," and "paradigm shifts." 
Maintain the original meaning and the use of "I" pronouns, parodying the style of executives but keeping it first-person singular. 
Only output the transformed sentence, no explanations or formatting.

Original: {user_input}
"""

        casual_prompt = f"""
Rewrite the following overly formal, jargon‑heavy corporate message (spoken from the "we" perspective) into a longer, plain‑English statement—about 25-40 words—from the same "we" point of view.

• Strip out buzzwords such as "strategic alignment," "synergy," "value‑add," "ideation bandwidth," and "paradigms."  
• Preserve the core meaning and keep the pronoun "we."  
• Output only the rewritten text—no extra commentary or formatting.

Original: {user_input}
"""

        real_prompt = f"""
Take the following overly formal, jargon-filled corporate message and translate it into what the company is really trying to say. Here is the messsage: {user_input}. Strip away all business buzzwords, vague language, and PR spin. 
Be blunt, honest, realistic and cynical — but stay true to the actual meaning and tone. 
Focus on what leadership is *actually* saying or implying, especially if it's about making money or greed, pushing work onto employees unfairly or suggesting unpaid overtime, or protecting the company's image while disregarding the ethics. Make it all about the company so that it paints them as someone who is selfish.
Keep it short and direct. Only output the real meaning — no explanations or formatting.
"""
        
        email_prompt = f"""
Convert the following response into an email format
• Output only the rewritten text—no extra commentary or formatting.
Response: {user_input}
"""

        if index == 0:
            prompt = corporate_prompt
        elif index == 1:
            prompt = casual_prompt
        elif index == 2:
            prompt = real_prompt
        elif index == 3:
            prompt = email_prompt
        else:
            raise Exception(f"Invalid index: {index}")
            
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            max_output_tokens=150,
            response_mime_type="text/plain",
        )

        result = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            result += chunk.text
        
        if not result or result.strip() == "":
            raise Exception("AI generated an empty response")
            
        return result
        
    except Exception as e:
        print(f"Error in generate function: {str(e)}")
        raise e

if __name__ == "__main__":
    user_input = input("Input: ")
    message = generate(user_input, 2)
    print(message)