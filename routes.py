from copy import deepcopy
from flask import Blueprint, request, Response, render_template, redirect, url_for, session, flash, \
    send_from_directory, send_file, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from csgoapi import GLOBAL_API_KEY, users, login_manager, sitemap, \
    settings_template, settings_permissions, settings_limitations
from csgoapi.tools import *
from csgoapi.api import *
from csgoapi.models import *

website = Blueprint('csgoapi', __name__)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('.login_view'))


@login_manager.user_loader
def load_user(username):
    if username in users.keys():
        api_object = users[username]['api']
        settings = users[username]['settings']
        if users[username]['fresh']:
            users[username]['fresh'] = False
            add_task(username, 'main', api_object.main)
        return User(username, api_object, settings)


@website.errorhandler(Exception)
def all_exception_handler(error):
    print("Error occurred, watch logs folder for details")
    logg(str(traceback.format_exc()))
    return render_template("error.html"), 500


@website.errorhandler(404)
def fourhounderfour(error):
    return redirect(url_for(".login_view"))


@website.route('/favicon.png')
def favicon():
    return send_from_directory(path_join(website.root_path, 'static'),
                               'img/favicon.png', mimetype='image/vnd.microsoft.icon')


@website.route('/')
@login_required
def index():
    return redirect(url_for('.login_view'))


@website.route(sitemap['home'])
@login_required
def home_view():
    home = {"me": current_user.api.me,
            "games": shuffle_games(current_user.api.csgo_games)[0:current_user.settings['home']['last_games_size']],
            "loading_status": generate_loading_status('home', users[current_user.username]['task'])}
    return render_template("home.html", **generate_default(current_user.api.me), **home)


@website.route(sitemap['statistics'])
@login_required
def statistic_view():
    return render_template("statistics.html", **generate_default(current_user.api.me))


@website.route(sitemap['profile'])
@login_required
def profile_view():
    return redirect(current_user.api.me.get('com_link'))


@website.route(sitemap['games'])
@login_required
def games_redirect():
    return redirect(url_for(".games_view", page=1))


@website.route(sitemap['games_pages'])
@login_required
def games_view(page=1):
    shuffled_games = shuffle_games(current_user.api.csgo_games)
    page_size = current_user.settings.get('games').get('page_size') or 10
    max_page = len(shuffled_games) // page_size + 1 if len(shuffled_games) % page_size != 0 else len(
        shuffled_games) // page_size
    if page <= 1:
        page = 1
    elif page >= max_page:
        page = max_page
    games = {"page": page,
             "page_size": page_size,
             "settings": current_user.settings.get('games'),
             "games": shuffled_games[page_size * (page - 1):page_size * page],
             "me": current_user.api.me,
             "paginator": generate_paginator(page, max_page),
             "loading_status": generate_loading_status('games', users[current_user.username]['task'])}
    return render_template("games.html", **generate_default(current_user.api.me), **games)


@website.route(sitemap['settings'], methods=['POST', 'GET'])
@login_required
def settings_view():
    if request.method == 'POST':
        data = request.get_json()
        for category in data.keys():
            if settings_permissions['settings'].get(category):
                for key in data[category].keys():
                    if key in settings_limitations.keys():
                        if isinstance(data[category][key], int):
                            if data[category][key] >= settings_limitations[key]['min'] and \
                                    data[category][key] <= settings_limitations[key]['max']:
                                users[current_user.username]['settings'][category][key] = data[category][key]
                    elif isinstance(data[category][key], bool):
                        users[current_user.username]['settings'][category][key] = bool(data[category][key])
                    else:
                        users[current_user.username]['settings'][category][key] = data[category][key]
    return render_template("settings.html", **generate_default(current_user.api.me), settings=current_user.settings,
                           loading_status=generate_loading_status('settings', users[current_user.username]['task']),
                           permissions=settings_permissions['settings'])


@website.route(sitemap['login'], methods=['POST', 'GET'])
def login_view():
    if current_user.is_authenticated:
        return redirect(url_for('.settings_view'))
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
                        settings_object = deepcopy(settings_template)
                        users[api_object.username] = {"api": api_object, "settings": settings_object,
                                                      "fresh": True, "task": AsyncTask()}
                        print(str(api_object.username) + " logged in!")
                        user = User(request.form.get("username"), api_object, settings_object)
                        login_user(user)
                return jsonify(response)
    return render_template("login.html")


@website.route('/getrsa', methods=['POST'])
def getrsa():
    if request.form.get("username") and request.form.get("username") not in users.keys():
        return jsonify(WebAuth.get_rsa(request.form.get("username")))
    return 'Error', 500


@website.route(sitemap['logout'])
@login_required
def logout_view():
    print(str(current_user.username) + " logged out!")
    if not users[current_user.username]['task'].finished:
        users[current_user.username]['task'].stop()
    users.pop(current_user.username)
    session.clear()
    logout_user()
    return redirect(url_for('.login_view'))


@website.app_template_filter()
def get_map_space(text):
    return " ".join(text.split()[1:])


@website.app_template_filter()
def get_only_date(date):
    return "-".join(reversed(date.split()[0].split("-")))


@website.app_template_filter()
def get_only_time(date):
    return ":".join(date.split()[1].split(":")[0:-1])


@website.app_template_filter()
def get_map(text):
    return "".join(text.split()[1:])


@website.app_template_filter()
def get_map(text):
    return "".join(text.split()[1:])


@website.app_template_filter()
def get_map(text):
    return "".join(text.split()[1:])


@website.app_template_filter()
def get_gamemode(text):
    if text.split(" ")[0].lower() == 'competitive':
        return 'Змагальний'
    else:
        return 'Напарники'


@website.app_template_filter()
def game_status(stat):
    if stat == -1:
        return "lose"
    elif stat == 0:
        return "draw"
    elif stat == 1:
        return "win"


@website.app_template_filter()
def game_status_text(stat):
    if stat == -1:
        return "Поразка"
    elif stat == 0:
        return "Нічия"
    elif stat == 1:
        return "Перемога"


@website.app_template_filter()
def sum_games(*args):
    arguments = args
    summ = 0
    for arg in arguments:
        if isinstance(arg, int):
            summ += arg
    return summ


@website.app_template_filter()
def get_c_rank_image(rank):
    if rank:
        return "c_" + rank
    else:
        return "c_u"


@website.app_template_filter()
def get_w_rank_image(rank):
    if rank:
        return "w_" + rank
    else:
        return "w_u"


@website.app_template_filter()
def country(code):
    if code:
        if code.upper() in countries.keys():
            return (countries.get(code.upper()).get('name').replace(" ", "-")).lower()
    return ""
