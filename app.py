from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
import hashlib

app = Flask(__name__)
app.secret_key = "secret123"

DATABASE = "users.db"


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
        password TEXT
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()

        con = get_db()
        cur = con.cursor()

        try:
            cur.execute(
                "INSERT INTO users (name,email,password) VALUES (?,?,?)",
                (name, email, password),
            )
            con.commit()

        except:
            return "Email already exists"

        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        user = cur.fetchone()

        session["user_id"] = user[0]
        session["name"] = name

        return redirect("/main")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()

        con = get_db()
        cur = con.cursor()

        cur.execute(
            "SELECT id,name FROM users WHERE email=? AND password=?",
            (email, password),
        )

        user = cur.fetchone()

        if user:
            session["user_id"] = user[0]
            session["name"] = user[1]
            return redirect("/main")

        return "Invalid login"

    return render_template("login.html")


@app.route("/main")
def main():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("main.html", name=session["name"])


@app.route("/story", methods=["GET", "POST"])
def story():

    if "user_id" not in session:
        return redirect("/login")

    con = get_db()
    cur = con.cursor()

    if request.method == "POST":

        content = request.form["content"]

        cur.execute(
            "INSERT INTO stories (user_id,content) VALUES (?,?)",
            (session["user_id"], content),
        )

        con.commit()

    cur.execute(
        "SELECT content FROM stories WHERE user_id=?",
        (session["user_id"],),
    )

    stories = cur.fetchall()

    return render_template("story.html", stories=stories)


@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)