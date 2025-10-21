from flask import Flask

from app.config import ServiceConfig, get_config
from app.service import init_app


def create_app():
    cfg = get_config()
    app = Flask(__name__)
    init_app(app, cfg)
    return app
