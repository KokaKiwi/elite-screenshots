from functools import wraps
from flask import abort, request
from . import settings


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

def authenticated(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        api_key = request.args.get('key', None)
        if api_key is None or api_key != settings.API_KEY:
            abort(401)

        return f(*args, **kwargs)

    return wrapped
