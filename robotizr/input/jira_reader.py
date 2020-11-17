import shutil
import base64
import urllib.request

from jira import JIRA
from robotizr.core import template
from robotizr.data.test_case import TestCase, Keyword
from robotizr.data.test_suite import TestSuite, Settings


class JiraReader(object):

    def __init__(self, config):
        self._config = config
        self._jira = JIRA(config['server'],
                          auth=(config['username'], config['password']))
        self._cache = {}

    def get_test(self, issue_id):
        if issue_id not in self._cache:
            self._cache[issue_id] = self._jira.issue(issue_id)
        return self._cache[issue_id]

    def convert_tests(self, query, props):
        issues = self._jira.search_issues(query, maxResults=False)
        suites = {}
        for issue in issues:
            suite_name = template.get_string_value_for_placeholder(self, issue, issue,
                                                                   self._config['mappings']['test_suite']['name'], props)
            if suite_name not in suites:
                suites[suite_name] = self._convert_obj(self._config["mappings"]["test_suite"], issue, props, TestSuite)
            suite = suites[suite_name]
            suite.test_cases.append(self._convert_obj(self._config["mappings"]["test_case"], issue, props, TestCase))
        return list(suites.values())

    def save_attachment(self, url, file_name):
        credentials = "%s:%s" % (self._config['username'], self._config['password'])
        headers = {"Authorization": "Basic %s" % str(base64.b64encode(credentials.encode("utf-8")), "utf-8")}

        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request) as response:
            with open(file_name, "wb") as out_file:
                shutil.copyfileobj(response, out_file)

    def _convert_obj(self, mappings, issue, props, clazz):
        obj = clazz()
        for field in mappings:
            if clazz is TestCase and field == "keywords":
                template.evaluate(self, obj, issue, issue, field, mappings[field], props, Keyword)
            elif clazz is TestSuite and field == "settings":
                template.evaluate(self, obj, issue, issue, field, mappings[field], props, Settings)
            else:
                template.evaluate(self, obj, issue, issue, field, mappings[field], props)
        return obj
