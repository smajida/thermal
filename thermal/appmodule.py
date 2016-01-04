import socket

from celery import Celery
import couchdb
from flask import g, Flask

from config import config, Config

celery = Celery('thermal', broker=Config.CELERY_BROKER_URL)

def create_app(config_name='development'):
    app = Flask('thermal')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    app.config['HOSTNAME'] = socket.gethostname()

    register_blueprints(app)
    register_db(app)

#    @app.before_request
#    def before_request():
#        couch = couchdb.Server()
#        db = couch['thermal']
#        g.db = db
#
    return app

def register_db(app):
    couch = couchdb.Server()
    app.db = couch['thermal']

def register_blueprints(app):
    from admin.views import admin
    from camera.views import camera
    from crap.controller import crap
    from picture.views import picture
    app.register_blueprint(camera, url_prefix='/camera')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(picture, url_prefix='/pictures')
    app.register_blueprint(crap, url_prefix='/crap')

def make_celery(app):
    celery = Celery('thermal', broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery
