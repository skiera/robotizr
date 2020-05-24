import base64
import logging
import mimetypes
import re
from os.path import normpath, join, dirname

import requests
from requests.auth import HTTPBasicAuth
from robot.api import ExecutionResult, ResultVisitor
from robot.result.model import Keyword


class JiraImporter(object):

    def __init__(self, config):
        self._config = config

    def import_result(self, file, project_key, test_exec_key):
        test_execution_key = self._create_test_execution(file, project_key, test_exec_key)

        self._update_test_execution(file, test_execution_key)

    def _create_test_execution(self, file, project_key, test_exec_key):
        f = open(file, "r")
        content = f.read()

        # Remove all non jira id tags to avoid creating unwanted jira test labels
        matches = re.findall("(<tag>(.*)</tag>)", content)
        for tag, name in matches:
            if not re.search("^([A-Z]{2,}-[0-9]+)$", name):
                content = content.replace(tag, "")

        # Create API request to create to test execution
        files = {'file': ('output.xml', content)}

        params = ''
        if project_key is not None:
            params = params + '?projectKey=' + project_key
        if test_exec_key is not None:
            params = params + '&testExecKey=' + test_exec_key

        r = requests.post(self._config['server'] + '/rest/raven/1.0/import/execution/robot' + params,
                          auth=HTTPBasicAuth(self._config['username'], self._config['password']),
                          files=files)
        json = r.json()

        logging.info('Created/Updated test execution %s with id %s', json['testExecIssue']['key'],
                     json['testExecIssue']['id'])

        return json['testExecIssue']['key']

    def _update_test_execution(self, file, test_execution_key):
        # Update test execution
        # - Update Title
        # - Update steps status

        r = requests.get(self._config['server'] + '/rest/raven/1.0/api/testexec/' + test_execution_key + '/test',
                         auth=HTTPBasicAuth(self._config['username'], self._config['password']))
        exec_json = r.json()

        status = {}

        result = ExecutionResult(file)
        result.visit(ExecutionStatusChecker(status))

        for test_key in status:
            for test in exec_json:
                if test_key == test['key']:
                    r = requests.get(
                        self._config['server'] + '/rest/raven/1.0/api/testrun/' + str(test['id']) + '/',
                        auth=HTTPBasicAuth(self._config['username'], self._config['password']))
                    run_json = r.json()

                    logging.info('Updating test run for test %s ...', test['key'])

                    las_pos = -1
                    for keyword in status[test_key]:
                        for i in range(len(run_json['steps'])):
                            if i <= las_pos:
                                continue
                            if keyword['name'].lower() == run_json['steps'][i]['step']['raw'].lower():
                                las_pos = i

                                input_json = {'status': keyword['status'], 'actualResult': keyword['message'],
                                              'evidences': []}
                                for attachment in keyword['attachments']:
                                    attachment_file = normpath(join(dirname(file), attachment))
                                    with open(attachment_file, "rb") as f:
                                        evidence = {
                                            'filename': attachment,
                                            'contentType': mimetypes.guess_type(attachment)[0],
                                            'data': base64.b64encode(f.read()).decode('utf-8')
                                        }
                                        input_json['evidences'].append(evidence)

                                r = requests.put(
                                    self._config['server'] + '/rest/raven/1.0/api/testrun/' + str(
                                        test['id']) + '/step/' + str(run_json['steps'][i]['id']) + '/',
                                    auth=HTTPBasicAuth(self._config['username'], self._config['password']),
                                    json=input_json
                                )

                                logging.info('... set status for %s to %s (with %i attachments)', run_json['steps'][i]['step']['raw'],
                                             keyword['status'], len(keyword['attachments']))

                                break
                            else:
                                las_pos = i


class ExecutionStatusChecker(ResultVisitor):

    def __init__(self, status):
        self._status = status

    def visit_test(self, test):
        match = re.search("[A-Z]{2,}-[0-9]+", test.name)
        if match:
            test_key = match.group(0)
            self._status[test_key] = []
            keywords = test.keywords.normal
            for keyword in keywords:
                status = {
                    'name': keyword.kwname,
                    'status': keyword.status,
                    'message': '',
                    'attachments': []
                }

                if keyword.status == 'FAIL':
                    status['message'] = keyword.parent.message

                self._search_screenshots(keyword, status)

                self._status[test_key].append(status)

    def _search_screenshots(self, keyword, status):
        if keyword.kwname == 'Capture Page Screenshot' or keyword.kwname == 'Capture Element Screenshot':
            match = re.search('img src="([^"]+)"', keyword.messages[0].message)
            if match:
                status['attachments'].append(match.group(1))
        else:
            for child in keyword.children:
                if isinstance(child, Keyword):
                    self._search_screenshots(child, status)
