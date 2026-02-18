from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import random
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key")

DATABASE = "users.db"


# ---------------- DATABASE ---------------- #

def get_db():
    return sqlite3.connect(DATABASE)


def init_db():
    con = get_db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        verification_code TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT
    )
    """)

    con.commit()
    con.close()


init_db()


# ---------------- EMAIL FUNCTION ---------------- #

def send_verification_email(receiver_email, code):
    smtp_email = os.environ.get("SMTP_EMAIL")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    if not smtp_email or not smtp_password:
        print("SMTP credentials missing")
        return

    subject = "Your Verification Code"
    body = f"Your verification code is: {code}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_email
    msg["To"] = receiver_email

    try:
        server = smtplib.SMTP("smtp.office365.com", 587)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, receiver_email, msg.as_string())
        server.quit()
    except Exception as e:
        print("Email send error:", e)


# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return render_template("index.html")


# -------- CREATE ACCOUNT -------- #

@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        con = get_db()
        cur = con.cursor()

        try:
            cur.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password),
            )
            con.commit()

            # Auto login
            cur.execute("SELECT id FROM users WHERE email = ?", (email,))
            user = cur.fetchone()
            session["user_id"] = user[0]

        except sqlite3.IntegrityError:
            con.close()
            return "Email already exists."

        con.close()
        return redirect(url_for("main"))

    return render_template("create_account.html")


# -------- LOGIN -------- #

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        con = get_db()
        cur = con.cursor()

        cur.execute(
            "SELECT id FROM users WHERE email = ? AND password = ?",
            (email, password),
        )
        user = cur.fetchone()

        if not user:
            con.close()
            return "Invalid email or password."

        code = str(random.randint(100000, 999999))

        cur.execute(
            "UPDATE users SET verification_code = ? WHERE email = ?",
            (code, email),
        )
        con.commit()
        con.close()

        send_verification_email(email, code)

        session["pending_user"] = user[0]
        session["pending_email"] = email

        masked_email = email[:2] + "********" + email[email.index("@"):]

        return render_template("verify.html", masked_email=masked_email)

    return render_template("login.html")


# -------- VERIFY CODE -------- #

@app.route("/verify", methods=["POST"])
def verify():
    code = request.form["code"]
    user_id = session.get("pending_user")

    if not user_id:
        return redirect(url_for("login"))

    con = get_db()
    cur = con.cursor()

    cur.execute(
        "SELECT verification_code FROM users WHERE id = ?",
        (user_id,),
    )
    user = cur.fetchone()

    if user and user[0] == code:
        session["user_id"] = user_id
        session.pop("pending_user", None)
        session.pop("pending_email", None)
        con.close()
        return redirect(url_for("main"))

    con.close()
    return "Invalid verification code."


# -------- MAIN -------- #

@app.route("/main")
def main():
    if "user_id" not in session:
        return redirect(url_for("home"))
    return render_template("main.html")


# -------- STORY -------- #

@app.route("/story", methods=["GET", "POST"])
def story():
    if "user_id" not in session:
        return redirect(url_for("home"))

    user_id = session["user_id"]

    con = get_db()
    cur = con.cursor()

    if request.method == "POST":
        content = request.form["story"]

        cur.execute("DELETE FROM stories WHERE user_id = ?", (user_id,))
        cur.execute(
            "INSERT INTO stories (user_id, content) VALUES (?, ?)",
            (user_id, content),
        )
        con.commit()

    cur.execute("SELECT content FROM stories WHERE user_id = ?", (user_id,))
    story = cur.fetchone()
    con.close()

    story_content = story[0] if story else ""

    return render_template("make_story.html", story_content=story_content)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# -------- RENDER PORT FIX -------- #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
