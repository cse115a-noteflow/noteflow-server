from flask import Blueprint, request, jsonify
from firebase_admin import firestore

db = firestore.client()
note_ref = db.collection('notes')

userAPI = Blueprint('userAPI', __name__)


@userAPI.route('/add', methods=['POST', 'GET'])
def add():
    if request.method == 'GET':
        return jsonify({"success": False, "error": "Use POST instead"}), 405

    try:
        note_ref.document(request.json.get("id")).set(request.json)
        return jsonify({"success": True, "message": f"Note added/updated successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@userAPI.route('/get', methods=['POST'])
def get():
    try:
        note = note_ref.document(request.json.get("id")).get()

        if note.exists:
            return jsonify({"success": True, "data": note.to_dict()}), 200
        else:
            return jsonify({"success": False, "error": f"Note not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@userAPI.route('/remove', methods=['POST'])
def remove():
    try:
        note_ref.document(request.json["id"]).delete()
        return jsonify({"success": True, "message": f"Note removed successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
