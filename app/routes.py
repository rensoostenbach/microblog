from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from app.models import User
import numpy as np
import keras.models
import re
import sys
import os
import os.path
import base64
sys.path.append(os.path.abspath('./model'))
from load import *
from datetime import datetime

UPLOAD_FOLDER = 'app/static/uploads/'
RESULT_FOLDER = '/static/results/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'tiff'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

global model, graph
model, graph = init()

@app.route('/')
@app.route('/index')
@login_required
def index():
	return render_template('index.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return predict(filename)
    return render_template('upload.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You were logged out')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/result/', methods=['POST'])
def result():
    return render_template('result.html')

@app.route('/contact/')
def contact():
    return render_template('contact.html')

@app.route('/portfolio/')
def portfolio():
    return render_template('portfolio.html')

@app.route('/predict/', methods=['GET', 'POST'])
def predict(file):
	#imgData = request.get_data()
	#convertImage(imgData)
	#print "debug"
  x = imread(os.path.join(app.config['UPLOAD_FOLDER'], file), mode = 'RGB')
	#x = np.invert(x)
  x = imresize(x,(299, 299))
  x = x/255
	#x = x.reshape(1, 299, 299, 3)
  x1 = np.zeros((1, 299, 299, 3))
  x1[0] = x
	#print "debug2"
  with graph.as_default():
		#perform the prediction
    out = model.predict(x1)
    print(out)
    print(np.argmax(out,axis=1))
		#print "debug3"
		#convert the response to a string
    output1 = np.array_str(out) + '\n' + np.array_str(np.argmax(out,axis=1))
    output2 = out[0]
    output2 = output2[0]
    output2_1 = str(round(output2*100, 3))
    output2_2 = out[0]
    output2_2 = output2_2[1]
    output2_3 = str(round(output2_2*100, 3))
    if output2 >= 0.85:
        output3 = "We are " + output2_1 + "% sure it's a cat!"
        output = os.path.join(app.config['RESULT_FOLDER'], 'cat.png')
    elif output2 <= 0.15:
        output3 = "We are " + output2_3 + "% sure it's a dog!"
        output = os.path.join(app.config['RESULT_FOLDER'], 'dog.jpg')
    else:
        output3 = "We aren't sure :("
        output = os.path.join(app.config['RESULT_FOLDER'], 'unsure.jpg')
        #output.show()
    return render_template('result.html', output3=output3, output=output)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

poll_data = {
   'question' : 'Which animal do you prefer?',
   'fields'   : ['Cat', 'Dog', 'Other']
}
polltxt = 'data.txt'

@app.route('/question')
@login_required
def question():
    return render_template('poll.html', data=poll_data)

@app.route('/poll')
@login_required
def poll():
    vote = request.args.get('field')

    out = open(polltxt, 'a')
    out.write( vote + '\n' )
    out.close()

    return render_template('thankyou.html', data=poll_data)

@app.route('/pollresults')
def show_results():
    votes = {}
    for f in poll_data['fields']:
        votes[f] = 0

    f  = open(polltxt, 'r')
    for line in f:
        vote = line.rstrip("\n")
        votes[vote] += 1

    return render_template('pollresults.html', data=poll_data, votes=votes)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

if __name__ == '__main__':
    app.run()
	#port = int(os.environ.get('PORT', 5000))
	#app.run(host='0.0.0.0', port=port)
	#optional if we want to run in debugging mode
	#app.run(debug=True)
