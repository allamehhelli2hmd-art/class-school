import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


# =========================================================
# APP CONFIG
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)

database_url = os.environ.get(
    "DATABASE_URL",
    "sqlite:///school.db"
)

# Render/PostgreSQL sometimes provides postgres://
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================================================
# DATABASE MODELS
# =========================================================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="student"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    grades = db.relationship(
        "Grade",
        backref="student",
        lazy=True
    )

    def set_password(self, password):

        self.password_hash = generate_password_hash(password)

    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )


class Subject(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    teacher_name = db.Column(
        db.String(120),
        default=""
    )


class Grade(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id"),
        nullable=False
    )

    score = db.Column(
        db.Float,
        nullable=False
    )

    title = db.Column(
        db.String(120),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    subject = db.relationship(
        "Subject"
    )


class Announcement(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    body = db.Column(
        db.Text,
        nullable=False
    )

    author = db.Column(
        db.String(120),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class OnlineClass(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    subject = db.Column(
        db.String(100),
        nullable=False
    )

    meeting_url = db.Column(
        db.String(500),
        nullable=False
    )

    starts_at = db.Column(
        db.DateTime,
        nullable=True
    )


class ScheduleItem(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    weekday = db.Column(
        db.String(30),
        nullable=False
    )

    start_time = db.Column(
        db.String(10),
        nullable=False
    )

    end_time = db.Column(
        db.String(10),
        nullable=False
    )

    subject = db.Column(
        db.String(100),
        nullable=False
    )

    teacher = db.Column(
        db.String(120),
        default=""
    )


# =========================================================
# HELPERS
# =========================================================

def get_current_user():

    user_id = session.get("user_id")

    if not user_id:
        return None

    return db.session.get(
        User,
        user_id
    )


@app.context_processor
def inject_user():

    return {
        "current_user": get_current_user()
    }


def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not get_current_user():

            flash(
                "ابتدا وارد حساب کاربری شوید.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        return function(*args, **kwargs)

    return wrapper


def role_required(*roles):

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            user = get_current_user()

            if not user or user.role not in roles:

                flash(
                    "شما اجازه دسترسی به این بخش را ندارید.",
                    "danger"
                )

                return redirect(
                    url_for("dashboard")
                )

            return function(*args, **kwargs)

        return wrapper

    return decorator


# =========================================================
# HTML TEMPLATE
# =========================================================

BASE_HTML = """
<!DOCTYPE html>

<html lang="fa" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>{{ title }}</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    background: #f4f6fb;

    color: #182230;

    font-family:
        Tahoma,
        Arial,
        sans-serif;
}

.navbar {

    background: #111827;

    color: white;

    padding: 16px 5%;

    display: flex;

    align-items: center;

    gap: 25px;

    flex-wrap: wrap;
}

.logo {

    font-size: 22px;

    font-weight: bold;

    margin-left: auto;
}

.navbar a {

    color: white;

    text-decoration: none;

    opacity: .9;

}

.navbar a:hover {

    opacity: 1;
}

.container {

    width: 92%;

    max-width: 1200px;

    margin: 35px auto;
}

.hero {

    background:
        linear-gradient(
            135deg,
            #111827,
            #273449
        );

    color: white;

    border-radius: 25px;

    padding: 55px;

    margin-bottom: 30px;
}

.hero h1 {

    font-size: 42px;

    margin-top: 0;
}

.hero p {

    color: #d1d5db;

    line-height: 2;

    font-size: 17px;
}

.card-grid {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(220px, 1fr)
        );

    gap: 18px;
}

.card {

    background: white;

    padding: 25px;

    border-radius: 18px;

    box-shadow:
        0 8px 30px
        rgba(0,0,0,.06);
}

.card h3 {

    margin-top: 0;
}

.stat {

    font-size: 32px;

    font-weight: bold;

    margin-bottom: 8px;
}

.btn {

    display: inline-block;

    background: #111827;

    color: white;

    border: none;

    padding: 12px 20px;

    border-radius: 10px;

    text-decoration: none;

    cursor: pointer;
}

.btn:hover {

    background: #273449;
}

.btn-danger {

    background: #b42318;
}

input,
textarea,
select {

    width: 100%;

    padding: 13px;

    border: 1px solid #d8dde6;

    border-radius: 10px;

    margin-bottom: 12px;

    font-family: inherit;
}

label {

    display: block;

    margin-bottom: 6px;

    font-size: 14px;
}

table {

    width: 100%;

    border-collapse: collapse;

    background: white;

    border-radius: 15px;

    overflow: hidden;
}

th,
td {

    padding: 14px;

    text-align: right;

    border-bottom: 1px solid #eee;
}

th {

    background: #f8fafc;
}

.alert {

    padding: 14px;

    border-radius: 10px;

    margin-bottom: 15px;
}

.success {

    background: #eaf8ef;

    color: #146c2e;
}

.danger {

    background: #fff0f0;

    color: #a61b1b;
}

.warning {

    background: #fff7df;

    color: #8a5a00;
}

.login-box {

    max-width: 430px;

    margin: 70px auto;

    background: white;

    padding: 35px;

    border-radius: 20px;

    box-shadow:
        0 15px 50px
        rgba(0,0,0,.08);
}

.notice {

    border-right: 4px solid #111827;

    padding: 15px;

    background: #f8fafc;

    margin-bottom: 12px;

    border-radius: 10px;
}

footer {

    text-align: center;

    padding: 30px;

    color: #8993a5;
}

@media(max-width:700px) {

    .hero {

        padding: 30px;
    }

    .hero h1 {

        font-size: 30px;
    }

    .navbar {

        flex-direction: column;

        align-items: stretch;
    }

}

</style>

</head>

<body>

{% if current_user %}

<nav class="navbar">

<div class="logo">
کلاس من 🎓
</div>

<a href="{{ url_for('dashboard') }}">
داشبورد
</a>

<a href="{{ url_for('grades') }}">
نمرات
</a>

<a href="{{ url_for('online_classes') }}">
کلاس آنلاین
</a>

<a href="{{ url_for('schedule') }}">
برنامه
</a>

<a href="{{ url_for('announcements') }}">
اطلاعیه‌ها
</a>

{% if current_user.role in ["teacher", "admin"] %}

<a href="{{ url_for('students') }}">
دانش‌آموزان
</a>

{% endif %}

<a href="{{ url_for('logout') }}">
خروج
</a>

</nav>

{% endif %}

<main class="container">

{% with messages = get_flashed_messages(with_categories=true) %}

{% for category, message in messages %}

<div class="alert {{ category }}">
{{ message }}
</div>

{% endfor %}

{% endwith %}

{{ content|safe }}

</main>

<footer>

سامانه اختصاصی کلاس
<br>
Python + Flask

</footer>

</body>

</html>
"""


def render_page(content, title="سامانه کلاس"):

    return render_template_string(
        BASE_HTML,
        content=content,
        title=title
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if get_current_user():

        return redirect(
            url_for("dashboard")
        )

    content = """

<div class="hero">

<h1>
سامانه هوشمند کلاس 🎓
</h1>

<p>
یک محیط اختصاصی برای مدیریت کلاس،
نمرات، اطلاعیه‌ها، برنامه هفتگی
و کلاس‌های آنلاین.
</p>

<a class="btn"
   href="/login">
ورود به سامانه
</a>

</div>

<div class="card-grid">

<div class="card">
<h3>📊 نمرات</h3>
<p>
مشاهده و مدیریت نمرات دانش‌آموزان.
</p>
</div>

<div class="card">
<h3>💻 کلاس آنلاین</h3>
<p>
دسترسی سریع به کلاس‌های مجازی.
</p>
</div>

<div class="card">
<h3>📢 اطلاعیه‌ها</h3>
<p>
آخرین اخبار و اطلاعیه‌های کلاس.
</p>
</div>

<div class="card">
<h3>📅 برنامه هفتگی</h3>
<p>
برنامه کلاس‌ها و درس‌ها.
</p>
</div>

</div>
"""

    return render_page(
        content,
        "سامانه کلاس"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if user and user.check_password(password):

            session.clear()

            session["user_id"] = user.id

            flash(
                f"خوش آمدی {user.full_name}!",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "نام کاربری یا رمز عبور اشتباه است.",
            "danger"
        )

    content = """

<div class="login-box">

<h1>
ورود
</h1>

<form method="post">

<label>
نام کاربری
</label>

<input
    name="username"
    required
    autocomplete="username"
>

<label>
رمز عبور
</label>

<input
    name="password"
    type="password"
    required
    autocomplete="current-password"
>

<button class="btn"
        style="width:100%"
        type="submit">

ورود به حساب

</button>

</form>

</div>
"""

    return render_page(
        content,
        "ورود"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    user = get_current_user()

    announcements = (
        Announcement.query
        .order_by(
            Announcement.created_at.desc()
        )
        .limit(5)
        .all()
    )

    classes = (
        OnlineClass.query
        .order_by(
            OnlineClass.id.desc()
        )
        .limit(5)
        .all()
    )

    if user.role == "student":

        grades = (
            Grade.query
            .filter_by(student_id=user.id)
            .order_by(
                Grade.created_at.desc()
            )
            .limit(10)
            .all()
        )

    else:

        grades = (
            Grade.query
            .order_by(
                Grade.created_at.desc()
            )
            .limit(10)
            .all()
        )

    content = f"""

<div class="hero">

<h1>
سلام {user.full_name} 👋
</h1>

<p>
به پنل اختصاصی کلاس خوش آمدی.
</p>

</div>

<div class="card-grid">

<div class="card">

<div class="stat">
📊
</div>

<h3>
نمرات
</h3>

<p>
مشاهده کارنامه و نمرات.
</p>

<a class="btn"
   href="/grades">
مشاهده
</a>

</div>

<div class="card">

<div class="stat">
💻
</div>

<h3>
کلاس آنلاین
</h3>

<p>
ورود به کلاس‌های مجازی.
</p>

<a class="btn"
   href="/online-classes">
مشاهده
</a>

</div>

<div class="card">

<div class="stat">
📅
</div>

<h3>
برنامه
</h3>

<p>
برنامه هفتگی کلاس.
</p>

<a class="btn"
   href="/schedule">
مشاهده
</a>

</div>

<div class="card">

<div class="stat">
📢
</div>

<h3>
اطلاعیه‌ها
</h3>

<p>
آخرین اطلاعیه‌های کلاس.
</p>

<a class="btn"
   href="/announcements">
مشاهده
</a>

</div>

</div>

<br>

<div class="card">

<h2>
آخرین اطلاعیه‌ها
</h2>

"""

    if announcements:

        for item in announcements:

            content += f"""

<div class="notice">

<h3>
{item.title}
</h3>

<p>
{item.body}
</p>

<small>
{item.author}
</small>

</div>

"""

    else:

        content += "<p>هنوز اطلاعیه‌ای ثبت نشده است.</p>"

    content += "</div>"

    return render_page(
        content,
        "داشبورد"
    )


# =========================================================
# GRADES
# =========================================================

@app.route("/grades")
@login_required
def grades():

    user = get_current_user()

    if user.role == "student":

        grades_list = (
            Grade.query
            .filter_by(student_id=user.id)
            .order_by(
                Grade.created_at.desc()
            )
            .all()
        )

    else:

        grades_list = (
            Grade.query
            .order_by(
                Grade.created_at.desc()
            )
            .all()
        )

    content = """

<h1>
📊 نمرات
</h1>

"""

    if user.role in ["teacher", "admin"]:

        students = User.query.filter_by(
            role="student"
        ).all()

        subjects = Subject.query.all()

        content += """

<div class="card">

<h2>
ثبت نمره
</h2>

<form method="post"
      action="/grades/add">

<label>
دانش‌آموز
</label>

<select name="student_id" required>

"""

        for student in students:

            content += f"""

<option value="{student.id}">
{student.full_name}
</option>

"""

        content += """

</select>

<label>
درس
</label>

<select name="subject_id" required>

"""

        for subject in subjects:

            content += f"""

<option value="{subject.id}">
{subject.name}
</option>

"""

        content += """

</select>

<label>
عنوان نمره
</label>

<input
    name="title"
    placeholder="مثلاً آزمون اول"
    required
>

<label>
نمره
</label>

<input
    name="score"
    type="number"
    step="0.01"
    min="0"
    max="20"
    required
>

<button class="btn">
ثبت نمره
</button>

</form>

</div>

<br>

"""

    content += """

<table>

<tr>

<th>
دانش‌آموز
</th>

<th>
درس
</th>

<th>
عنوان
</th>

<th>
نمره
</th>

</tr>

"""

    for grade in grades_list:

        content += f"""

<tr>

<td>
{grade.student.full_name}
</td>

<td>
{grade.subject.name}
</td>

<td>
{grade.title}
</td>

<td>
<strong>
{grade.score}
</strong>
</td>

</tr>

"""

    content += """

</table>
"""

    return render_page(
        content,
        "نمرات"
    )


@app.post("/grades/add")
@role_required("teacher", "admin")
def add_grade():

    student_id = request.form.get(
        "student_id",
        type=int
    )

    subject_id = request.form.get(
        "subject_id",
        type=int
    )

    score = request.form.get(
        "score",
        type=float
    )

    title = request.form.get(
        "title",
        "ارزشیابی"
    )

    if (
        not student_id
        or not subject_id
        or score is None
        or not 0 <= score <= 20
    ):

        flash(
            "اطلاعات نمره صحیح نیست.",
            "danger"
        )

        return redirect(
            url_for("grades")
        )

    db.session.add(
        Grade(
            student_id=student_id,
            subject_id=subject_id,
            score=score,
            title=title
        )
    )

    db.session.commit()

    flash(
        "نمره با موفقیت ثبت شد.",
        "success"
    )

    return redirect(
        url_for("grades")
    )


# =========================================================
# STUDENTS
# =========================================================

@app.route("/students")
@role_required("teacher", "admin")
def students():

    users = (
        User.query
        .filter_by(role="student")
        .order_by(User.full_name)
        .all()
    )

    content = """

<h1>
👨‍🎓 دانش‌آموزان
</h1>

<div class="card">

<table>

<tr>

<th>
شناسه
</th>

<th>
نام
</th>

<th>
نام کاربری
</th>

</tr>

"""

    for user in users:

        content += f"""

<tr>

<td>
{user.id}
</td>

<td>
{user.full_name}
</td>

<td>
{user.username}
</td>

</tr>

"""

    content += """

</table>

</div>
"""

    return render_page(
        content,
        "دانش‌آموزان"
    )


# =========================================================
# ANNOUNCEMENTS
# =========================================================

@app.route("/announcements")
@login_required
def announcements():

    items = (
        Announcement.query
        .order_by(
            Announcement.created_at.desc()
        )
        .all()
    )

    user = get_current_user()

    content = """

<h1>
📢 اطلاعیه‌ها
</h1>

"""

    if user.role in ["teacher", "admin"]:

        content += """

<div class="card">

<h2>
ایجاد اطلاعیه
</h2>

<form method="post"
      action="/announcements/add">

<label>
عنوان
</label>

<input
    name="title"
    required
>

<label>
متن
</label>

<textarea
    name="body"
    rows="5"
    required
></textarea>

<button class="btn">
انتشار
</button>

</form>

</div>

<br>

"""

    for item in items:

        content += f"""

<div class="card">

<h2>
{item.title}
</h2>

<p>
{item.body}
</p>

<small>
نویسنده: {item.author}
</small>

</div>

<br>

"""

    return render_page(
        content,
        "اطلاعیه‌ها"
    )


@app.post("/announcements/add")
@role_required("teacher", "admin")
def add_announcement():

    title = request.form.get(
        "title",
        ""
    ).strip()

    body = request.form.get(
        "body",
        ""
    ).strip()

    if title and body:

        db.session.add(
            Announcement(
                title=title,
                body=body,
                author=get_current_user().full_name
            )
        )

        db.session.commit()

        flash(
            "اطلاعیه منتشر شد.",
            "success"
        )

    return redirect(
        url_for("announcements")
    )


# =========================================================
# ONLINE CLASSES
# =========================================================

@app.route("/online-classes")
@login_required
def online_classes():

    classes = (
        OnlineClass.query
        .order_by(
            OnlineClass.id.desc()
        )
        .all()
    )

    user = get_current_user()

    content = """

<h1>
💻 کلاس‌های آنلاین
</h1>

"""

    if user.role in ["teacher", "admin"]:

        content += """

<div class="card">

<h2>
افزودن کلاس آنلاین
</h2>

<form method="post"
      action="/online-classes/add">

<label>
عنوان
</label>

<input
    name="title"
    required
>

<label>
درس
</label>

<input
    name="subject"
    required
>

<label>
لینک کلاس
</label>

<input
    name="meeting_url"
    type="url"
    placeholder="https://..."
    required
>

<button class="btn">
افزودن کلاس
</button>

</form>

</div>

<br>

"""

    content += '<div class="card-grid">'

    for online_class in classes:

        content += f"""

<div class="card">

<h2>
{online_class.title}
</h2>

<p>
درس: {online_class.subject}
</p>

<a
    class="btn"
    href="{online_class.meeting_url}"
    target="_blank"
>
ورود به کلاس
</a>

</div>

"""

    content += "</div>"

    return render_page(
        content,
        "کلاس آنلاین"
    )


@app.post("/online-classes/add")
@role_required("teacher", "admin")
def add_online_class():

    title = request.form.get(
        "title",
        ""
    ).strip()

    subject = request.form.get(
        "subject",
        ""
    ).strip()

    meeting_url = request.form.get(
        "meeting_url",
        ""
    ).strip()

    if title and subject and meeting_url:

        db.session.add(
            OnlineClass(
                title=title,
                subject=subject,
                meeting_url=meeting_url
            )
        )

        db.session.commit()

        flash(
            "کلاس آنلاین اضافه شد.",
            "success"
        )

    return redirect(
        url_for("online_classes")
    )


# =========================================================
# SCHEDULE
# =========================================================

@app.route("/schedule")
@login_required
def schedule():

    items = ScheduleItem.query.all()

    content = """

<h1>
📅 برنامه هفتگی
</h1>

<div class="card-grid">

"""

    for item in items:

        content += f"""

<div class="card">

<h3>
{item.weekday}
</h3>

<h2>
{item.subject}
</h2>

<p>
{item.start_time}
تا
{item.end_time}
</p>

<p>
{item.teacher}
</p>

</div>

"""

    content += "</div>"

    return render_page(
        content,
        "برنامه هفتگی"
    )


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def initialize_database():

    db.create_all()

    # Admin
    if not User.query.filter_by(
        username="admin"
    ).first():

        admin = User(
            username="admin",
            full_name="مدیر کلاس",
            role="admin"
        )

        admin.set_password(
            os.environ.get(
                "ADMIN_INITIAL_PASSWORD",
                "ChangeMe123!"
            )
        )

        db.session.add(admin)

    # Subjects
    if Subject.query.count() == 0:

        subjects = [
            "ریاضی",
            "فیزیک",
            "شیمی",
            "ادبیات",
            "زبان",
            "دینی",
            "عربی"
        ]

        for name in subjects:

            db.session.add(
                Subject(
                    name=name
                )
            )

    # Welcome announcement
    if Announcement.query.count() == 0:

        db.session.add(
            Announcement(
                title="به سامانه کلاس خوش آمدید 🎓",
                body=(
                    "این سامانه برای مدیریت "
                    "کلاس، نمرات، اطلاعیه‌ها "
                    "و کلاس‌های آنلاین ساخته شده است."
                ),
                author="مدیر کلاس"
            )
        )

    # Sample schedule
    if ScheduleItem.query.count() == 0:

        schedule = [

            ("شنبه", "08:00", "09:30", "ریاضی"),
            ("شنبه", "10:00", "11:30", "فیزیک"),
            ("یکشنبه", "08:00", "09:30", "شیمی"),
            ("یکشنبه", "10:00", "11:30", "ادبیات"),
            ("دوشنبه", "08:00", "09:30", "زبان"),
            ("دوشنبه", "10:00", "11:30", "عربی"),

        ]

        for item in schedule:

            db.session.add(
                ScheduleItem(
                    weekday=item[0],
                    start_time=item[1],
                    end_time=item[2],
                    subject=item[3]
                )
            )

    db.session.commit()


with app.app_context():

    initialize_database()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
