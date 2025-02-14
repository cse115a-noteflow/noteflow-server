from flask import Flask, request, Response
from flask_cors import CORS
from firebase_admin import credentials, initialize_app

cred = credentials.Certificate("api/key.json")
default_app = initialize_app(cred)


def create_app():
    app = Flask(__name__)

    args = {
        "supports_credentials": True,
        "methods": "*",
        "origins": ["http://localhost:5173"],
    }

    # Flask-CORS doesn't seem to want to handle OPTIONS requests even though
    # that's like the entire point of the library???
    # https://github.com/corydolphin/flask-cors/issues/292#issuecomment-883929183
    @app.before_request
    def basic_authentication():
        if request.method.lower() == 'options':
            
            return Response(headers={
                "Allow": "*",
                "Access-Control-Allow-Origin": args["origins"],
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": args["methods"],
                "Access-Control-Allow-Credentials": "true"
            })

    CORS(app, **args)

    app.config['SECRET_KEY'] = 'abcdefg'

    from .notesAPI import notesAPI
    from api.aiAPI import aiAPI  # Absolute import

    # Must also wrap blueprints in CORS
    CORS(notesAPI, **args)
    CORS(notesAPI, **args)

    app.register_blueprint(notesAPI, url_prefix='/notes')
    app.register_blueprint(aiAPI, url_prefix='/ai')
    return app
