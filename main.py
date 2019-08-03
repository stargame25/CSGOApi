import re
import sys
import time
import string
import datetime
import pprint
from random import choice as rchoice
from os.path import join as path_join
from copy import deepcopy
from api import *
from countries import *
from waitress import serve
from flask import Flask, render_template, session, escape, request, json, redirect, url_for, jsonify, \
    send_from_directory, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

users = {}

default_config = {
    'api': {'api_key': None},
    'website': {"secret_key": None, 'allow_download_icons': False, 'allow_download_all_games': True, 'max_download_games': None},
    'app': {'online': 1, 'dev_mode': 1, 'threads': 16, 'version': '0.6.7'}
}

settings_template = {
    'login': {},
    'home': {'last_games_count': 2},
    'statistic': {},
    'profile': {},
    'games': {"page_size": 10, "load_icons": False},
    'settings': {}
}


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


def randomString(stringLength=32):
    letters = string.ascii_lowercase
    return ''.join(rchoice(letters) for i in range(stringLength))


def read_json_file(path, filename):
    with open(path + '\\' + filename, 'r', encoding='utf8') as file:
        return json.load(file)


def get_config():
    out = {}
    try:
        with open(config_name, "r") as conf:
            category = None
            for line in conf:
                if line.strip():
                    if re.match(r"^\[\w+\]$", line):
                        category = line.strip().replace('[', "").replace(']', "")
                        out[category] = {}
                    elif category:
                        temp = line.strip().split("=")
                        if temp[1]:
                            if temp[1].lower() in ['t', 'f']:
                                if temp[1].lower() == 't':
                                    out[category][temp[0]] = True
                                else:
                                    out[category][temp[0]] = False
                            elif temp[1].isdigit():
                                out[category][temp[0]] = int(temp[1])
                            else:
                                out[category][temp[0]] = str(temp[1])
                        else:
                            out[category][temp[0]] = None
                else:
                    category = None
        return out
    except Exception:
        generate_config()
        return get_config()


def set_config(data):
    with open(config_name, 'w') as file:
        for item in data:
            file.write(item.upper()+'\n')


def generate_config():
    config = []
    for category, section in default_config.items():
        config.append('[' + category + ']')
        for title, value in section.items():
            if value is None:
                config.append(title.strip() + '=')
            elif isinstance(value, int):
                config.append(title.strip() + '=' + str(value))
            elif isinstance(value, bool):
                if value:
                    config.append(title.strip() + '=' + 'T')
                else:
                    config.append(title.strip() + '=' + 'F')
            else:
                config.append(title.strip() + '=' + value.strip())
        config.append("")
    set_config(config)




def threads_counts(count):
    if isinstance(count, int):
        if count > 4 and count < 128:
            return count
    return 4


def str_to_datetime(string):
    return datetime.datetime.strptime(string.replace(" GMT", ""), '%Y-%m-%d %H:%M:%S')


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


def gen_temp_ban(date):
    if date:
        nowtime = datetime.datetime.utcnow()
        expire = str_to_datetime(date)
        if nowtime < expire:
            temp = expire - nowtime
            return {'days': temp.days, 'hours': temp.seconds // 3600,
                    'minutes': (temp.seconds // 60) % 60, 'seconds': (temp.seconds % 60) % 60,
                    'delta': int(time.mktime(expire.timetuple()))}
    return {}

def shuffle_games(games):
    if not games or len(games.get(gamemodes[0])) == 0:
        return games.get(gamemodes[1])
    if not games or len(games.get(gamemodes[1])) == 0:
        return games.get(gamemodes[0])
    c_index = 0
    w_index = 0
    out = []
    for i in range(len(games[gamemodes[0]]) + len(games[gamemodes[1]])):
        if c_index != len(games[gamemodes[0]]) and w_index != len(games[gamemodes[1]]):
            if str_to_datetime(games[gamemodes[0]][c_index]['info']['date']) > \
                    str_to_datetime(games[gamemodes[1]][w_index]['info']['date']):
                out.append(games[gamemodes[0]][c_index])
                c_index += 1
            else:
                out.append(games[gamemodes[1]][w_index])
                w_index += 1
        elif w_index == len(games[gamemodes[1]]):
            out.append(games[gamemodes[0]][c_index])
            c_index += 1
        elif c_index == len(games[gamemodes[0]]):
            out.append(games[gamemodes[1]][w_index])
            w_index += 1
    return out


def generate_paginator(page, max_page):
    out = []
    if page <= 3:
        for i in range(5):
            out.append(i + 1)
    elif page > max_page - 3:
        for i in range(5):
            out.append(max_page - 4 + i)
    else:
        for i in range(5):
            out.append(page - 2 + i)
    return out


config_name = "config.ini"
teams = ['terrorists', 'counter-terrorists']

# --------------------IMPORTANT--------------------#
config_ini = get_config()
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
