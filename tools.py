from os import mkdir
from os.path import isdir, join as path_join
import time
import datetime
import json
from csgoapi import base_dir, users
from csgoapi.api import CSGOApi
from csgoapi.config_templates import task_relations
from csgoapi.countries import *
from csgoapi.models import AsyncTask


def str_to_datetime(string):
    return datetime.datetime.strptime(string.replace(" GMT", ""), '%Y-%m-%d %H:%M:%S')


def read_json_file(path, filename):
    folder = path_join(base_dir, path)
    path = path_join(folder, filename)
    with open(path, 'r', encoding='utf8') as file:
        return json.load(file)


def check_threads_counts(count):
    if isinstance(count, int):
        if count > 4 and count < 128:
            return count
    return 4


def add_task(username, task, method):
    if users[username]['task'].finished:
        async_job = AsyncTask(username, task, method)
        users[username]['task'] = async_job
        async_job.setDaemon(True)
        async_job.start()


def generate_default(me):
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
    return {"version": 0, "conn": conn, "perm_ban": perm_ban, "temp_ban": gen_temp_ban(expire)}


def generate_loading_status(page, task):
    if page in task_relations.keys():
        if not task.finished:
            if task.name in task_relations[page]:
                return True
    return False


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
            out.append(i+1)
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
    if not isdir("logs"):
        mkdir("logs")
    folder = path_join(base_dir, "logs")
    path = path_join(folder, str(datetime.datetime.now()).replace(":", "-") + '.txt')
    with open(path, "w") as file:
        file.write(trace)
