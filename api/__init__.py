from flask import Flask
from flask_cors import CORS
from firebase_admin import credentials, initialize_app

cred = credentials.Certificate("api/key.json")
default_app = initialize_app(cred)


def create_app():
    app = Flask(__name__)

    CORS(app)

    app.config['SECRET_KEY'] = 'abcdefg'

    from .userAPI import userAPI

    app.register_blueprint(userAPI, url_prefix='/note')

    return app
