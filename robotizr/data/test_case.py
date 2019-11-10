class TestCase(object):
    def __init__(self):
        self.name = None
        self.documentation = None
        self.tags = []
        self.setup = []
        self.teardown = []
        self.template = None
        self.timeout = None
        self.keywords = []


class Keyword(object):
    def __init__(self):
        self.keyword = None
        self.arguments = []
