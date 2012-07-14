from flask import Flask
app = Flask(__name__)

def run_app(config):
    app.config = dict(app.config.items() + config.items())
    from yak.web import views
    app.run(host='0.0.0.0', port=app.config['PORT'])
