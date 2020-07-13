import logging
import os

import requests
from jsonmerge import Merger
from requests.auth import HTTPBasicAuth


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

    def clone_tests(self, test_keys, new_project_key):
        if not new_project_key:
            raise ValueError("Project key missing")

        folders = self.get_test_repository_folders(new_project_key)

        for test_key in test_keys:
            r = requests.get(self._config['server'] + '/rest/api/2/issue/' + test_key,
                             auth=HTTPBasicAuth(self._config['username'], self._config['password']))
            if r.status_code != 200:
                logging.error("%s: %s", r.status_code, r.text)
                raise ValueError(r.text)

            orig_issue = r.json()

            if orig_issue["fields"]["issuetype"]["name"] != "Test":
                raise ValueError("Ticket type '" + orig_issue["fields"]["issuetype"]["name"]
                                 + "' is not supported, must be 'Test'")

            # FIXME Remove static field names and add mapping support
            new_issue = {
                "fields": {
                    "project": {
                        "key": new_project_key
                    },
                    "issuetype": {
                        "name": orig_issue["fields"]["issuetype"]["name"]
                    },
                    "summary": orig_issue["fields"]["summary"],
                    "description": orig_issue["fields"]["description"],
                    "customfield_12651": {
                        "id": orig_issue["fields"]["customfield_12651"]["id"]
                    },
                    "priority": {
                        "id": orig_issue["fields"]["priority"]["id"]
                    },
                    "assignee": {
                        "name": "tempo"
                    },
                    "customfield_12655": {
                        "steps": []
                    }
                },
                "update": {
                    "issuelinks": [
                        {
                            "add": {
                                "type": {
                                    "name": "Cloners",
                                    "inward": "is cloned by",
                                    "outward": "clones"
                                },
                                "inwardIssue": {
                                    "key": orig_issue["key"]
                                }
                            }
                        }
                    ]
                }
            }

            for orig_step in orig_issue["fields"]["customfield_12655"]["steps"]:
                new_step = {
                    "index": orig_step["index"],
                    "step": orig_step["step"]
                }
                if "data" in orig_step:
                    new_step["data"] = orig_step["data"]
                if "result" in orig_step:
                    new_step["result"] = orig_step["result"]

                new_issue["fields"]["customfield_12655"]["steps"].append(new_step)

            r = requests.post(self._config['server'] + '/rest/api/2/issue',
                              auth=HTTPBasicAuth(self._config['username'], self._config['password']),
                              json=new_issue)
            if r.status_code >= 300:
                raise ValueError(r.text)
            else:
                response = r.json()
                new_test_key = response['key']

            if not new_test_key:
                raise ValueError("Missing new test key")

            folder = orig_issue["fields"]["customfield_13050"]
            if folder not in folders:
                folders[folder] = self._create_test_repository_folder_recursive(folder, new_project_key, folders)

            folder_id = folders[folder]

            json = {"add": [new_test_key]}
            r = requests.put(self._config['server'] + '/rest/raven/1.0/api/testrepository/'
                             + new_project_key + '/folders/' + str(folder_id) + '/tests',
                             auth=HTTPBasicAuth(self._config['username'], self._config['password']),
                             json=json)
            if r.status_code >= 300:
                raise ValueError(r.text)

            logging.info("Cloned %s -> %s", orig_issue['key'], new_test_key)

    def _create_test_repository_folder_recursive(self, folder, project_key, folders):
        tmp = folder
        missing_folders = []
        while tmp not in folders:
            head, tail = os.path.split(tmp)
            tmp = head
            missing_folders.append(tail)
            if not tmp or tmp == '/':
                raise ValueError("Can not find root folder for '" + folder + '"')

        root_folder_id = folders[tmp]
        for missing_folder in missing_folders:
            json = {"name": missing_folder}
            r = requests.post(self._config['server'] + '/rest/raven/1.0/api/testrepository/'
                              + project_key + '/folders/' + str(root_folder_id),
                              auth=HTTPBasicAuth(self._config['username'], self._config['password']),
                              json=json)
            if r.status_code >= 300:
                raise ValueError(r.text)
            root_folder_id = r.json()["id"]

        logging.info("Created folder: %s", folder)
        return root_folder_id

    def get_test_repository_folders(self, project_key):
        r = requests.get(self._config['server'] + '/rest/raven/1.0/api/testrepository/' + project_key + '/folders',
                         auth=HTTPBasicAuth(self._config['username'], self._config['password']))
        if r.status_code >= 300:
            logging.error("%s: %s", r.status_code, r.text)
            raise ValueError(r.text)

        folder_json = r.json()
        folders = self._convert_folders_to_list(folder_json)
        return folders

    def _convert_folders_to_list(self, json):
        folder_list = {}
        for folder in json["folders"]:
            folder_list[folder["testRepositoryPath"] + "/" + folder["name"]] = folder["id"]
            if folder["folders"]:
                schema = {"properties": {"bar": {"mergeStrategy": "append"}}}
                merger = Merger(schema)
                folder_list = merger.merge(folder_list, self._convert_folders_to_list(folder))
        return folder_list
