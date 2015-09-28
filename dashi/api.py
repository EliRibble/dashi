import flask

import pygal

blueprint = flask.Blueprint('api', __name__)

@blueprint.route('/')
def index():
    return flask.render_template('index.html')

@blueprint.route('/barchart/')
def forecast():
    bar_chart = pygal.Bar(width=500, height=400)
    bar_chart.title = 'Eli'
    lower, higher, params = [12, 13], [15, 18], ['param1', 'param2']
    bar_chart.add('lower', lower)
    bar_chart.add('higher', higher)
    bar_chart.x_labels = params
    return flask.Response(response=bar_chart.render(), content_type='image/svg+xml')
