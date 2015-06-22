from flask import Blueprint, request
from PIL import Image
from .utils import render_json

api = Blueprint('api', __name__)


def error(msg):
    return {'status': 'err', 'message': str(msg)}


@api.route('/categories')
@render_json
def categories():
    from .data import Root, Category

    def render_category(category):
        return {
            'name': category.full_name,
            'path': str(category.rel_path),
        }

    root = Root()
    all_categories = filter(
        lambda child: isinstance(child, Category), root.all_children)
    all_categories = map(render_category, all_categories)
    all_categories = list(all_categories)

    return {
        'categories': all_categories,
    }


@api.route('/categories/create', methods=['POST'])
@render_json
def categories_create():
    from .data import Entity, Category

    data = request.get_json()

    parent = Entity.load(data['parent'])

    name = data['name']
    description = data['description']

    if name == '':
        return error('Name must be filled!')

    category = Category(name, description, parent=parent)
    category.save()

    return {'status': 'ok', 'path': str(category.rel_path)}


@api.route('/screenshot/create', methods=['POST'])
@render_json
def screenshot_create():
    from .data import Entity, Category, Screenshot

    data = request.get_json()

    category = Entity.load(data['category'])

    name = data['name']
    description = data.get('description')
    metadata = data['metadata']

    if name == '':
        return error('Name must be filled!')

    screenshot = Screenshot(
        name, description=description, category=category, metadata=metadata)
    screenshot.save()

    return {'status': 'ok', 'path': str(screenshot.rel_path)}


@api.route('/screenshot/upload', methods=['POST'])
@render_json
def screenshot_upload():
    from .data import Screenshot

    path = request.form['path']
    screenshot = Screenshot.load(path)

    if 'file' not in request.files:
        return error('You must provide a file!')

    file = request.files['file']

    img = Image.open(file)
    img.save(str(screenshot.image().path))

    screenshot.ensure_sizes()

    return {'status': 'ok'}
