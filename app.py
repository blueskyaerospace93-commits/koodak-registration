
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import sqlite3, os, uuid
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'database.db')
ALLOWED_EXT = {'png','jpg','jpeg','pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = '1111'  # برای توسعه خوبه، در پروداکشن حتما تغییر بده


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

def init_db():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                family TEXT,
                birthdate TEXT,
                codemelli TEXT,
                parent TEXT,
                phone TEXT,

                address TEXT,
                class TEXT,
                file TEXT
            )
        ''')

@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        file = request.files.get('document')
        saved_filename = ''
        if file and allowed_file(file.filename):
            orig = secure_filename(file.filename)
            saved_filename = f"{uuid.uuid4().hex}_{orig}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_filename))

        data = (
            request.form.get('name',''),

            request.form.get('family',''),
            request.form.get('birthdate',''),
            request.form.get('codemelli',''),
            request.form.get('parent',''),
            request.form.get('phone',''),
            request.form.get('address',''),
            request.form.get('class',''),
            saved_filename
        )

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT INTO registrations (name, family, birthdate, codemelli, parent, phone, address, class, file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)
        flash("ثبتنام با موفقیت انجام شد.", "success")
        return redirect('/thanks')

    return render_template('form.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin')
def admin_panel():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM registrations ORDER BY id DESC')
        rows = cur.fetchall()
    return render_template('admin.html', records=rows)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_record(id):

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT file FROM registrations WHERE id = ?', (id,))
        result = cur.fetchone()
        if result and result[0]:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], result[0])
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    app.logger.warning("Can't remove file: %s", e)
        cur.execute('DELETE FROM registrations WHERE id = ?', (id,))
        conn.commit()
    flash("رکورد حذف شد.", "info")
    return redirect('/admin')

@app.route('/thanks')
def thanks():
    return "<h3 style='text-align:center;margin-top:40px;'>ثبتنام با موفقیت انجام شد. ممنون!</h3>"

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0",port=5000)
        #debug=True)  # در تولید debug=False و از سرور مناسب استفاده کن
