import sys
from os.path import join as path_join
from copy import deepcopy
from tools import *
from api import *
from countries import *
from waitress import serve
from flask import Flask, render_template, session, escape, request, json, redirect, url_for, jsonify, \
    send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

users = {}

class User(UserMixin):
    id = None
    username = None
    api = None
    settings = None

    def __init__(self, _username, _api, _settings):
        self.username = _username
        self.api = _api
        self.settings = _settings

    def get_id(self):
        return self.username


def generate_default(me):
    version = app_section.get("VERSION")
    conn = CSGOApi.check_steam_status()
    perm_ban = None
    CSGO = None
    Steam = None
    VAC = None
    overwatch = None
    expire = ""
    if me:
        if me.get('cooldown'):
            expire = me.get('cooldown').get('expire')
        if me.get('VAC'):
            VAC = "VAC"
        if me.get('overwatch'):
            overwatch = "overwatch"
    return {"version": version, "conn": conn, "perm_ban": perm_ban, "temp_ban": gen_temp_ban(expire)}

settings_template_name = "settings_template.ini"
config_name = "config.ini"
teams = ['terrorists', 'counter-terrorists']

# --------------------IMPORTANT--------------------#
config_ini = get_config(config_name, config_types[0])
settings_template = get_config(settings_template_name, config_types[1])
app_section = config_ini.get("APP") if config_ini.get("APP") else {}
api_section = config_ini.get("API") if config_ini.get("API") else {}
web_section = config_ini.get("WEBSITE") if config_ini.get("WEBSITE") else {}
GLOBAL_API_KEY = api_section.get('API_KEY') if api_section.get('API_KEY') else ''
if getattr(sys, 'frozen', False):
    template_folder = path_join(sys._MEIPASS, 'templates')
    static_folder = path_join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_view"
# --------------------IMPORTANT--------------------#


ranks = ["Silver 1", "Silver 2", "Silver 3", "Silver 4", "Silver Elite", "Silver Elite Master ",
         "Gold Nova 1", "Gold Nova 2", "Gold Nova 3", "Gold Nova Master", "Master Guardian 1 ",
         "Master Guardian 2 ", "Master Guardian Elite ", "Distinguished Master Guardian", "Legendary Eagle",
         "Legendary Eagle Master", "Supreme Master First Class ", "The Global Elite"]

sitemap = dict(login='/login', logout='/logout', home='/home', statistics='/statistics', profile='/profile',
               games='/games/<int:page>', settings='/settings', setdown='/setdown', escape="/escape")


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login_view'))


@login_manager.user_loader
def load_user(username):
    if username in users.keys():
        api_object = users[username]['api']
        settings = users[username]['settings']
        return User(username, api_object, settings)


@app.errorhandler(Exception)
def all_exception_handler(error):
    print(error)
    return render_template("error.html"), 500


@app.errorhandler(404)
def fourhounderfour(error):
    return redirect(url_for("login_view"))


@app.route('/favicon.png')
def favicon():
    return send_from_directory(path_join(app.root_path, 'static'),
                               'img/favicon.png', mimetype='image/vnd.microsoft.icon')


@app.route('/')
@login_required
def index():
    return redirect(url_for('login_view'))


@app.route(sitemap['home'])
@login_required
def home_view():
    home = {"me": current_user.api.me,
            "games": shuffle_games(current_user.api.csgo_games)[0:current_user.settings['home']['last_games_count']],
            "ranks": ranks}
    return render_template("home.html", **generate_default(current_user.api.me), **home)


@app.route(sitemap['statistics'])
@login_required
def statistic_view():
    return render_template("statistics.html", **generate_default(current_user.api.me))


@app.route(sitemap['profile'])
@login_required
def profile_view():
    return redirect(current_user.api.me.get('com_link'))


@app.route('/games')
@login_required
def games_redirect():
    return redirect(url_for("games_view", page=1))


@app.route('/games/<int:page>')
@login_required
def games_view(page=1):
    shuffled_games = shuffle_games(current_user.api.csgo_games)
    max_page = len(shuffled_games) // current_user.settings.get('games').get('page_size') + 1 if len(
        shuffled_games) % current_user.settings.get('games').get('page_size') != 0 else len(
        shuffled_games) // current_user.settings.get('games').get('page_size')
    if page <= 1:
        page = 1
    elif page >= max_page:
        page = max_page
    games = {"page": page,
             "page_size": current_user.settings.get('games').get('page_size'),
             "settings": current_user.settings.get('games'),
             "games": shuffled_games[current_user.settings.get('games').get('page_size') * (page - 1):current_user.settings.get('games').get('page_size') * page],
             "me": current_user.api.me,
             "paginator": generate_paginator(page, max_page)}
    return render_template("games.html", **generate_default(current_user.api.me), **games)


@app.route(sitemap['settings'], methods=['POST', 'GET'])
@login_required
def settings_view():
    if request.method == 'POST':
        if int(request.form.get("gamesCount")) > 0 and int(request.form.get("gamesCount")) < 6:
            current_user.settings['home']['last_games_count'] = int(request.form.get("gamesCount"))
        if request.form.get("iconLoad"):
            if request.form.get("iconLoad") == "on":
                current_user.settings['games']['load_icons'] = True
            else:
                current_user.settings['games']['load_icons'] = False
    return render_template("settings.html", **generate_default(current_user.api.me), settings=current_user.settings)


@app.route(sitemap['login'], methods=['POST', 'GET'])
def login_view():
    if current_user.is_authenticated:
        return redirect(url_for('settings_view'))
    else:
        if request.method == "POST":
            if request.form.get("username") and request.form.get("password") and request.form.get("timestamp"):
                api_object = CSGOApi(request.form.get("username"), GLOBAL_API_KEY)
                response = api_object.login_in(username=request.form.get('username'),
                                               password=request.form.get('password'),
                                               timestamp=request.form.get("timestamp"),
                                               captcha=request.form.get('captcha') or '',
                                               captcha_gid=request.form.get('captcha_gid') or -1,
                                               email_code=request.form.get('email_code') or '',
                                               steam_id=request.form.get('emailsteamid') or '',
                                               twofactor_code=request.form.get('twofactor_code') or '')
                if int(response['code']) in [1, 2, 3]:
                    if int(response['code'] == 1):
                        api_object.main()
                        settings_object = deepcopy(settings_template)
                        users[api_object.username] = {"api": api_object, "settings": settings_object}
                        print(str(api_object.username) + " logged in!")
                        user = User(request.form.get("username"), api_object, settings_object)
                        login_user(user)
                return jsonify(response)
    return render_template("login.html")


@app.route('/getrsa', methods=['POST'])
def getrsa():
    if request.form.get("username") and request.form.get("username") not in users.keys():
        return jsonify(WebAuth.get_rsa(request.form.get("username")))
    return 'Error', 500


@app.route(sitemap['logout'])
@login_required
def logout_view():
    print(str(current_user.username) + " logged out!")
    session.clear()
    users.pop(current_user.username)
    logout_user()
    return redirect(url_for('login_view'))


@app.template_filter()
def get_map_space(text):
    return " ".join(text.split()[1:])


@app.template_filter()
def get_only_date(date):
    return "-".join(reversed(date.split()[0].split("-")))


@app.template_filter()
def get_only_time(date):
    return ":".join(date.split()[1].split(":")[0:-1])


@app.template_filter()
def get_map(text):
    return "".join(text.split()[1:])


@app.template_filter()
def get_map(text):
    return "".join(text.split()[1:])


@app.template_filter()
def get_map(text):
    return "".join(text.split()[1:])


@app.template_filter()
def get_gamemode(text):
    return text.split(" ")[0]


@app.template_filter()
def game_status(stat):
    if stat == -1:
        return "lose"
    elif stat == 0:
        return "draw"
    elif stat == 1:
        return "win"


@app.template_filter()
def game_status_text(stat):
    if stat == -1:
        return "Поразка"
    elif stat == 0:
        return "Нічия"
    elif stat == 1:
        return "Виграш"


@app.template_filter()
def sum_games(*args):
    arguments = args
    summ = 0
    for arg in arguments:
        if isinstance(arg, int):
            summ += arg
    return summ


@app.template_filter()
def get_c_rank_image(rank):
    if rank:
        return "c_" + rank
    else:
        return "c_u"


@app.template_filter()
def get_w_rank_image(rank):
    if rank:
        return "w_" + rank
    else:
        return "w_u"


@app.template_filter()
def country(code):
    if code:
        if code.upper() in countries.keys():
            return (countries.get(code.upper()).get('name').replace(" ", "-")).lower()
    return ""


if __name__ == '__main__':
    key = web_section.get('SECRET_KEY')
    app.secret_key = randomString() if not key or len(key) < 10 else key
    try:
        if bool(app_section.get('ONLINE') and not app_section.get("DEV_MODE")):
            print("Server is accessible from internet")
            serve(app, host='0.0.0.0', port=8080, threads=threads_counts(app_section.get("THREADS")))
        else:
            print("Server is NOT accessible from internet")
            if bool(app_section.get("DEV_MODE")):
                app.config['DEBUG'] = bool(web_section.get("DEV_MODE"))
                app.run(port=8080)
            else:
                serve(app, port=8080)
    except Exception as e:
        print("App error, server crashed")
