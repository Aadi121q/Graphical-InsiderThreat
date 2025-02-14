from flask import Flask, render_template, redirect, url_for, request, session, flash, g, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import datetime
import csv
from functools import wraps
import boto3
from botocore.exceptions import NoCredentialsError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
DATABASE = 'users_db.sqlite'
LOG_FILE = 'user_activities.csv'
UPLOAD_FOLDER = 'uploads'
CITIZENSHIP_FOLDER = os.path.join(UPLOAD_FOLDER, 'citizenship')
PHOTOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'photos')
WEB_FOLDER = os.path.join(UPLOAD_FOLDER, 'web')
FINANCIAL_FOLDER = os.path.join(UPLOAD_FOLDER, 'financial_reports')
GOVERNMENT_FOLDER = os.path.join(UPLOAD_FOLDER, 'government_orders')
CONTRACTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'contracts_agreements')
CRIME_FOLDER = os.path.join(UPLOAD_FOLDER, 'crime_reports')
VISA_FOLDER = os.path.join(UPLOAD_FOLDER, 'visa_work')
DEPORTATION_FOLDER = os.path.join(UPLOAD_FOLDER, 'deportation_blacklist')

# Ensure the upload folders exist
os.makedirs(CITIZENSHIP_FOLDER, exist_ok=True)
os.makedirs(PHOTOS_FOLDER, exist_ok=True)
os.makedirs(WEB_FOLDER, exist_ok=True)
os.makedirs(FINANCIAL_FOLDER, exist_ok=True)
os.makedirs(GOVERNMENT_FOLDER, exist_ok=True)
os.makedirs(CONTRACTS_FOLDER, exist_ok=True)
os.makedirs(CRIME_FOLDER, exist_ok=True)
os.makedirs(VISA_FOLDER, exist_ok=True)
os.makedirs(DEPORTATION_FOLDER, exist_ok=True)

# AWS S3 Configuration
S3_BUCKET = 'insideraadi' 
S3_ACCESS_KEY = 'AKIAYENHGH35RYXZLJT7' 
S3_SECRET_KEY = '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'
S3_REGION = 'us-east-1'  

# Initialize the database and create the users and logs table if it doesn't exist
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                timestamp TEXT,
                details TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        db.commit()

# Get database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Log user activity
def log_activity(action, details=None):
    if 'user_id' in session:
        timestamp = datetime.datetime.now().strftime('%m/%d %H:%M')
        user_id = session.get('user_id', None)
        username = session.get('username', 'Unknown')

        log_entry = [user_id, username, action, timestamp, details]

        # Append to CSV log file
        with open(LOG_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(log_entry)

# Decorator to require login for specific routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Upload file to AWS S3
def upload_to_s3(file, folder, bucket_name):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=S3_REGION
    )

    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            f"{folder}/{file.filename}",
            ExtraArgs={
                "ContentType": file.content_type
            }
        )
    except NoCredentialsError:
        return False
    return True

# Route for the home page
@app.route('/')
def home():
    citizenship_files = os.listdir(CITIZENSHIP_FOLDER)
    photo_files = os.listdir(PHOTOS_FOLDER)
    web_files = os.listdir(WEB_FOLDER)
    financial_files = os.listdir(FINANCIAL_FOLDER)
    government_files = os.listdir(GOVERNMENT_FOLDER)
    contracts_files = os.listdir(CONTRACTS_FOLDER)
    crime_files = os.listdir(CRIME_FOLDER)
    visa_files = os.listdir(VISA_FOLDER)
    deportation_files = os.listdir(DEPORTATION_FOLDER)
    return render_template('home.html', 
                           citizenship_files=citizenship_files, 
                           photo_files=photo_files, 
                           web_files=web_files, 
                           financial_files=financial_files,
                           government_files=government_files,
                           contracts_files=contracts_files,
                           crime_files=crime_files,
                           visa_files=visa_files,
                           deportation_files=deportation_files)

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            log_activity('Login', f"User logged in: {username}")
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

# Route for the dashboard page
@app.route('/dashboard')
@login_required
def dashboard():
    citizenship_files = os.listdir(CITIZENSHIP_FOLDER)
    photo_files = os.listdir(PHOTOS_FOLDER)
    web_files = os.listdir(WEB_FOLDER)
    financial_files = os.listdir(FINANCIAL_FOLDER)
    government_files = os.listdir(GOVERNMENT_FOLDER)
    contracts_files = os.listdir(CONTRACTS_FOLDER)
    crime_files = os.listdir(CRIME_FOLDER)
    visa_files = os.listdir(VISA_FOLDER)
    deportation_files = os.listdir(DEPORTATION_FOLDER)
    return render_template('admin_panel.html', 
                           citizenship_files=citizenship_files, 
                           photo_files=photo_files, 
                           web_files=web_files,
                           financial_files=financial_files,
                           government_files=government_files,
                           contracts_files=contracts_files,
                           crime_files=crime_files,
                           visa_files=visa_files,
                           deportation_files=deportation_files)

# Route to upload files
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    folder = request.form['folder']
    file = request.files['file']
    if file:
        folder_paths = {
            'citizenship': CITIZENSHIP_FOLDER,
            'photos': PHOTOS_FOLDER,
            'web': WEB_FOLDER,
            'financial_reports': FINANCIAL_FOLDER,
            'government_orders': GOVERNMENT_FOLDER,
            'contracts_agreements': CONTRACTS_FOLDER,
            'crime_reports': CRIME_FOLDER,
            'visa_work': VISA_FOLDER,
            'deportation_blacklist': DEPORTATION_FOLDER
        }

        # Save file to local folder
        file_path = os.path.join(folder_paths[folder], file.filename)
        file.save(file_path)
        file_size = os.path.getsize(file_path)

        # Upload to AWS S3
        file.seek(0)  # Reset file pointer to the beginning
        if upload_to_s3(file, folder, S3_BUCKET):
            log_activity('File Uploaded to S3', f"{folder}: {file.filename}, Size: {file_size} bytes")
        else:
            log_activity('Failed to Upload File to S3', f"{folder}: {file.filename}, Size: {file_size} bytes")

        log_activity('File Uploaded', f"{folder}: {file.filename}, Size: {file_size} bytes")
        flash('File uploaded successfully')
    return redirect(url_for('dashboard'))

# Route to download files
@app.route('/download/<folder>/<filename>')
@login_required
def download_file(folder, filename):
    folder_paths = {
        'citizenship': CITIZENSHIP_FOLDER,
        'photos': PHOTOS_FOLDER,
        'web': WEB_FOLDER,
        'financial_reports': FINANCIAL_FOLDER,
        'government_orders': GOVERNMENT_FOLDER,
        'contracts_agreements': CONTRACTS_FOLDER,
        'crime_reports': CRIME_FOLDER,
        'visa_work': VISA_FOLDER,
        'deportation_blacklist': DEPORTATION_FOLDER
    }
    folder_path = folder_paths.get(folder, CITIZENSHIP_FOLDER)
    file_path = os.path.join(folder_path, filename)
    file_size = os.path.getsize(file_path)
    log_activity('File Downloaded', f"{folder}: {filename}, Size: {file_size} bytes")
    return send_from_directory(folder_path, filename)

# Route to delete files
@app.route('/delete/<folder>/<filename>', methods=['POST'])
@login_required
def delete_file(folder, filename):
    folder_paths = {
        'citizenship': CITIZENSHIP_FOLDER,
        'photos': PHOTOS_FOLDER,
        'web': WEB_FOLDER,
        'financial_reports': FINANCIAL_FOLDER,
        'government_orders': GOVERNMENT_FOLDER,
        'contracts_agreements': CONTRACTS_FOLDER,
        'crime_reports': CRIME_FOLDER,
        'visa_work': VISA_FOLDER,
        'deportation_blacklist': DEPORTATION_FOLDER
    }
    folder_path = folder_paths.get(folder, CITIZENSHIP_FOLDER)
    file_path = os.path.join(folder_path, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        log_activity('File Deleted', f"{folder}: {filename}")
        flash('File deleted successfully')
    else:
        flash('File not found')
    return redirect(url_for('dashboard'))

# Route to edit files
@app.route('/edit', methods=['POST'])
@login_required
def edit_file():
    folder = request.form['folder']
    file_name = request.form['file_name']
    new_file_name = request.form['new_file_name']
    folder_paths = {
        'citizenship': CITIZENSHIP_FOLDER,
        'photos': PHOTOS_FOLDER,
        'web': WEB_FOLDER,
        'financial_reports': FINANCIAL_FOLDER,
        'government_orders': GOVERNMENT_FOLDER,
        'contracts_agreements': CONTRACTS_FOLDER,
        'crime_reports': CRIME_FOLDER,
        'visa_work': VISA_FOLDER,
        'deportation_blacklist': DEPORTATION_FOLDER
    }
    folder_path = folder_paths.get(folder, CITIZENSHIP_FOLDER)
    file_path = os.path.join(folder_path, file_name)
    new_file_path = os.path.join(folder_path, new_file_name)

    # Rename the file if the new file name is different
    if new_file_name and new_file_name != file_name:
        os.rename(file_path, new_file_path)
        file_path = new_file_path
        log_activity('File Renamed', f"{folder}: {file_name} -> {new_file_name}")

    flash('File edited successfully')
    return redirect(url_for('dashboard'))

# Route to fetch files for a specific folder
@app.route('/files/<folder>')
@login_required
def get_files(folder):
    folder_paths = {
        'citizenship': CITIZENSHIP_FOLDER,
        'photos': PHOTOS_FOLDER,
        'web': WEB_FOLDER,
        'financial_reports': FINANCIAL_FOLDER,
        'government_orders': GOVERNMENT_FOLDER,
        'contracts_agreements': CONTRACTS_FOLDER,
        'crime_reports': CRIME_FOLDER,
        'visa_work': VISA_FOLDER,
        'deportation_blacklist': DEPORTATION_FOLDER
    }
    folder_path = folder_paths.get(folder, CITIZENSHIP_FOLDER)
    files = os.listdir(folder_path)
    return jsonify(files)

# Route to logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    log_activity('Logout')
    return redirect(url_for('login'))

# Routes for each service page
@app.route('/citizenship')
@login_required
def citizenship():
    citizenship_files = os.listdir(CITIZENSHIP_FOLDER)
    return render_template('citizenship.html', citizenship_files=citizenship_files)

@app.route('/financial_reports')
@login_required
def financial_reports():
    financial_files = os.listdir(FINANCIAL_FOLDER)
    return render_template('financial_reports.html', financial_files=financial_files)

@app.route('/birth_certificates')
@login_required
def birth_certificates():
    photo_files = os.listdir(PHOTOS_FOLDER)
    return render_template('birth_certificates.html', photo_files=photo_files)

@app.route('/government_orders')
@login_required
def government_orders():
    government_files = os.listdir(GOVERNMENT_FOLDER)
    return render_template('government_orders.html', government_files=government_files)

@app.route('/contracts_agreements')
@login_required
def contracts_agreements():
    contracts_files = os.listdir(CONTRACTS_FOLDER)
    return render_template('contracts_agreements.html', contracts_files=contracts_files)

@app.route('/crime_reports')
@login_required
def crime_reports():
    crime_files = os.listdir(CRIME_FOLDER)
    return render_template('crime_reports.html', crime_files=crime_files)

@app.route('/visa_work')
@login_required
def visa_work():
    visa_files = os.listdir(VISA_FOLDER)
    return render_template('visa_work.html', visa_files=visa_files)

@app.route('/deportation_blacklist')
@login_required
def deportation_blacklist():
    deportation_files = os.listdir(DEPORTATION_FOLDER)
    return render_template('deportation_blacklist.html', deportation_files=deportation_files)

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    # Initialize the CSV log file with headers if it doesn't exist
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['user_id', 'username', 'action', 'timestamp', 'details'])
    app.run(debug=True)