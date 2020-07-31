# Robotizr

Robotizr is a generator tool for [Robot Framework](https://robotframework.org/) test cases from a test case management tool (only [Xray for Jira](https://www.getxray.app/) so far).

## Getting Started

These instructions will explain how it works and how to install it. 

### How it works

The basic idea behind this tool is to increase the accessibility of the test automation by using a test management tool.

Like the concept of *mobile first* in the webdesign world this tool follows to concept of *human first* for mobile tests.
How does it work? Test management tools helps to manage your test cases and gives everyone an easy access. Some tools like [Xray for Jira](https://www.getxray.app/) provides the possibility to import test executions from test automation frameworks.

`Test Manangement Tool` -> `Test case generation` -> `Test implementation` -> `Test execution` -> `Import test results`

### Supported Tools

At the moment only [Xray for Jira](https://www.getxray.app/) is supported. No plan for other tools yet.
Please contact me if you need any help or support with other test management tools. 

### Prerequisites

Only Python 3 is needed, all dependencies are installed automatically via `pip`.

### Installing

You can install the current development version from GitHub:

```
pip install --upgrade -e git+https://github.com/skiera/robotizr@develop#egg=robotizr
```

### Usage

```shell script
python -m robotizr -h
usage: python -m robotizr [-h] [-c CONFIG [CONFIG ...]] [-s SOURCE] [-q QUERY]
                          [-t TARGET] [-i IMPORT_TEST_EXEC] [-p PROJECT_KEY]
                          [-k TEST_EXEC_KEY] [--set-field SET_FIELD SET_FIELD]
                          [--add-field ADD_FIELD ADD_FIELD]
                          [--print-default-config] [--print-test PRINT_TEST]
                          [--clone-tests CLONE_TESTS [CLONE_TESTS ...]]
                          [--print-config]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG [CONFIG ...], --config CONFIG [CONFIG ...]
                        Path to config file
  -s SOURCE, --source SOURCE
                        Test case source
  -q QUERY, --query QUERY
                        Query to be executed to get tests which should be
                        generated
  -t TARGET, --target TARGET
                        Target folder where the files should be placed,
                        default is current directory
  -i IMPORT_TEST_EXEC, --import-test-exec IMPORT_TEST_EXEC
                        Import test execution result file
  -p PROJECT_KEY, --project-key PROJECT_KEY
                        Project key for test execution import
  -k TEST_EXEC_KEY, --test-exec-key TEST_EXEC_KEY
                        Test execution key to be overwritten
  --set-field SET_FIELD SET_FIELD
                        Define field - value pairs to be set (e.g. --set-field
                        summary "Foo bar")
  --add-field ADD_FIELD ADD_FIELD
                        Define field - value pairs to be added (e.g. --add-
                        field scope webshop)
  --print-default-config
                        Prints the content of the default config and exit
  --print-test PRINT_TEST
                        Prints the fields of the given issue and exit
  --clone-tests CLONE_TESTS [CLONE_TESTS ...]
                        Clones a given set of tests to the given project-key
                        (e.g. --clone-tests TEST-1 TEST-2 TEST-3 --project-key
                        PROJECT
  --print-config        Prints the content of the merged config
```

### Test case generation 

Robotizr allows to separation of configuration files to for example store project related information in the project repository and login + password in a personal file. 

Example project configuration:

```json
{
  "source": {
    "example": {
      "type": "jira",
      "server": "https://jira.example.com/jira",
      "fields": {
        "customfield_13557": {
          "type": "TextField",
          "alias": ["scope", "platform"]
        },
        "customfield_12756": {
          "type": "MultiSelect",
          "alias": ["environments"]
        },
        "fixVersions": {
          "type": "VersionPicker"
        }
      },
      "mappings": {
        "test_suite": {
          "name": "%fields.customfield_13050|default=unnamed%",
          "settings": {
            "resources": [
              "../${RELATIVE_ROOT_PATH}init.robot"
            ],
            "suite_setup": [
              "Init Suite Keyword"
            ],
            "test_setup": [
              "Init Test Keyword"
            ],
            "test_teardown": [
              "Teardown Keyword"
            ]
          }
        },
        "test_case": {
          "name": "%key% %fields.summary%",
          "tags": [
            "project:%fields.project.name%",
            "key:%key%",
            "set:%fields.customfield_12657%",
            "plan:%fields.customfield_12751%",
            "link:%fields.issuelinks.outwardIssue.key%",
            "link:%fields.issuelinks.inwardIssue.key%",
            "label:%fields.labels%"
          ],
          "documentation": "%fields.description%",
          "setup": "%fields.customfield_12658|convert=&key& &fields.summary&%",
          "keywords": "%fields.customfield_12655.steps:keyword=step,arguments=data%"
        }
      }
    }
  }
}
```

Example login + password configuration:

```json
{
  "source": {
    "example": {
      "username": "username",
      "password": "MySecretPassword123"
    }
  }
}
```

Example call

```shell script
python -m robotizr -c ${PATH_TO_PROJECT}/config/robotizr-config.json ${HOME}/secure/private.json -s example -t ${PATH_TO_PROJECT}\cases --query "project = EXMAPLE AND type = test"
```

### Execution result import

Robotizr can also import test execution files to create Test Execution tickets in Jira. 

Example call to create a new execution ticket

```shell script
python -m robotizr -c ${PATH_TO_PROJECT}/config/robotizr-config.json ${HOME}/secure/private.json -s example -p PRJ -i output.xml
```

or to update an existing one

```shell script
python -m robotizr -c ${PATH_TO_PROJECT}/config/robotizr-config.json ${HOME}/secure/private.json -s example -p PRJ -k PRJ-123 -i output.xml
```


## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Sven Kiera** - *Initial work* - [skiera](https://github.com/skiera)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
