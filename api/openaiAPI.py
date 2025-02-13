from flask import Blueprint, request, jsonify
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Create Blueprint
openaiAPI = Blueprint('openaiAPI', __name__)

# Set OpenAI API Key
openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)

@openaiAPI.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get("message")
        print(f"Received message: {user_message}")
        
        if not user_message:
            print("Error: No message received")
            return jsonify({"success": False, "error": "Message is required"}), 400
        
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[{"role": "user", "content": user_message}]
        )
        
        bot_reply = response.choices[0].message.content
        print(f"AI Response: {bot_reply}")

        return jsonify({"success": True, "response": bot_reply}), 200
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()  # ✅ Get full error details
        print(f"OpenAI API Error:\n{error_details}")  # ✅ Print full error to terminal

        return jsonify({"success": False, "error": str(e)}), 500
