from jira import JIRA
from robotizr.core import template
from robotizr.data.test_case import TestCase, Keyword
from robotizr.data.test_suite import TestSuite, Settings


class JiraReader(object):

    def __init__(self, config):
        self.config = config
        self.jira = JIRA(config['server'],
                         auth=(config['username'], config['password']))
        self.cache = {}

    def get_test(self, issue_id):
        if issue_id not in self.cache:
            self.cache[issue_id] = self.jira.issue(issue_id)
        return self.cache[issue_id]

    def convert_tests(self, query):
        issues = self.jira.search_issues(query)
        suites = {}
        for issue in issues:
            suite_name = template.get_string_value_for_placeholder(self, issue,
                                                                   self.config['mappings']['test_suite']['name'])
            if suite_name not in suites:
                suites[suite_name] = self._convert_obj(self.config["mappings"]["test_suite"], issue, TestSuite)
            suite = suites[suite_name]
            suite.test_cases.append(self._convert_obj(self.config["mappings"]["test_case"], issue, TestCase))
        return list(suites.values())

    def _convert_obj(self, mappings, issue, clazz):
        obj = clazz()
        for field in mappings:
            if clazz is TestCase and field == "keywords":
                template.evaluate(self, obj, issue, field, mappings[field], Keyword)
            elif clazz is TestSuite and field == "settings":
                template.evaluate(self, obj, issue, field, mappings[field], Settings)
            else:
                template.evaluate(self, obj, issue, field, mappings[field])
        return obj
