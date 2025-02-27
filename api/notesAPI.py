from flask import Blueprint, request, jsonify
from firebase_admin import firestore, auth
from uuid import uuid4
from services.rag import rag_store, rag_remove, rag_query
from datetime import datetime

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
                owned_notes = note_ref.where("owner", "==", uid).where("title", ">", query).limit(limit).start_after({"id": cursor}).stream()
                shared_notes = note_ref.where(f'permissions.{uid}', 'in', ['view', 'edit']).where("title", ">", query).limit(limit).start_after({"id": cursor}).stream()
            else:
                owned_notes = note_ref.where("owner", "==", uid).where("title", ">", query).limit(limit).page().stream()
                shared_notes = note_ref.where(f'permissions.{uid}', 'in', ['view', 'edit']).where("title", ">", query).limit(limit).stream()
        else:
            # Get all notes
            if cursor:
                owned_notes = note_ref.where("owner", "==", uid).limit(limit).start_after({"id": cursor}).stream()
                shared_notes = note_ref.where(f'permissions.{uid}', "in", ['view', 'edit']).limit(limit).start_after({"id": cursor}).stream()
            else:
                owned_notes = note_ref.where("owner", "==", uid).limit(limit).stream()
                shared_notes = note_ref.where(f'permissions.{uid}', 'in', ['view', 'edit']).limit(limit).stream()

        
        notes = list(owned_notes) + list(shared_notes)
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
        r['createdAt'] = datetime.now().timestamp()
        r['modifiedAt'] = datetime.now().timestamp()
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
        
        r['modifiedAt'] = datetime.now().timestamp()
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

@notesAPI.route('/<id>/share', methods=['POST'])
def share(id):
    try:
        auth_token = request.headers.get('Authorization')
        if not auth_token:
            return jsonify({"success": False, "error": "Missing Authorization header"}), 401
        
        auth_token = auth_token.split(' ').pop()
        decoded_token = auth.verify_id_token(auth_token)
        sender_uid = decoded_token['uid']

        # Parse request JSON
        r = request.get_json()
        recipient_email = r.get("email")
        permission_level = r.get("permission", "view")  # Default to editor

        if not recipient_email:
            return jsonify({"success": False, "error": "Recipient email required"}), 400

        # Get recipient UID from email
        recipient_user = auth.get_user_by_email(recipient_email)
        recipient_uid = recipient_user.uid

        # Fetch the note
        note_doc = note_ref.document(id).get()
        if not note_doc.exists:
            return jsonify({"success": False, "error": "Note not found"}), 404

        note_data = note_doc.to_dict()
        owner = note_data.get("owner", {})
        permissions = note_data.get("permissions", {})

        # Only allow owners to share
        if sender_uid != owner:
            return jsonify({"success": False, "error": "Only the owner can share this note"}), 403

        # Update permissions
        permissions[recipient_uid] = permission_level
        note_ref.document(id).update({"permissions": permissions})

        return jsonify({"success": True, "message": f"Note shared with {recipient_email}"}), 200

    except auth.UserNotFoundError:
        return jsonify({"success": False, "error": "User with this email not found" + recipient_user.uid}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

