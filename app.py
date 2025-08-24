from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import sqlite3
import os
import uuid
import random
import string
import openpyxl

app = Flask(__name__)
app.secret_key = "supersecretkey" # برای session ادمین

# 📂 مسیر آپلود
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# 📌 ایجاد دیتابیس
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
                  file_paths TEXT,
                  tracking_code TEXT)''')
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

        # 📂 ساخت پوشه بر اساس کد ملی
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], national_id)
        os.makedirs(user_folder, exist_ok=True)

        file_paths = []
        # ۴ مدرک (اولی اجباری)
        for i in range(1, 5):
            file = request.files.get(f"file{i}")
            if file and file.filename != "":
                ext = os.path.splitext(file.filename)[1]
                saved_filename = f"{uuid.uuid4().hex}{ext}"
                file_path = os.path.join(user_folder, saved_filename)
                file.save(file_path)
                file_paths.append(file_path)

        # اجباری بودن فایل اول
        if len(file_paths) == 0:
            return "❌ آپلود مدرک اول الزامی است."

        # 🎲 کد پیگیری ۱۰ رقمی رندوم
        tracking_code = ''.join(random.choices(string.digits, k=10))

        # 💾 ذخیره در دیتابیس
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""INSERT INTO students 
                     (name, family, national_id, phone1, phone2, address, group_name, file_paths, tracking_code)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (name, family, national_id, phone1, phone2, address, group_name, ";".join(file_paths), tracking_code))
        conn.commit()
        conn.close()

        return f"✅ ثبت‌نام با موفقیت انجام شد.<br> کد پیگیری شما: <b>{tracking_code}</b>"

    return render_template("form.html")


# 🔑 ورود به پنل مدیریت
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if "admin" in session and session["admin"] == True:
        return admin_panel()

    if request.method == "POST":
        password = request.form.get("password")
        if password == "2802":
            session["admin"] = True
            return admin_panel()
        else:
            flash("❌ رمز عبور اشتباه است. فقط ادمین اجازه ورود دارد.")
            return render_template("admin_login.html")

    return render_template("admin_login.html")


# 📊 پنل مدیریت
def admin_panel():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    rows = c.fetchall()
    conn.close()
    return render_template("admin.html", rows=rows)


# ❌ حذف رکورد
@app.route("/delete/<int:student_id>")
def delete(student_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_login"))


# 📤 خروجی اکسل
@app.route("/export")
def export_excel():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    rows = c.fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students"

    # سرستون‌ها
    headers = ["ID", "نام", "نام خانوادگی", "کد ملی", "تلفن ۱", "تلفن ۲", "آدرس", "گروه", "مدارک", "کد پیگیری"]
    ws.append(headers)

    for row in rows:
        ws.append(row)

    file_path = "students.xlsx"
    wb.save(file_path)
    return send_file(file_path, as_attachment=True)


# ▶️ اجرا محلی
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
