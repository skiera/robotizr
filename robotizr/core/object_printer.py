import types


def print_object(obj, prefix=''):
    if isinstance(obj, dict):
        for key in obj:
            print_attr(key, obj[key], prefix)
    elif isinstance(obj, list):
        for i, entry in enumerate(obj):
            print_attr(str(i), entry, prefix)
    else:
        fields = dir(obj)
        for field in fields:
            if not field.startswith("__"):
                attr = getattr(obj, field)
                print_attr(field, attr, prefix)


def print_attr(field, attr, prefix):
    if isinstance(attr, (types.BuiltinFunctionType, types.MethodType)) or field.startswith("_"):
        return
    elif isinstance(attr, list):
        print(prefix, field, "(", type(attr), ")")
        i = 0
        for value in attr:
            print_attr(str(i), value, (" " * (len(field) + 1)) + prefix)
            i = i + 1
    elif isinstance(attr, (type, object)) and not isinstance(attr, (int, str, float, complex)):
        print(prefix, field, "(", type(attr), "):")
        print_object(attr, (" " * (len(field) + 1)) + prefix)
    else:
        print(prefix, field, "(", type(attr), "):", attr)
