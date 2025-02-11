from flask import Flask
from flask_cors import CORS
from firebase_admin import credentials, initialize_app


cred = credentials.Certificate("api/noteflow-77eb6-firebase-adminsdk-fbsvc-1263da6926.json")
default_app = initialize_app(cred)


def create_app():
    app = Flask(__name__)

    CORS(app)

    app.config['SECRET_KEY'] = 'abcdefg'

    from .userAPI import userAPI
    from api.openaiAPI import openaiAPI  # Absolute import
    app.register_blueprint(userAPI, url_prefix='/note')
    app.register_blueprint(openaiAPI, url_prefix='/ai')

    return app
