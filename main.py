#!/usr/bin/env python
from elite.app import app

if __name__ == '__main__':
    app.config['DEBUG'] = True
    app.run()
