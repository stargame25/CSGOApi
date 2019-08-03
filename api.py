import os
import json
import datetime
import re
import steam.webauth as webauth
import steam.webapi as webapi
import steam.steamid as steamidapi
from steam.core.cm import CMServerList
from bs4 import BeautifulSoup as bs

user_input = input

https_steam_comm_url = "https://steamcommunity.com/"
https_steam_store_url = "https://store.steampowered.com/"
steam_api_url = "http://api.steampowered.com/"
gamemodes = ['competitive', 'wingman']
max_retries = 5


class WebAuth(webauth.WebAuth):
    def __init__(self):
        self.session = webauth.make_requests_session()

    @staticmethod
    def get_rsa(username):
        return webauth.WebAuth('', '').get_rsa_key(username)

    def get_captcha(self, gid):
        return "https://steamcommunity.com/login/rendercaptcha/?gid=%s" % gid

    def _get(self, url, **kwars):
        for domain in ['store.steampowered.com', 'help.steampowered.com', 'steamcommunity.com']:
            self.session.cookies.set('Steam_Language', "english", domain=domain)
            self.session.cookies.set('birthtime', '-3333', domain=domain)
            self.session.cookies.set('sessionid', self.session_id, domain=domain)
        return self.session.get(url, **kwars)

    def _send_login(self, username='', password='', timestamp='', captcha='',
                    captcha_gid=-1, email_code='', steam_id='', twofactor_code=''):
        data = {
            'username': username,
            "password": password,
            "emailauth": email_code,
            "emailsteamid": str(steam_id) if email_code else '',
            "twofactorcode": twofactor_code,
            "captchagid": captcha_gid,
            "captcha_text": captcha,
            "loginfriendlyname": "python-steam webauth",
            "rsatimestamp": timestamp,
            "remember_login": 'true',
            "donotcache": int(webauth.time() * 100000),
        }
        try:
            return self.session.post('https://steamcommunity.com/login/dologin/', data=data, timeout=15).json()
        except webauth.requests.exceptions.RequestException as e:
            raise webauth.HTTPError(str(e))

    def login(self, username='', password='', timestamp='', captcha='', captcha_gid=-1,
              email_code='', steam_id='', twofactor_code='', language='english'):
        resp = self._send_login(username=username, password=password, timestamp=timestamp,
                                captcha=captcha, captcha_gid=captcha_gid, email_code=email_code,
                                steam_id=steam_id, twofactor_code=twofactor_code)
        if resp['success'] and resp['login_complete']:
            self.logged_on = True
            for cookie in list(self.session.cookies):
                for domain in ['store.steampowered.com', 'help.steampowered.com', 'steamcommunity.com']:
                    self.session.cookies.set(cookie.name, cookie.value, domain=domain, secure=cookie.secure)
            self.session_id = webauth.generate_session_id()
            for domain in ['store.steampowered.com', 'help.steampowered.com', 'steamcommunity.com']:
                self.session.cookies.set('Steam_Language', language, domain=domain)
                self.session.cookies.set('birthtime', '-3333', domain=domain)
                self.session.cookies.set('sessionid', self.session_id, domain=domain)
            self._finalize_login(resp)
            return {'code': 1}
        else:
            if resp.get('captcha_needed', False):
                if resp.get('clear_password_field', False):
                    return {"code": 0, 'captcha_gid': resp['captcha_gid'],
                            'captcha_url': self.get_captcha(resp['captcha_gid'])}
                else:
                    return {"code": 4, 'captcha_gid': resp['captcha_gid'],
                            'captcha_url': self.get_captcha(resp['captcha_gid'])}
            elif resp.get('emailauth_needed', False):
                return {"code": 2, "emailsteamid": webauth.SteamID(resp['emailsteamid'])}
            elif resp.get('requires_twofactor', False):
                return {"code": 3}
            elif "too many login failures" in resp.get('message'):
                return {"code": -1}
            else:
                return {"code": 0}


class CSGOApi(object):
    def __init__(self, username, _api_key=None, _api_domain='csgohelper'):
        self.username = username
        self.webclient = None
        self.api_interface = None
        self.session_id = None
        self.api_key = _api_key
        self.api_domain = _api_domain
        self.limited = True
        self.me = {'steamid': "", 'com_link': ""}
        self.gamemodes = gamemodes
        self.team_names = ['terrorists', 'counter-terrorists']
        self.csgo_games = {self.gamemodes[0]: [], self.gamemodes[1]: []}
        self.bans = [30, 2 * 60, 24 * 60, 7 * 24 * 60]
        self.cache_names = ['games.json', 'player.json']

    @staticmethod
    def time(date):
        return datetime.datetime.strptime(date.replace("GMT", "").strip(), "%Y-%m-%d %H:%M:%S")

    @staticmethod
    def check_steam_status():
        servers_con = CMServerList()
        servers_con.bootstrap_from_dns()
        return bool(len(servers_con))

    def login_in(self, username='', password='', timestamp='', captcha='', captcha_gid=-1,
                 email_code='', steam_id='', twofactor_code='', language='english'):
        self.webclient = WebAuth()
        return self.webclient.login(username=username, password=password, timestamp=timestamp,
                                    captcha=captcha, captcha_gid=captcha_gid, email_code=email_code,
                                    steam_id=steam_id, twofactor_code=twofactor_code, language=language)

    def main(self):
        self.session_id = self.webclient.session_id
        self.me['steamid'] = str(self.webclient.steam_id.as_64)
        com_link = self.webclient._get(self.webclient.steam_id.community_url).url
        if com_link[-1] == "/":
            self.me['com_link'] = com_link
        else:
            self.me['com_link'] = com_link + "/"
        self.load_me()
        self.load_all_games()
        if not self.api_key:
            self.api_key = self.get_api_key()
            if self.api_key:
                self.api_interface = webapi.WebAPI(self.api_key)
                self.limited = False
            else:
                self.limited = True

    def get_api_key(self):
        resp = self.webclient._get("https://steamcommunity.com/dev/apikey")
        html = bs(resp.text, "html.parser")
        if html.find("div", {"id": "bodyContents_lo"}):
            return None
        if html.find("input", {"name": "Revoke"}) is not None:
            return html.find("div", {"id": "bodyContents_ex"}).find_all("p")[0].text.strip().split(' ')[1]
        else:
            reg_resp = self.webclient.session.post("https://steamcommunity.com/dev/registerkey", data={
                "domain": self.api_domain,
                "agreeToTerms": "agreed",
                "sessionid": self.session_id,
                "Submit": "Register"})
            return self.get_api_key()

    def load_new_games(self, gamemode):
        continue_token = 0
        games_count = 0
        temp = []
        while continue_token is not None:
            match_dict = self.get_games_history(gamemode, self.session_id, continue_token)
            data = self.parse_games(gamemode, match_dict['html'])
            for game in data:
                if self.check_for_new(game['info']['date'], self.csgo_games[gamemode][0]['info']['date']):
                    temp.append(game)
                    games_count += 1
                else:
                    self.csgo_games[gamemode] = temp + self.csgo_games[gamemode]
                    return
            continue_token = match_dict['continue_token']
        return

    def load_games(self, gamemode):
        continue_token = 0
        while continue_token is not None:
            match_dict = self.get_games_history(gamemode, self.session_id, continue_token)
            data = self.parse_games(gamemode, match_dict['html'])
            for game in data:
                self.csgo_games[gamemode].append(game)
            continue_token = match_dict.get('continue_token')

    def load_all_games(self):
        for mode in self.gamemodes:
            self.load_games(mode)

    def check_for_new(self, date, check_date):
        if self.time(date) > self.time(check_date):
            return True
        return False

    def extract_json(self, content):
        return json.loads(content, encoding='utf8')

    def read_json(self, filename):
        content = None
        try:
            with open(self.username + '/' + filename, encoding='utf8') as cached_games:
                content = json.load(cached_games)
        except Exception as e:
            print(e)
        return content

    def save_json(self, filename, content):
        try:
            with open(self.username + '/' + filename, 'w', encoding='utf8') as cached_player:
                json.dump(content, cached_player, ensure_ascii=False)
        except Exception as e:
            print(e)
            return False
        return True

    def get_steam_stat(self):
        resp = self.webclient._get(self.me['com_link'])
        return resp.text

    def get_player_stat(self):
        resp = self.webclient._get(self.me['com_link'] + 'gcpd/730/?tab=matchmaking')
        return resp.text

    def get_player_steamid(self, community_links):
        if isinstance(community_links, list):
            out = []
            for i in community_links:
                out.append(steamidapi.from_url(i).as_64)
            return out
        else:
            return str(steamidapi.from_url(community_links).as_64)

    def get_steam_profile_info(self, steamids):
        if isinstance(steamids, list):
            temp = ""
            for i in steamids:
                temp = temp + str(i) + ", "
            return self.api_interface.call("ISteamUser.GetPlayerSummaries", steamids=temp)['response']['players']
        else:
            return self.api_interface.call("ISteamUser.GetPlayerSummaries", steamids=steamids)['response']['players'][0]

    def get_player_ban_status(self, steamids):
        temp = ""
        if isinstance(steamids, list):
            for i in steamids:
                temp = temp + str(i) + ", "
            return self.extract_json(self.webclient._get("http://api.steampowered.com/" +
                                                         "ISteamUser/GetPlayerBans/v1/?key=" +
                                                         self.api_key + "&steamids=" + temp).text)['players']
        else:
            return self.extract_json(self.webclient._get("http://api.steampowered.com/" +
                                                         "ISteamUser/GetPlayerBans/v1/?key=" +
                                                         self.api_key + "&steamids=" + steamids).text)['players'][0]

    def get_games_history(self, gamemode, session_id, continue_token):
        gamemode = 'matchhistorywingman' if gamemode == 'wingman' else 'matchhistorycompetitive'
        for i in range(max_retries):
            try:
                resp = self.webclient._get(self.me['com_link'] + 'gcpd/730?ajax=1'
                                           + '&tab=' + gamemode + '&continue_token=' + str(continue_token)
                                           + '&sessionid=' + str(session_id))
                dict_resp = self.extract_json(resp.text)
                return dict_resp
            except json.decoder.JSONDecodeError as e:
                pass
        return None

    def load_cache(self):
        if os.path.isdir(self.username):
            if os.path.isfile(self.username + '/' + self.cache_names[0]) and \
                    os.path.isfile(self.username + '/' + self.cache_names[1]):
                self.csgo_games = self.read_json(self.cache_names[0])
                self.me = self.read_json(self.cache_names[1])
                return True
            else:
                return False
        else:
            if not os.path.isdir(self.username):
                os.mkdir(self.username)
            return False

    def save_cache(self):
        if not os.path.isdir(self.username):
            os.mkdir(self.username)
        self.save_json(self.cache_names[0], self.csgo_games)
        self.save_json(self.cache_names[1], self.me)

    def get_cheaters_stat(self, gamemode):
        if self.limited:
            return False
        for game in self.csgo_games[gamemode]:
            game['cheats'] = []
            all_players = game['stat'][self.team_names[0]] + game['stat'][self.team_names[1]]
            temp = {'date': game['info']['date'], 'steamids': []}
            for j in all_players:
                temp['steamids'].append(j['steamid'])
            resp = self.get_player_ban_status(temp['steamids'])
            for response in resp:
                ban = self.check_ban(response, temp['date'])
                if ban['banned']:
                    game['cheats'].append({**{'steamid': response['SteamId']}, **ban})

    def check_ban(self, data, date=None):
        banned = False
        VAC = False
        VAC_counts = 0
        overwatch = False
        ov_counts = 0
        after_game = None
        last_ban_date = 0
        if data['VACBanned']:
            banned = True
            VAC = True
            VAC_counts = data['NumberOfVACBans']
        if data['NumberOfGameBans'] > 0:
            banned = True
            overwatch = True
            ov_counts = data['NumberOfGameBans']
        if banned:
            last_ban_date = data['DaysSinceLastBan']
        if (VAC or overwatch) and (date is not None):
            ban_date = datetime.timedelta(days=data['DaysSinceLastBan'])
            game_date = self.time(date)
            now_date = datetime.datetime.now()
            after_game = (now_date - ban_date) > game_date
        return {"banned": banned, "VAC": VAC, "VAC_counts": VAC_counts, "overwatch": overwatch,
                "ov_counts": ov_counts, "after": after_game, "DaysSinceLastBan": last_ban_date}

    def parse_games(self, gamemode, html):
        games_set = []
        striped_html = html.strip()
        html = bs(striped_html, 'html.parser')
        games = html.find_all("tr")
        for game in games:
            columns = game.find_all("table")
            if columns:
                game_info = self.parse_game_info(columns[0])
                game_stat = self.parse_game_stat(columns[1], gamemode)
                games_set.append({"info": game_info, "stat": game_stat})
        return games_set

    def parse_game_info(self, column):
        replay_link = column.find('td', {'class': 'csgo_scoreboard_cell_noborder'})
        options = column.find_all("tr")
        game_info_dict = {}
        game_info_dict['gamemode'] = options[0].text.strip()
        game_info_dict['date'] = options[1].text.strip()
        game_info_dict['search_time'] = re.findall(r'\d+:\d+', options[2].text.strip())[0]
        game_info_dict['play_time'] = re.findall(r'\d+:\d+', options[3].text.strip())[0]
        if replay_link:
            game_info_dict['replay'] = replay_link.find('a')['href']
        return game_info_dict

    def parse_game_stat(self, data, gamemode):
        player_counts = 5 if gamemode == 'competitive' else 2
        leaderboard = data.find_all("tr")
        game_stat_dict = {}
        teams = []
        game_stat_dict['game_score'] = leaderboard[player_counts + 1].find('td').text.strip()
        for i in range(2):
            team = []
            for j in range(player_counts):
                player_stat = leaderboard[(i * (player_counts + 1)) + 1 + j].find_all("td")
                player_stat_dict = {}
                player_stat_dict['player_name'] = player_stat[0].find('a', {"class": "linkTitle"}).text.strip()
                player_stat_dict['profile_link'] = player_stat[0].find('a', {"class": "linkTitle"})['href']
                player_stat_dict['steamid'] = str(
                    steamidapi.make_steam64(player_stat[0].find('img')['data-miniprofile']))
                player_stat_dict['player_icon'] = player_stat[0].find('img')['src']
                player_stat_dict['ping'] = player_stat[1].text.strip()
                player_stat_dict['kills'] = player_stat[2].text.strip()
                player_stat_dict['assists'] = player_stat[3].text.strip()
                player_stat_dict['deaths'] = player_stat[4].text.strip()
                player_stat_dict['mvps'] = "0" if len(re.findall(r'\d+', player_stat[5].text.strip())) == 0 else \
                    re.findall(r'\d+', player_stat[5].text.strip())[0]
                player_stat_dict['hs_percent'] = player_stat[6].text.strip()
                player_stat_dict['score'] = player_stat[7].text.strip()
                team.append(player_stat_dict)
            teams.append(team)
        game_stat_dict[self.team_names[0]] = teams[0]
        game_stat_dict[self.team_names[1]] = teams[1]
        game_stat_dict['status'] = self.check_game_status(game_stat_dict)
        return game_stat_dict

    def check_game_status(self, game):
        score = game['game_score'].split(' : ')
        if score[0] == score[1]:
            return 0
        if self.find_player_team_in_game(game, self.me['steamid'])['team'] == self.team_names[0]:
            if int(score[0]) > int(score[1]):
                return 1
            else:
                return -1
        else:
            if int(score[0]) < int(score[1]):
                return 1
            else:
                return -1

    def find_player_team_in_game(self, game, steamid):
        for i in self.team_names:
            for player in game[i]:
                if steamid == player['steamid']:
                    return {'team': i}
        return None

    def check_me_ban_status(self):
        if not self.limited:
            return self.check_ban(self.get_player_ban_status(self.me['steamid']))
        else:
            # develop alternate method for check
            return {'banned': None, 'VAC': None, 'overwatch': None}

    def check_me_temp_ban_status(self):
        cooldown = {}
        csgo_profile = bs(self.get_player_stat(), 'html.parser')
        info_table = csgo_profile.find_all('table', {'class': 'generic_kv_table'})
        if len(info_table) == 3:
            cooldown_info = info_table[0].find_all('tr')[1].find_all('td')
            cooldown['expire'] = cooldown_info[0].text.strip()
            cooldown['cd_level'] = cooldown_info[1].text.strip()
        return cooldown

    def load_me(self):
        steam_profile = bs(self.get_steam_stat(), 'html.parser')
        csgo_profile = bs(self.get_player_stat(), 'html.parser')
        ban_data = self.check_me_ban_status()
        self.me['banned'] = ban_data['banned']
        self.me['VAC'] = ban_data['VAC']
        self.me['overwatch'] = ban_data['overwatch']
        self.me['name'] = steam_profile.find('span', {'class': 'actual_persona_name'}).text.strip()
        self.me['realname'] = steam_profile.find('div', {'class': 'header_real_name ellipsis'}).find('bdi').text.strip()
        if steam_profile.find('div', {'class': 'header_real_name ellipsis'}).find('img'):
            self.me['country'] = \
                re.findall(r'(\w+)',
                           steam_profile.find('div', {'class': 'header_real_name ellipsis'}).find('img')['src'])[
                    -2]
        self.me['icon'] = steam_profile.find('div', {'class': 'playerAvatarAutoSizeInner'}).find('img')['src']
        self.me['level'] = steam_profile.find('span', {'class': 'friendPlayerLevelNum'}).text.strip()
        self.me['status'] = steam_profile.find('div', {'class': 'playerAvatar'})['class'][-1]
        info_tables = csgo_profile.find_all('table', {'class': 'generic_kv_table'})
        ranks = []
        for info in info_tables[len(info_tables) - 2].find_all('tr')[1:]:
            comp_info = info.find_all('td')
            gamemode_info = {}
            gamemode_info['gamemode'] = comp_info[0].text.strip()
            gamemode_info['wins'] = comp_info[1].text.strip()
            gamemode_info['draws'] = comp_info[2].text.strip()
            gamemode_info['losses'] = comp_info[3].text.strip()
            gamemode_info['rank'] = comp_info[4].text.strip()
            gamemode_info['last_game'] = comp_info[5].text.strip().replace('GMT', '').strip()
            ranks.append(gamemode_info)
        for rank in ranks:
            gamemode = rank.pop("gamemode").lower()
            self.me[gamemode] = rank
        self.me['cooldown'] = self.check_me_temp_ban_status()

    def check_for_error(self, html):
        if html.find("p", {"class": "sectionText"}) or html.find("h3"):
            return True
        else:
            return False

    def _login_in(self, password):
        self.webclient = webauth.WebAuth(self.username).cli_login(password=password)

    def _main(self):
        self.session_id = self.webclient.session_id
        self.me['steamid'] = str(self.webclient.steam_id.as_64)
        com_link = self.webclient._get(self.webclient.steam_id.community_url).url
        if com_link[-1] == "/":
            self.me['com_link'] = com_link
        else:
            self.me['com_link'] = com_link + "/"
        print("Steam ID: " + self.me['steamid'])
        print("Link: " + self.me['com_link'])
        if not self.api_key:
            self.api_key = self.get_api_key()
            if self.api_key:
                self.api_interface = webapi.WebAPI(self.api_key)
                self.limited = False
                print(self.api_key)
            else:
                self.limited = True
                print("Limited account")
        print("Program start time: " + str(datetime.datetime.now().time()))
        if not self.load_cache():
            print("No cache")
            self.load_me()
            self.load_games(self.gamemodes[0])
            self.load_games(self.gamemodes[1])
            print("Ban check start time: " + str(datetime.datetime.now().time()))
            print("Ban statistic for competitive")
            self.get_cheaters_stat(self.gamemodes[0])
            print("Ban statistic for wingman")
            self.get_cheaters_stat(self.gamemodes[1])
            print("Ban check end time: " + str(datetime.datetime.now().time()))
            print("End of the program: " + str(datetime.datetime.now().time()))
            self.save_cache()
        else:
            print("Cache")
            self.load_new_games(self.gamemodes[0])
            self.load_new_games(self.gamemodes[1])


if __name__ == '__main__':
    username = input("username: ")
    password = input("password: ")
    apid = CSGOApi(username)
    apid._login_in(password)
    apid._main()
