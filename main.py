import os
from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename
import json
from showcase_scripts.form_extract import extract

UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = { 'jpg' }

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('view_fields', filename=filename))
    return render_template('upload.html')

@app.route('/upload/<string:filename>')
def view_fields(filename=''):
    try:
        # image = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        data, form_id = extract(filename)
        return render_template('view.html', data=data, image=filename, form_id=form_id)

    except Exception as e:
        print(e)
        return redirect(url_for('upload_file'))

@app.route('/tech.html')
def tech():
    return render_template('tech.html')