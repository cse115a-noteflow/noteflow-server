from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from uuid import uuid4
from services.rag import rag_store, rag_remove, rag_query

db = firestore.client()
note_ref = db.collection('notes')

notesAPI = Blueprint('notesAPI', __name__, url_prefix='/notes')


@notesAPI.route('/', methods=['POST'])
def add():
    try:
        print("Adding note")
        id = str(uuid4())
        r = request.get_json()
        r['id'] = id
        note_ref.document(id).set(r)

        # Also store vectors in Pinecone
        rag_store(r)

        return jsonify({"success": True, "id": id, "message": f"Note added/updated successfully"}), 200
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