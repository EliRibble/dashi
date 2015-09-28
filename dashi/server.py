import flask

import dashi.api
import pygal


def create_app():
    app = flask.Flask(__name__, static_url_path='')

    app.register_blueprint(dashi.api.blueprint)

    return app

def run():
    app = create_app()
    app.config['DEBUG'] = True
    app.run('0.0.0.0', 5000)
