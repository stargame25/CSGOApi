import re as regex
from os import mkdir
from os.path import isdir, dirname, abspath, join as path_join
from csgoapi.config_templates import *

base_dir = abspath(dirname(__file__))
folder = path_join(base_dir, "configs")

def get_config(config_name):
    out = {}
    if not isdir("configs"):
        mkdir("configs")
    try:
        print(path_join(folder, config_name + '.ini'))
        with open(path_join(folder, config_name + '.ini'), "r") as conf:
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
        if config_name in config_types.keys():
            generate_config(config_name, config_types[config_name].get('data'),
                            bool(config_types[config_name].get('setting')))
            return get_config(config_name)
        else:
            return {}


def set_config(config_name, data, upper=False):
    with open(path_join(folder, config_name + '.ini'), 'w') as file:
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
