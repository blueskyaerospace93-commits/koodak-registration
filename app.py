from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import uuid

app = Flask(__name__)

# 📂 تنظیمات پوشه آپلود
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # اگر نبود، بساز
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# 📌 ایجاد جدول دیتابیس در صورت نبود
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  family TEXT,
                  national_id TEXT,
                  phone1 TEXT,
                  phone2 TEXT,
                  address TEXT,
                  group_name TEXT,
                  file_path TEXT)''')
    conn.commit()
    conn.close()

init_db()


# 📝 فرم ثبت‌نام
@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "")
        family = request.form.get("family", "")
        national_id = request.form.get("national_id", "")
        phone1 = request.form.get("phone1", "")
        phone2 = request.form.get("phone2", "")
        address = request.form.get("address", "")
        group_name = request.form.get("group_name", "")

        # 📂 ذخیره فایل آپلودشده
        file_path = ""
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename != "":
                ext = os.path.splitext(file.filename)[1]
                saved_filename = f"{uuid.uuid4().hex}{ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
                file.save(file_path)

        # 💾 ذخیره در دیتابیس
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO students (name, family, national_id, phone1, phone2, address, group_name, file_path) VALUES (?,?,?,?,?,?,?,?)",
                  (name, family, national_id, phone1, phone2, address, group_name, file_path))
        conn.commit()
        conn.close()

        return redirect(url_for("register")) # بعد از ثبت، دوباره به فرم برگرده

    return render_template("form.html")


# 📊 پنل مدیریت
@app.route("/admin")
def admin():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    rows = c.fetchall()
    conn.close()
    return render_template("admin.html", rows=rows)


# ❌ حذف رکورد
@app.route("/delete/<int:student_id>")
def delete(student_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


# ▶️ اجرای محلی
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
