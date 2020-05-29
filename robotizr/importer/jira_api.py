import requests
from requests.auth import HTTPBasicAuth
import logging


class JiraApi(object):

    def __init__(self, config):
        self._config = config

    def update_issue(self, issue_key, fields_set, fields_add):

        fields = {}
        self._define_fields(fields, "set", fields_set)
        self._define_fields(fields, "add", fields_add)

        logging.info("Updating issue %s: %s", issue_key, fields)

        json = {
            'update': fields
        }

        r = requests.put(self._config['server'] + '/rest/api/2/issue/' + issue_key,
                         auth=HTTPBasicAuth(self._config['username'], self._config['password']),
                         json=json)
        if r.status_code == 204:
            logging.info("Issue %s successfully updated", issue_key)
        else:
            logging.error("%s: %s", r.status_code, r.text)

    def _define_fields(self, fields, action, args_fields):
        if args_fields:
            for name, value in args_fields:
                if 'fields' in self._config and name not in self._config['fields']:
                    for k in self._config['fields']:
                        if 'alias' in self._config['fields'][k] and name in self._config['fields'][k]['alias']:
                            name = k

                if name not in fields:
                    fields[name] = []

                field_type = 'TextField'
                if 'fields' in self._config and name in self._config['fields']:
                    field_type = self._config['fields'][name]['type']

                if field_type == 'VersionPicker':
                    fields[name].append({action: [{'name': value}]})
                elif field_type == 'MultiSelect':
                    fields[name].append({action: [value]})
                else:
                    fields[name].append({action: value})
