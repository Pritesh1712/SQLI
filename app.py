from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, make_response
import joblib
import os 
import sys
from datetime import datetime
from xhtml2pdf import pisa
from io import BytesIO

app = Flask(__name__)

# Talisman(app, content_security_policy={
#     'default-src': ["'self'"],
#     'style-src': ["'self'", 'https://fonts.googleapis.com', "'unsafe-inline'"],
#     'font-src': ['https://fonts.gstatic.com'],
#     'script-src': ["'self'", 'https://cdn.jsdelivr.net', "'unsafe-inline'"]
# })

app.secret_key = 'your_secret_key'
# model = joblib.load(os.path.join('sqli_model.pkl'))
# vectorizer = joblib.load(os.path.join('vectorizer.pkl'))
# ✅ Determine base path (PyInstaller-compatible)
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Load model & vectorizer using absolute paths
model_path = os.path.join(BASE_DIR, 'sqli_model.pkl')
vectorizer_path = os.path.join(BASE_DIR, 'vectorizer.pkl')

model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input = request.form.get('user_input')

        vectorized_input = vectorizer.transform([user_input])
        # result = model.predict(vectorized_input)[0]
        
        # session['prediction'] = result  
        # save_log(user_input, result)
        result = model.predict(vectorized_input)[0]
        label = "Safe" if result == 0 else "Attack"

        session['prediction'] = label  
        save_log(user_input, label)

        return redirect(url_for('index'))   
    
    prediction = session.pop('prediction', None)  
    return render_template('index.html', prediction=prediction)

log_file = "logs.txt"

def save_log(user_input, prediction):
    ip = request.remote_addr
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"{user_input}|{prediction}|{ip}|{time}\n")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == 'admin123':  # example
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    downloaded = request.args.get('downloaded') == 'true'

    logs = []
    safe = 0
    attack = 0

    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            for line in f.readlines():
                parts = line.strip().split("|")
                if len(parts) == 4:
                    logs.append(tuple(parts))
                    if parts[1] == "Safe":
                        safe += 1
                    else:
                        attack += 1

    total = safe + attack

    return render_template(
        'dashboard.html',
        total=total,
        safe=safe,
        attack=attack,
        logs=logs,
        downloaded=downloaded
    )

@app.route('/download_logs')
def download_logs():
    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            for line in f.readlines():
                parts = line.strip().split("|")
                if len(parts) == 4:
                    logs.append(tuple(parts))

    html = render_template("logs_pdf_template.html", logs=logs)

    # Convert to PDF
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_file)

    if pisa_status.err:
        return "Error generating PDF", 500

    # ✅ Save PDF manually to Downloads folder
    downloads_path = str(Path.home() / "Downloads")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"recent_logs_{timestamp}.pdf"
    filepath = os.path.join(downloads_path, filename)

    with open(filepath, "wb") as f:
        f.write(pdf_file.getvalue())

    return redirect(url_for('dashboard', downloaded='true', filename=filename))

@app.route('/logout')
def logout():
    session.clear()  
    return redirect(url_for('index'))  

# @app.after_request
# def set_security_headers(response):
#     response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; object-src 'none'"
#     response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
#     response.headers['X-Content-Type-Options'] = 'nosniff'
#     response.headers['X-Frame-Options'] = 'DENY'
#     response.headers['Referrer-Policy'] = 'no-referrer'
#     response.headers['Permissions-Policy'] = 'geolocation=(), microphone=()'
#     return response


@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self'; "
        "object-src 'none'"
    )
    return response


if __name__ == '__main__':
    app.run(debug=True)
