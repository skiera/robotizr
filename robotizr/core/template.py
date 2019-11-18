import re


def evaluate(source, test, issue, field, template, props, clazz=None):
    attr = getattr(test, field)
    if isinstance(attr, list):
        if isinstance(template, list):
            for row in template:
                attr.extend(get_list_value_for_placeholder(source, issue, row, props, clazz))
        else:
            attr.extend(get_list_value_for_placeholder(source, issue, template, props, clazz))
    else:
        setattr(test, field, get_string_value_for_placeholder(source, issue, template, props, clazz))


def get_list_value_for_placeholder(source, issue, template, props, clazz=None):
    matches = re.findall("(%([^%|:]+)(?::([^%|]+))?(?:\\|([^%]+))?%)", template)
    if len(matches) != 1:
        raise LookupError(
            "Expected 1 match, but found %d matches %s for template '%s'" % (len(matches), matches, template))
    result = []
    for placeholder, key, args, modifier in matches:
        attr = rgetattr(issue, key)
        if isinstance(attr, list):
            values = rgetattr(issue, key)
            for value in values:
                if clazz is not None:
                    obj = clazz()
                    fields = re.findall("([^,=]+)=([^,]+)?", args)
                    for field_name, field_value in fields:
                        evaluate(source, obj, value, field_name, "%" + field_value.replace("~", "|") + "%", props)
                    result.append(obj)
                else:
                    if value:
                        if modifier:
                            value = modify(source, modifier, value, props)
                        result.append(template.replace(placeholder, str(value).rstrip()))
        else:
            value = rgetattr(issue, key)
            if value:
                result.extend(template.replace(placeholder, str(rgetattr(issue, key)).rstrip()).split("\n"))

    return result if len(result) != 1 or result[0] else []


def get_string_value_for_placeholder(source, issue, template, props, clazz=None):
    if clazz is not None:
        obj = clazz()
        for field in template:
            attr = getattr(obj, field)
            for t in template[field]:
                attr.append(get_string_value_for_placeholder(source, issue, t, props))
        return obj
    else:
        matches = re.findall("(%([^%|:]+)(?::([^%|]+))?(?:\\|([^%]+))?%)", template)
        value = template
        modifier = None
        for placeholder, key, args, modifier in matches:
            value = value.replace(placeholder, str(rgetattr(issue, key)).rstrip())

        if modifier:
            value = modify(source, modifier, value, props)

        return value


def modify(source, modifier, value, props):
    matches = re.search("([a-z_]+)=(.*)", modifier)
    if matches:
        cmd = matches.group(1)
        payload = matches.group(2)
        if cmd == "convert":
            if not value:
                return value
            issue = source.get_test(value)
            return get_string_value_for_placeholder(source, issue, payload.replace("&", "%"), props)
        elif cmd == "download":
            if value:
                url, file_name, variable = payload.split(";")
                url = get_string_value_for_placeholder(source, value, url.replace("&", "%"), props)
                file_name = "%s/%s" % (props["target"], get_string_value_for_placeholder(source, value, file_name.replace("&", "%"), props))
                source.save_attachment(url, file_name)
                variable = get_string_value_for_placeholder(source, value, variable.replace("&", "%"), props)
                return variable
        elif cmd == "default":
            if not value or value is None:
                return payload
        else:
            print("WARN unknown command modifier '%s' ('%s')" % (cmd, modifier))
    else:
        print("WARN modifier '%s' is invalid" % modifier)
    return value


def rgetattr(obj, attr):
    def _rgetattr(_obj, names, pos):
        name = names[pos]
        if len(names) == pos + 1:
            value = getattr(_obj, name)
            return value if value and value is not None else ""

        if isinstance(_obj, list):
            result = []
            for row in _obj:
                result.append(_rgetattr(getattr(row, name), names, pos + 1))
            return result
        else:
            return _rgetattr(getattr(_obj, name), names, pos + 1)

    try:
        return _rgetattr(obj, attr.split("."), 0)
    except AttributeError as err:
        print("INFO", err)
        return ""
