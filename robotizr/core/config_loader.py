from jsonmerge import Merger
import json
import os
import re


def load(files):
    schema = {
        "properties": {
            "bar": {
                "mergeStrategy": "append"
            }
        }
    }
    merger = Merger(schema)
    config = json.load(open(os.path.dirname(os.path.abspath(__file__)) + '/../resources/default-config.json'))

    for file in files:
        custom_config = json.load(open(file))
        config = merger.merge(config, custom_config)

    for source in config['source']:
        match = re.search("^%%([0-9A-Za-z_-]+)%%$", config['source'][source]['password'])
        if match:
            config['source'][source]['password'] = os.environ.get(match.group(1), '')
        match = re.search("^%%([0-9A-Za-z_-]+)%%$", config['source'][source]['username'])
        if match:
            config['source'][source]['username'] = os.environ.get(match.group(1), '')

    return config


