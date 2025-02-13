from flask import Blueprint, request, jsonify
from firebase_admin import firestore, auth
from uuid import uuid4
from services.rag import rag_store, rag_remove, rag_query

db = firestore.client()
note_ref = db.collection('notes')

notesAPI = Blueprint('notesAPI', __name__, url_prefix='/notes')

@notesAPI.route('/', methods=['GET'])
def get_notes():
    try:
        auth_token = request.headers.get('Authorization')
        query = request.args.get('q')
        cursor = request.args.get('cursor') or None
        limit = 10

        if not auth_token:
            return jsonify({"success": False, "error": "Missing Authorization header"}), 401
        
        # Remove Bearer
        auth_token = auth_token.split(' ').pop()

        # Get uid from ID token
        decoded_token = auth.verify_id_token(auth_token)
        uid = decoded_token['uid']

        if query:
            # Search by query
            if cursor:
                notes = note_ref.where("owner", "==", uid).where("title", ">", query).limit(limit).start_after({"id": cursor}).stream()
            else:
                notes = note_ref.where("owner", "==", uid).where("title", ">", query).limit(limit).page().stream()
        else:
            # Get all notes
            if cursor:
                notes = note_ref.where("owner", "==", uid).limit(limit).start_after({"id": cursor}).stream()
            else:
                notes = note_ref.where("owner", "==", uid).limit(limit).stream()

        notes = [note.to_dict() for note in notes]

        # To save on performance, don't return content
        for note in notes:
            note.pop("content", None)

        newCursor = notes[-1]['id'] if len(notes) == limit else None
        
        return jsonify({"success": True, "results": notes, "cursor": newCursor}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@notesAPI.route('/', methods=['POST'])
def add():
    try:
        id = str(uuid4())
        r = request.get_json()
        r['id'] = id
        note_ref.document(id).set(r)

        # Also store vectors in Pinecone
        rag_store(r)

        return jsonify({"success": True, "id": id, "message": f"Note added/updated successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@notesAPI.route('/<id>', methods=['PUT'])
def put(id):
    try:
        # Todo - check permissions
        r = request.get_json()
        if r['id'] != id:
            return jsonify({"success": False, "error": "ID mismatch"}), 400
        if not note_ref.document(id).get().exists:
            return jsonify({"success": False, "error": "Note not found"}), 404
    
        # TODO: Add write permissions checks here
        
        note_ref.document(id).set(r)

        # Also store vectors in Pinecone
        rag_store(r)

        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@notesAPI.route('/<id>', methods=['GET'])
def get(id):
    try:
        note = note_ref.document(id).get()

        if note.exists:
            return jsonify({"success": True, "data": note.to_dict()}), 200
        else:
            return jsonify({"success": False, "error": f"Note not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@notesAPI.route('/<id>', methods=['DELETE'])
def remove(id):
    try:
        note_ref.document(id).delete()
        # Also remove vectors from Pinecone
        rag_remove(id)

        return jsonify({"success": True, "message": f"Note removed successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@notesAPI.route('/<id>/search', methods=['GET'])
def search(id):
    try:
        query = request.args.get('q')
        note = note_ref.document(id).get()

        if note.exists:
            context = rag_query(query, id)
            return jsonify({"success": True, "data": context}), 200
        else:
            return jsonify({"success": False, "error": f"Note not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500