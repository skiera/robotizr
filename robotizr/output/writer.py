import os
import re
import codecs
import unicodedata


def write(config, suites, target):
    for suite in suites:

        name_parts = suite.name.strip("/").split("/")
        for i, s in enumerate(name_parts):
            name_parts[i] = slugify(s)

        path = "%s/%s" % (target, '/'.join(name_parts[:-1]))
        os.makedirs(path, exist_ok=True)

        # TODO make file style / separator configurable (space separated, pipe separated [table format, aligned pipes])
        separator = ' ' * int(config['number_of_spaces'])

        rel_root_path = "../" * (len(name_parts) - 1)

        with codecs.open("%s/%s.%s" % (path, name_parts[-1], config['file_extension']), "w+", "utf-8-sig") as f:
            if suite.settings:
                f.write("*** Settings ***\n")
                write_multi_suite_setting(f, "Suite Setup", suite.settings.suite_setup, separator)
                write_multi_suite_setting(f, "Suite Teardown", suite.settings.suite_teardown, separator)
                write_multi_suite_setting(f, "Test Setup", suite.settings.test_setup, separator)
                write_multi_suite_setting(f, "Test Teardown", suite.settings.test_teardown, separator)
                for resource in suite.settings.resources:
                    f.write("Resource%s%s\n" % (separator, resource.replace("${RELATIVE_ROOT_PATH}", rel_root_path)))
                f.write("\n")
            f.write("*** Test Cases ***\n")

            for test_case in suite.test_cases:
                try:
                    f.write(test_case.name + "\n")
                    if test_case.documentation:
                        f.write("%s[Documentation]%s%s\n" % (
                            separator, separator, test_case.documentation.replace("\r", "").replace("\n", "\n" + separator + "..." + separator)))
                    if test_case.tags:
                        f.write("%s[Tags]%s%s\n" % (separator, separator, separator.join(test_case.tags)))
                    if len(test_case.setup) > 0:
                        write_multi_test_setting(f, "Setup", suite.settings.test_setup + test_case.setup, separator)
                    for keyword in test_case.keywords:
                        f.write("%s%s" % (separator, keyword.keyword))
                        for argument in keyword.arguments:
                            f.write("%s%s" % (separator, argument))
                        f.write("\n")
                    if test_case.teardown:
                        f.write("%s[Teardown]%sRun Keywords%s%s\n" % (
                            separator, separator, separator, (separator + "AND" + separator).join(test_case.teardown)))
                    f.write("\n")
                except UnicodeEncodeError as err:
                    print("WARN", err)


def write_multi_suite_setting(f, name, keywords, separator):
    if len(keywords) == 1:
        f.write("%s%s%s\n" % (name, separator, keywords[0]))
    elif len(keywords) > 1:
        f.write(
            "%s%sRun Keywords%s%s\n" % (
                name, separator, separator, (separator + "AND" + separator).join(keywords)))


def write_multi_test_setting(f, name, keywords, separator):
    if len(keywords) == 1:
        f.write("%s[%s]%s%s\n" % (separator, name, separator, keywords[0]))
    elif len(keywords) > 1:
        f.write(
            "%s[%s]%sRun Keywords%s%s\n" % (
                separator, name, separator, separator, (separator + "AND" + separator).join(keywords)))


def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '-', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)
