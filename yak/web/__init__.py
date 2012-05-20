from flask import Flask
app = Flask(__name__)

def run_app(config):
    for key in config:
        app.config[key] = config[key]
    from yak.web import views
    app.run(host='0.0.0.0', port=app.config['PORT'])
