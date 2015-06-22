from functools import wraps


def render_json(f):
    from flask import jsonify

    @wraps(f)
    def wrapped(*args, **kwargs):
        res = f(*args, **kwargs)

        return jsonify(res)
    return wrapped


def templated(name=None):
    from flask.ext.mako import render_template

    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            res = f(*args, **kwargs)

            template_name = name
            if isinstance(res, tuple):
                (template_name, data) = res
            else:
                data = res or {}

            return render_template(template_name, **data)
        return wrapped
    return wrapper
