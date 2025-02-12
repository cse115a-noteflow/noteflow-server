from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from services.vectorstore_service import delete_note_vectors, save_note_vectors, retrieve_similar_notes
from services.llm_service import query_llm
from services.text_processing import chunk_notes


db = firestore.client()
note_ref = db.collection('notes')

ragAPI = Blueprint('ragAPI', __name__)

@ragAPI.route('/store', methods=['POST'])
def store():
    """Retrives note, embeds, and stores in Pinecone"""
    try:
        note_data = request.json
        
        note_id = note_data.get("id")
        
        if not note_id:
            return jsonify({"success": False, "error": "Document ID is required"}), 400
        
        # Processing the document
        title = note_data.get("title", "")
        description = note_data.get("description", "")
        owner_email = note_data.get("owner", {}).get("email", "")
        text_blocks = [" ".join(
            block["value"]
            for block in note_data.get("content", [])
            if block.get("value", "").strip()
        )]
        
        # Chunking the document
        note_chunks = chunk_notes(text_blocks, title, description, owner_email)
        
        # Create embeddings and store in Pinecone
        save_note_vectors(note_id, note_chunks)
        
        return jsonify({"success": True, "message": "Note stored in Pinecone"}), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ragAPI.route('/remove_vectors', methods=['POST'])
def remove_vectors():
    """Removes all document vectors from Pinecone by note ID."""
    try:
        data = request.json
        note_id = data.get("id")

        if not note_id:
            return jsonify({"success": False, "error": "Document ID is required"}), 400

        # Delete vectors from Pinecone
        delete_note_vectors(note_id)

        return jsonify({"success": True, "message": f"All vectors for document {note_id} removed from Pinecone"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500 

@ragAPI.route('/query', methods=['POST'])
def query_rag():
    """Handles user query using RAG pipeline."""
    try:
        data = request.json
        query = data.get("query")
        note_id = data.get("id")
        
        if not query or not note_id:
            return jsonify({"success": False, "error": "Query and document ID are required"}), 400
        
        context = retrieve_similar_notes(query, note_id, top_k = 3)
        response = query_llm(query, context)
        
        return jsonify({"success": True, "response": response}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

        