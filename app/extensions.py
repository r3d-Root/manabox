from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from flask_smorest import Api

db = SQLAlchemy()
oauth = OAuth()
smorest_api = Api()