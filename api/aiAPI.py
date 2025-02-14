from flask import Blueprint, request, jsonify
import openai
import os
import re
import json
from dotenv import load_dotenv
from api.notesAPI import note_ref
from services.llm_service import query_llm

# Load environment variables from .env
load_dotenv()

# Create Blueprint
aiAPI = Blueprint('aiAPI', __name__, url_prefix='/ai')

# Set OpenAI API Key
openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)

@aiAPI.route('/summarize', methods=['POST'])
def summary():
    try:
        data = request.json

        if not data or not data.get("id"):
            return jsonify({"success": False, "error": "id is required"}), 400

        note = note_ref.document(data["id"]).get()
        if not note.exists:
            return jsonify({"success": False, "error": "Note not found"}), 404
        
        note_data = note.to_dict()

        content = "\n".join([block["value"] for block in note_data.get("content", []) if block.get("value", "").strip()])

        response = query_llm("Summarize the note content above.", content, "")

        if response is None:
            return jsonify({"success": False, "error": "Error generating summary"}), 500

        return jsonify({"success": True, "data": response}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

REMOVE_FORMATTING = re.compile(r"(```json)*([^`]+)*(```)*")

@aiAPI.route('/flashcards', methods=['POST'])
def flashcards():
    try:
        data = request.json

        if not data or not data.get("id"):
            return jsonify({"success": False, "error": "id is required"}), 400

        note = note_ref.document(data["id"]).get()
        if not note.exists:
            return jsonify({"success": False, "error": "Note not found"}), 404
        
        note_data = note.to_dict()

        content = "\n".join([block["value"] for block in note_data.get("content", []) if block.get("value", "").strip()])

        response = query_llm("Create flashcards from the note content above in a JSON list using form {\"term\": \"A\", \"definition\": \"The definition of A\" }. Do not return nothing else.", content, "")

        if response is None:
            return jsonify({"success": False, "error": "Error generating flashcards"}), 500

        print(response)

        # replace backticks, newlines, and extra spaces
        response = REMOVE_FORMATTING.sub(r'\2', response).strip()
        js = json.loads(response)

        return jsonify({"success": True, "data": js}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@aiAPI.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get("message")
        print(f"Received message: {user_message}")
        
        if not user_message:
            print("Error: No message received")
            return jsonify({"success": False, "error": "Message is required"}), 400
        
        reply = query_llm(user_message, "", "")
        
        if reply is None:
            return jsonify({"success": False, "error": "Error generating response"}), 500

        return jsonify({"success": True, "response": reply}), 200
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()  # ✅ Get full error details
        print(f"OpenAI API Error:\n{error_details}")  # ✅ Print full error to terminal

        return jsonify({"success": False, "error": str(e)}), 500
