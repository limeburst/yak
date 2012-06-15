from flask import Flask
app = Flask(__name__)

def run_app(config):
    # TODO: Use 'app.config.from_pyfile'
    app.config = dict(app.config.items()+config.items())
    app.secret_key = 'not_so_secret'
    from yak.web import views
    app.run(host='0.0.0.0', port=app.config['PORT'])
