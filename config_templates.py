default_config = {
    'api': {'api_key': None},
    'website': {"secret_key": None, 'allow_download_icons': False, 'allow_download_all_games': True,
                'max_download_games': None},
    'app': {'online': 1, 'dev_mode': True, 'threads': 16, 'version': '0.7.7'}
}

task_relations = {
    'home': ['main'],
    'statistic': ['main'],
    'profile': [],
    'games': ['main'],
    'settings': []
}

settings_template = {
    'home': {'last_games_size': 3},
    'statistic': {},
    'profile': {},
    'games': {"page_size": 10, "load_icons": False},
    'settings': {}
}

settings_permissions = {
    'settings': {
        'home': True,
        'games': True
    }
}

settings_limitations = {
    'page_size': {
        'max': 5,
        'min': 2
    }
}

config_types = {
    'default_config': {'data': default_config, 'setting': True},
    'settings_template': {'data': settings_template},
    'settings_permission': {'data': settings_permissions},
    'settings_limitations': {'data': settings_limitations}
}

config_names = list(config_types.keys())
