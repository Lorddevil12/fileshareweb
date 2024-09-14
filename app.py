from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
import zipfile
from convertwtp import convert_pdf_to_docx
from convertptw import convert_docx_to_pdf

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

with app.app_context():
    db.create_all()

def create_folder_zip(files):
    folder_id = str(uuid.uuid4())
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_id)
    
    os.makedirs(folder_path)

    for file in files:
        if file.filename:
            file_path = os.path.join(folder_path, file.filename)
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            file.save(file_path)

    zip_filename = folder_id + ".zip"
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))
    
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))
    os.rmdir(folder_path)
    
    return zip_filename

@app.route('/compressor', methods=['GET', 'POST'])
def compressor():
    if 'user_id' not in session:
        flash('You need to log in first')
        return redirect(url_for('login'))

    if request.method == 'POST':
        files = request.files.getlist('files')
        if len(files) == 0:
            flash('No files selected')
            return redirect(request.url)

        zip_filename = create_folder_zip(files)
        flash(f'Files compressed successfully! Download your zip file <a href="{{ url_for("download", filename=zip_filename) }}">here</a>.', 'info')
        return redirect(request.url)

    return render_template('compressor.html')

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Signup successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out')
    return redirect(url_for('login'))

@app.route('/image_converter')
def image_converter():
    return render_template('image.html')

@app.route('/audio_converter')
def audio_converter():
    return render_template('audio.html')

@app.route('/video_converter')
def video_converter():
    return render_template('video.html')

@app.route('/pdf_to_word')
def pdf_to_word():
    return render_template('pdf_to_word.html')

@app.route('/convertptw', methods=['POST'])
def convert_pdf_to_docx_route():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('pdf_to_word'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('pdf_to_word'))
    if file and file.filename.endswith('.pdf'):
        input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        output_path = os.path.join(UPLOAD_FOLDER, file.filename.replace('.pdf', '.docx'))
        file.save(input_path)
        convert_pdf_to_docx(input_path, output_path)
        return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(output_path), as_attachment=True)
    flash('Invalid file format. Only .pdf files are supported.')
    return redirect(url_for('pdf_to_word'))

@app.route('/word_to_pdf')
def word_to_pdf():
    return render_template('word_to_pdf.html')

@app.route('/convertwtp', methods=['POST'])
def convert_docx_to_pdf_route():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('word_to_pdf'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('word_to_pdf'))
    if file and file.filename.endswith('.docx'):
        input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        output_path = os.path.join(UPLOAD_FOLDER, file.filename.replace('.docx', '.pdf'))
        file.save(input_path)
        convert_docx_to_pdf(input_path, output_path)
        return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(output_path), as_attachment=True)
    flash('Invalid file format. Only .docx files are supported.')
    return redirect(url_for('word_to_pdf'))

@app.route('/send', methods=['GET', 'POST'])
def send():
    if 'user_id' not in session:
        flash('You need to log in first')
        return redirect(url_for('login'))

    if request.method == 'POST':
        files = request.files.getlist('files') + request.files.getlist('folder')
        if len(files) == 0:
            flash('No files selected')
            return redirect(request.url)
        
        unique_filename = create_folder_zip(files)
        flash(f'Folder sent successfully! Share this code with the recipient: {unique_filename}')
        return redirect(url_for('index'))

    return render_template('send.html')

@app.route('/receive', methods=['GET', 'POST'])
def receive():
    if 'user_id' not in session:
        flash('You need to log in first')
        return redirect(url_for('login'))

    if request.method == 'POST':
        file_code = request.form['file_code']
        if file_code == '':
            flash('Please enter a file code')
            return redirect(request.url)

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_code)
        if os.path.exists(file_path):
            return send_from_directory(app.config['UPLOAD_FOLDER'], file_code, as_attachment=True)
        else:
            flash('File not found')
            return redirect(request.url)

    return render_template('receive.html')

if __name__ == '__main__':
    app.run(debug=True)
