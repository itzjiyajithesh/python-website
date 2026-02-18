from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import random
import os

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
        content TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    con.commit()
    con.close()


init_db()


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
        except sqlite3.IntegrityError:
            con.close()
            return "Email already exists."

        con.close()
        return redirect(url_for("login"))

    return render_template("create_account.html")


# -------- LOGIN STEP 1 -------- #

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]

        con = get_db()
        cur = con.cursor()

        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cur.fetchone()

        if not user:
            con.close()
            return "Email not found."

        code = str(random.randint(100000, 999999))

        cur.execute(
            "UPDATE users SET verification_code = ? WHERE email = ?",
            (code, email),
        )
        con.commit()
        con.close()

        session["pending_email"] = email

        # Simulated email (check Render logs to see the code)
        print("Verification Code:", code)

        return redirect(url_for("verify"))

    return render_template("login.html")


# -------- LOGIN STEP 2 -------- #

@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        code = request.form["code"]
        password = request.form["password"]
        email = session.get("pending_email")

        if not email:
            return redirect(url_for("login"))

        con = get_db()
        cur = con.cursor()

        cur.execute(
            "SELECT id, verification_code, password FROM users WHERE email = ?",
            (email,),
        )
        user = cur.fetchone()

        if user and user[1] == code and user[2] == password:
            session["user_id"] = user[0]
            session.pop("pending_email", None)
            con.close()
            return redirect(url_for("main"))

        con.close()
        return "Invalid code or password."

    return render_template("verify.html")


# -------- MAIN PAGE -------- #

@app.route("/main")
def main():
    if "user_id" not in session:
        return redirect(url_for("home"))

    return render_template("main.html")


# -------- STORY PAGE -------- #

@app.route("/story", methods=["GET", "POST"])
def story():
    if "user_id" not in session:
        return redirect(url_for("home"))

    user_id = session["user_id"]

    con = get_db()
    cur = con.cursor()

    if request.method == "POST":
        content = request.form["story"]

        # Remove previous story (1 story per user)
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


# -------- LOGOUT -------- #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# -------- RENDER PORT FIX -------- #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
