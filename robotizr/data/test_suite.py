class TestSuite(object):
    def __init__(self):
        self.name = None
        self.test_cases = []
        self.settings = None


class Settings(object):
    def __init__(self):
        self.name = None
        self.documentation = None
        self.default_tags = []
        self.force_tags = []
        self.suite_setup = []
        self.suite_teardown = []
        self.test_setup = []
        self.test_teardown = []
        self.resources = []
