from flask import Flask
from flask_session import Session
from .config import Config

def create_app():
  app = Flask(__name__)

  app.config.from_object(Config)
  app.config['SESSION_PERMANENT'] = False
  app.config['SESSION_TYPE'] = 'filesystem'

  Session(app)

  from app.routes import api
  app.register_blueprint(api)

  return app