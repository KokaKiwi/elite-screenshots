from flask import Flask, jsonify, abort, send_from_directory
from .utils import templated, authenticated

app = Flask(__name__)
app.config.from_object('elite.settings')

from flask.ext.mako import MakoTemplates
mako = MakoTemplates(app)

from .api import api
app.register_blueprint(api, url_prefix='/api')

# Routes


@app.route('/')
@app.route('/<path:path>')
@templated()
def resource(path=None):
    from pathlib import Path
    from flask.ext.mako import render_template
    from .data import Entity, Category, Screenshot, Root

    path = path or Path()

    template_names = {
        Root: 'index.html',
        Category: 'category.html',
        Screenshot: 'screenshot.html',
    }

    entity = Entity.load(path)
    if entity is None:
        abort(404)

    template_name = template_names[entity.__class__]

    return template_name, dict(root=Root(), resource=entity)


@app.route('/<path:path>.png')
def resource_image(path):
    from . import settings

    return send_from_directory(str(settings.DATA_PATH), path + '.png')


@app.route('/panel')
@templated('panel.html')
@authenticated
def panel():
    pass
