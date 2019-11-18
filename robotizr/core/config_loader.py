from jsonmerge import Merger
import json
import os


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
    return config
