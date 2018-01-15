from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
#from config import Config
import config
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_login import LoginManager, UserMixin, \
                                login_required, login_user, logout_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from scipy.misc import imsave, imread, imresize
import numpy as np
import keras.models
import re
import sys
import os
import os.path
import base64
sys.path.append(os.path.abspath('./model'))
from load import *

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'tiff'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
login_manager = LoginManager()
#app.config.from_object(Config)
app.config.from_object(app.config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
global model, graph
model, graph = init()
