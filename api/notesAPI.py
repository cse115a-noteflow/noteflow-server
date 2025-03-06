from flask import Blueprint, request, jsonify
from firebase_admin import firestore, auth
from uuid import uuid4
from services.rag import rag_store, rag_remove, rag_query
import secrets
from datetime import datetime, timedelta



db = firestore.client()
note_ref = db.collection('notes')

notesAPI = Blueprint('notesAPI', __name__, url_prefix='/notes')

@notesAPI.route('', methods=['GET'])
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
                shared_notes = note_ref.where(f'permissions.user.{uid}.permission', 'in', ['view', 'edit']).where("title", ">", query).limit(limit).start_after({"id": cursor}).stream()
            else:
                owned_notes = note_ref.where("owner", "==", uid).where("title", ">", query).limit(limit).page().stream()
                shared_notes = note_ref.where(f'permissions.user.{uid}.permission', 'in', ['view', 'edit']).where("title", ">", query).limit(limit).stream()
        else:
            # Get all notes
            if cursor:
                owned_notes = note_ref.where("owner", "==", uid).limit(limit).start_after({"id": cursor}).stream()
                shared_notes = note_ref.where(f'permissions.user.{uid}.permission', "in", ['view', 'edit']).limit(limit).start_after({"id": cursor}).stream()
            else:
                owned_notes = note_ref.where("owner", "==", uid).limit(limit).stream()
                shared_notes = note_ref.where(f'permissions.user.{uid}.permission', 'in', ['view', 'edit']).limit(limit).stream()

        
        notes = list(owned_notes) + list(shared_notes)
        notes = [note.to_dict() for note in notes]

        # To save on performance, don't return content
        for note in notes:
            note.pop("content", None)

        newCursor = notes[-1]['id'] if len(notes) == limit else None
        
        return jsonify({"success": True, "results": notes, "cursor": newCursor}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@notesAPI.route('', methods=['POST'])
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
        auth_token = request.headers.get('Authorization')
        if not auth_token:
            return jsonify({"success": False, "error": "Missing Authorization header"}), 401
        
        auth_token = auth_token.split(' ').pop()
        decoded_token = auth.verify_id_token(auth_token)
        sender_uid = decoded_token['uid']

        note = note_ref.document(id).get()

        if note.exists:
            if note.get("owner") == sender_uid or note.get('permissions.global') is not None or note.get(f'permissions.user.{sender_uid}.permission') in ['view', 'edit']:
                return jsonify({"success": True, "data": note.to_dict()}), 200

            return jsonify({"success": False, "error": f"No permission"}), 200
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
        user_permissions = r.get("user")
        global_permissions = r.get("global")

        if user_permissions is None or "global" not in r.keys():
            return jsonify({"success": False, "error": "Bad request format"}), 400
        
        # Fetch the note
        note_doc = note_ref.document(id).get()
        if not note_doc.exists:
            return jsonify({"success": False, "error": "Note not found"}), 404

        note_data = note_doc.to_dict()
        owner = note_data.get("owner", {})
        permissions = {
            "user": {},
            "global": None
        }

        # Only allow owners to share
        if sender_uid != owner:
            return jsonify({"success": False, "error": "Only the owner can share this note"}), 403

        successes = []
        failures = []

        for email, permission in user_permissions.items():
            try:
                if "@" not in email:
                    recipient_user = auth.get_user(email)
                else:
                    recipient_user = auth.get_user_by_email(email)
                recipient_uid = recipient_user.uid
                recipient_name = recipient_user.display_name
                permissions['user'][recipient_uid] = {"permission": permission, "name": recipient_name}
                successes.append(email)
            except auth.UserNotFoundError:
                failures.append(email)
            
        permissions["global"] = global_permissions

        note_ref.document(id).update({"permissions": permissions})

        return jsonify({"success": True, "successes": successes, "failures": failures, "permissions": permissions}), 200

    except auth.UserNotFoundError:
        return jsonify({"success": False, "error": "User with this email not found" + recipient_user.uid}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@notesAPI.route('/<id>/generate-share-link', methods=['POST'])
def generate_share_link(id):
    try:
        auth_token = request.headers.get('Authorization')
        if not auth_token:
            return jsonify({"success": False, "error": "Missing Authorization header"}), 401

        auth_token = auth_token.split(' ').pop()
        decoded_token = auth.verify_id_token(auth_token)
        sender_uid = decoded_token['uid']

        r = request.get_json()
        permission_level = r.get("permission", "view")  # Default to view

        # Fetch the note
        note_doc = note_ref.document(id).get()
        if not note_doc.exists:
            return jsonify({"success": False, "error": "Note not found"}), 404

        note_data = note_doc.to_dict()

        # Only owners or editors can generate a share link
        if sender_uid != note_data["owner"] and note_data["permissions"].get(sender_uid) != "edit":
            return jsonify({"success": False, "error": "You don't have permission to generate a share link"}), 403

        # Generate a unique token
        share_token = str(uuid4())

        # Store the share link in Firestore
        db.collection("shareLinks").document(share_token).set({
            "noteId": id,
            "permission": permission_level,
            "createdAt": firestore.SERVER_TIMESTAMP,
        })

        return jsonify({"success": True, "token": share_token}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@notesAPI.route('/accept-share-link', methods=['POST'])
def accept_share_link():
    try:
        auth_token = request.headers.get('Authorization')
        if not auth_token:
            return jsonify({"success": False, "error": "Missing Authorization header"}), 401

        auth_token = auth_token.split(' ').pop()
        decoded_token = auth.verify_id_token(auth_token)
        recipient_uid = decoded_token['uid']

        r = request.get_json()
        share_token = r.get("shareToken")

        print(f"[DEBUG] Received share token: {share_token}")

        if not share_token:
            print("[ERROR] Invalid share token")
            return jsonify({"success": False, "error": "Invalid share token"}), 400

        # Retrieve the token from Firestore
        token_doc = db.collection("shareLinks").document(share_token).get()
        if not token_doc.exists:
            print("[ERROR] Invalid or expired share link")

            return jsonify({"success": False, "error": "Invalid or expired share link"}), 404

        token_data = token_doc.to_dict()
        note_id = token_data["noteId"]
        permission_level = token_data["permission"]

        print(f"[DEBUG] Found token data: {token_data}")

        # Fetch the note
        note_doc = note_ref.document(note_id).get()
        if not note_doc.exists:
            print("[ERROR] Note not found")
            return jsonify({"success": False, "error": "Note not found"}), 404

        note_data = note_doc.to_dict()
        permissions = note_data.get("permissions", {})
        print(f"[DEBUG] Existing permissions: {permissions}")
        # Grant the recipient the permission
        

        permissions["user"][recipient_uid] = {
            "permission": permission_level,
            "name": decoded_token.get("name", "Unknown User")
        }

        print(f"[DEBUG] Updated permissions: {permissions}")
        note_ref.document(note_id).update({"permissions": permissions})
        print("[SUCCESS] User granted permission")
        return jsonify({"success": True, "message": f"Access granted as {permission_level}"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500