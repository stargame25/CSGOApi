import sys
from os.path import join as path_join
from os.path import abspath, dirname
from flask import Flask
from flask_login import LoginManager
from secrets import token_hex
from csgoapi.config import *


config_ini = get_config(config_names[0])
settings_template = get_config(config_names[1])
settings_permissions = get_config(config_names[2])
settings_limitations = get_config(config_names[3])
app_section = config_ini.get("APP") or {}
api_section = config_ini.get("API") or {}
web_section = config_ini.get("WEBSITE") or {}
GLOBAL_API_KEY = api_section.get('API_KEY')
VERSION = app_section.get("VERSION")
PORT = app_section.get("PORT") or 8080
DEBUG = app_section.get("DEV_MODE") or False
ONLINE = app_section.get('ONLINE') or False
THREADS = app_section.get("THREADS") if 4 <= (app_section.get("THREADS") or 4) <= 128 else 4
STAGE = ONLINE and not DEBUG
login_manager = LoginManager()
login_manager.login_view = 'csgoapi.login_view'
users = {}

sitemap = dict(login='/login', logout='/logout', home='/home', statistics='/statistics', profile='/profile',
               games='/games', games_pages='/games/<int:page>', settings='/settings', setdown='/setdown',
               escape="/escape")


def create_app():
    app = None
    if getattr(sys, 'frozen', False):
        template_folder = path_join(sys._MEIPASS, 'templates')
        static_folder = path_join(sys._MEIPASS, 'static')
        app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    else:
        app = Flask(__name__)
    key = web_section.get('SECRET_KEY')
    app.config['SECRET_KEY'] = key if key else token_hex(32)
    login_manager.init_app(app)
    from .routes import website
    app.register_blueprint(website)

    return app
