import argparse
import itertools
import logging
import os
import sys

from robotizr.core import config_loader
from robotizr.core import object_printer
from robotizr.importer.jira_api import JiraApi
from robotizr.importer.jira_importer import JiraImporter
from robotizr.input.jira_reader import JiraReader
from robotizr.output import writer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def run():
    parser = argparse.ArgumentParser(prog='python -m robotizr')
    parser.add_argument('-c', '--config', action='append', nargs='+', help='Path to config file')
    parser.add_argument('-s', '--source', help='Test case source')

    parser.add_argument('-q', '--query', help='Query to be executed to get tests which should be generated')
    parser.add_argument('-t', '--target', help='Target folder where the files should be placed, default is current '
                                               'directory', default='.')

    parser.add_argument('-i', '--import-test-exec', help='Import test execution result file')
    parser.add_argument('-p', '--project-key', help='Project key for test execution import')
    parser.add_argument('-k', '--test-exec-key', help='Test execution key to be overwritten')
    parser.add_argument('--set-field', nargs=2, action='append',
                        help='Define field - value pairs to be set (e.g. --set-field summary "Foo bar")')
    parser.add_argument('--add-field', nargs=2, action='append',
                        help='Define field - value pairs to be added (e.g. --add-field scope webshop)')

    parser.add_argument('--print-default-config', help='Prints the content of the default config and exit',
                        action='store_true')
    parser.add_argument('--print-test', help='Prints the fields of the given issue and exit')

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
    elif args.print_default_config:
        print_default_config()
    elif args.print_test:
        print_issue(args)
    elif args.import_test_exec:
        if args.project_key or args.test_exec_key:
            import_test_exec(args)
        else:
            parser.print_help()
    else:
        generate(args)


def print_default_config():
    print(open(os.path.dirname(os.path.abspath(__file__)) + '/resources/default-config.json').read())


def print_issue(args):
    config_files = list(itertools.chain(*args.config))
    config = config_loader.load(config_files)
    reader = JiraReader(config['source'][args.source])
    test = reader.get_test(args.print_test)
    object_printer.print_object(test)


def generate(args):
    config_files = list(itertools.chain(*args.config))
    config = config_loader.load(config_files)
    reader = JiraReader(config['source'][args.source])
    props = {"target": args.target}
    suites = reader.convert_tests(args.query, props)
    writer.write(config['output'], suites, args.target)


def import_test_exec(args):
    config_files = list(itertools.chain(*args.config))
    config = config_loader.load(config_files)
    importer = JiraImporter(config['source'][args.source])
    issue_key = importer.import_result(args.import_test_exec, args.project_key, args.test_exec_key)
    update_fields(issue_key, config, args)


def update_fields(issue_key, config, args):
    source = config['source'][args.source]
    api = JiraApi(source)
    api.update_issue(issue_key, args.set_field, args.add_field)

