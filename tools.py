from os import mkdir, path
import re as regex
import time
import datetime
import string
import json
from random import choice

config_types = ['default', 'template']

default_config = {
    'api': {'api_key': None},
    'website': {"secret_key": None, 'allow_download_icons': False, 'allow_download_all_games': True,
                'max_download_games': None},
    'app': {'online': 1, 'dev_mode': 1, 'threads': 16, 'celery_broker_url': 'redis://localhost:6379/0',
            'celery_result_backend': 'redis://localhost:6379/0', 'version': '0.7.1'}
}

settings_template = {
    'login': {},
    'home': {'last_games_count': 2},
    'statistic': {},
    'profile': {},
    'games': {"page_size": 10, "load_icons": False},
    'settings': {}
}


def randomString(stringLength=32):
    letters = string.ascii_lowercase
    return ''.join(choice(letters) for i in range(stringLength))


def read_json_file(path, filename):
    with open(path + '\\' + filename, 'r', encoding='utf8') as file:
        return json.load(file)


def get_config(config_name, type):
    out = {}
    try:
        with open(config_name, "r") as conf:
            category = None
            for line in conf:
                if line.strip():
                    if regex.match(r"^\[\w+\]$", line):
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
        if type in config_types:
            if type == config_types[0]:
                generate_config(config_name, default_config, True)
            elif type == config_types[1]:
                generate_config(config_name, settings_template)
            return get_config(config_name, type)
        else:
            return {}


def set_config(config_name, data, upper=False):
    with open(config_name, 'w') as file:
        for item in data:
            if upper:
                file.write(item.upper() + '\n')
            else:
                file.write(item + '\n')


def generate_config(config_name, config_dict, upper=False):
    config = []
    for category, section in config_dict.items():
        config.append('[' + category + ']')
        for title, value in section.items():
            if value is None:
                config.append(title.strip() + '=')
            elif isinstance(value, bool):
                if value:
                    config.append(title.strip() + '=' + 'T')
                else:
                    config.append(title.strip() + '=' + 'F')
            elif isinstance(value, int):
                config.append(title.strip() + '=' + str(value))
            else:
                config.append(title.strip() + '=' + value.strip())
        config.append("")
    set_config(config_name, config, upper)


def threads_counts(count):
    if isinstance(count, int):
        if count > 4 and count < 128:
            return count
    return 4


def str_to_datetime(string):
    return datetime.datetime.strptime(string.replace(" GMT", ""), '%Y-%m-%d %H:%M:%S')


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
    gamemodes = list(games.keys())
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
    if max_page == 0:
        return []
    if max_page < 5:
        for i in range(max_page):
            out.append(i)
    elif page <= 3:
        for i in range(5):
            out.append(i + 1)
    elif page > max_page - 3:
        for i in range(5):
            out.append(max_page - 4 + i)
    else:
        for i in range(5):
            out.append(page - 2 + i)
    return out


def logg(trace):
    if not path.isdir("logs"):
        mkdir("logs")
    with open('logs\\' + str(datetime.datetime.now()).replace(":", "-") + '.txt', "w") as file:
        file.write(trace)
