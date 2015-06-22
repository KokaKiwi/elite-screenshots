import arrow
import toml
from pathlib import Path
from . import settings


class Entity(object):
    METADATA_FILENAME = 'metadata.toml'

    def save(self):
        data = self.as_dict()
        data['type'] = self.type

        path = self.path
        if not path.exists():
            path.mkdir(parents=True)

        metadata_path = path / self.METADATA_FILENAME
        with metadata_path.open('w+') as f:
            toml.dump(data, f)

    def as_dict(self):
        return {}

    @property
    def type(self):
        return self.__class__.__name__.lower()

    @classmethod
    def load(cls, path):
        path = Path(path)

        if not path.is_absolute():
            path = settings.DATA_PATH / path

        if path == settings.DATA_PATH:
            return Root()

        metadata_path = settings.DATA_PATH / path / cls.METADATA_FILENAME
        if not metadata_path.exists():
            return None

        with metadata_path.open() as f:
            data = toml.load(f)

        return cls.load_from_data(path, data)

    @classmethod
    def load_from_data(self, path, data):
        LOAD_FUNCTIONS = {
            'category': Category.load_from_data,
            'screenshot': Screenshot.load_from_data,
        }

        type = data['type']
        load_function = LOAD_FUNCTIONS[type]

        return load_function(path, data)

    @classmethod
    def is_entity(cls, path):
        path = Path(path)

        metadata_path = settings.DATA_PATH / path / cls.METADATA_FILENAME
        return metadata_path.exists()

    @property
    def url(self):
        from flask import url_for

        return url_for('resource', path=self.rel_path)

    @property
    def breadcrumb(self):
        breadcrumb = self.parent.breadcrumb if self.parent else []
        return breadcrumb + [self]

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.path == other.path


class Category(Entity):

    def __init__(self, name, description=None, parent=None, path=None):
        self.name = name
        self.description = description
        self._parent = parent
        self._path = path

    @property
    def slug_name(self):
        from boltons.strutils import slugify
        return slugify(self.name)

    @property
    def path(self):
        if self._path:
            return self._path

        path = self._parent.path if self._parent else settings.DATA_PATH
        return path / self.slug_name

    @property
    def rel_path(self):
        return self.path.relative_to(settings.DATA_PATH)

    @property
    def parent(self):
        if self._parent:
            return self._parent

        path = self._path.parent if self._path else Path()
        return Category.load(path)

    @property
    def children(self):
        for path in self.path.iterdir():
            if not path.is_dir():
                continue
            if not Entity.is_entity(path):
                continue

            yield Entity.load(path)

    @property
    def subcategories(self):
        _filter = lambda child: isinstance(child, Category)
        return filter(_filter, self.children)

    @property
    def screenshots(self):
        _filter = lambda child: isinstance(child, Screenshot)
        return filter(_filter, self.children)

    @property
    def all_children(self):
        for child in self.children:
            yield child

            if isinstance(child, Category):
                yield from child.all_children

    @property
    def full_name(self):
        if self.parent and not isinstance(self.parent, Root):
            return '%s / %s' % (self.parent.full_name, self.name)
        return self.name

    def dump_tree(self, level=0):
        indent = '  '*level + '-'
        print(indent, self)

        for child in self.children:
            child.dump_tree(level=level+1)

    def as_dict(self):
        return {
            'name': self.name,
            'description': self.description,
        }

    @classmethod
    def load_from_data(cls, path, data):
        name = data['name']
        description = data.get('description')

        return Category(name, description, path=path)

    def __repr__(self):
        return '<Category name=%r path=%s>' % (self.name, self.path)


class Screenshot(Entity):
    DATE_FORMAT = 'YYYY-MM-DD'

    THUMBNAIL_SIZE = (300, 186)
    SHOW_SIZE = (1920, 1080)
    SIZES = [
        (1920, 1080),
        (1024, 768),
        (800, 600),
        THUMBNAIL_SIZE,
        SHOW_SIZE,
    ]

    def __init__(self, name, description=None, date=None, category=None, metadata=None, path=None):
        self.name = name
        self.description = description
        self.date = date or arrow.utcnow()
        self.metadata = metadata or {}
        self._category = category
        self._path = path

    @property
    def slug_name(self):
        from boltons.strutils import slugify
        return slugify(self.name)

    @property
    def foldername(self):
        return '%s-%s' % (self.date.format(self.DATE_FORMAT), self.slug_name)

    @property
    def category(self):
        if self._category:
            return self._category

        path = self._path.parent
        return Category.load(path)

    parent = category

    @property
    def path(self):
        if self._path:
            return self._path

        return self._category.path / self.foldername

    @property
    def rel_path(self):
        return self.path.relative_to(settings.DATA_PATH)

    @property
    def thumbnail(self):
        return self.image(size=Screenshot.THUMBNAIL_SIZE)

    def image(self, size=None):
        return Image(self, size=size)

    def ensure_sizes(self):
        for size in Screenshot.SIZES:
            self.image(size=size).ensure_image()

    def dump_tree(self, level=0):
        indent = '  '*level + '-'
        print(indent, self)

    def as_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'date': self.date,
            'metadata': self.metadata,
        }

    @classmethod
    def load_from_data(cls, path, data):
        name = data['name']
        description = data.get('description')
        date = arrow.get(data['date'])
        metadata = data.get('metadata', {})

        return Screenshot(name, description=description, date=date, metadata=metadata, path=path)

    def __repr__(self):
        return '<Screenshot name=%r date=%r path=%s>' % (self.name, self.date.humanize(), self.path)


class Root(Category):

    def __init__(self):
        super().__init__('Root')

        if not self.path.exists():
            self.path.mkdir(parents=True)

    @property
    def path(self):
        return settings.DATA_PATH

    @property
    def parent(self):
        return None

    def save(self):
        pass

    def __repr__(self):
        return '<Root>'


class Image(object):
    DEBUG = False

    def __init__(self, screenshot, size=None):
        self.screenshot = screenshot
        self.size = size

    @property
    def original(self):
        return self.screenshot.image()

    @property
    def image(self):
        from PIL import Image

        if not self.path.exists():
            return None

        return Image.open(str(self.path))

    @property
    def path(self):
        if self.size is None:
            filename = 'original.png'
        else:
            filename = '%dx%d.png' % (self.width, self.height)

        return self.screenshot.path / filename

    @property
    def url(self):
        if self.DEBUG:
            return self.placeholder

        if self.size is None:
            filename = 'original.png'
        else:
            filename = '%dx%d.png' % (self.width, self.height)

        self.ensure_image()
        return '%s/%s' % (self.screenshot.url, filename)

    @property
    def width(self):
        return self.size[0]

    @property
    def height(self):
        return self.size[1]

    @property
    def placeholder(self):
        (w, h) = self.size or (1920, 1080)

        return 'http://placehold.it/%dx%d' % (w, h)

    def ensure_image(self):
        if not self.path.exists():
            img = self.original.image
            img.resize(self.size).save(str(self.path))
