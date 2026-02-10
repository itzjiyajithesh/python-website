from flask import Flask, render_template_string, request, redirect, session, url_for
import sqlite3
import hashlib
import os

app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static"
)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# ---------- NO CACHE ----------
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ---------- DATABASE ----------
def get_db():
    return sqlite3.connect("users.db")

def init_db():
    con = get_db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    con.commit()
    con.close()

init_db()

# ---------- BASE TEMPLATE ----------
def base_start():
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Jiya’s Reading Diary</title>
    <link rel="stylesheet" href="{url_for('static', filename='style.css')}">
</head>
<body>
"""

BASE_END = """
</body>
</html>
"""

# ---------- HOME ----------
@app.route("/")
def home():
    user = session.get("user")

    if not user:
        return render_template_string(
            base_start() + """
            <div style="max-width:900px;margin:90px auto;text-align:center;" class="glow-box">
                <img src="{{ url_for('static', filename='J.png') }}" width="300"><br><br>

                <h2>Welcome to Jiya’s Reading Diary</h2>

                <p>
                    This is a personal reading space where stories live, genres unfold,
                    and readers discover worlds through books.
                    <br><br>
                    Founded by Jiya, this app is built for thoughtful readers who love
                    reflection, imagination, and storytelling.
                </p>

                <br><br>

                <button class="glow-btn" onclick="location.href='/signup'">
                    Let’s Get Started!
                </button>
            </div>
            """ + BASE_END
        )

    return render_template_string(
        base_start() + """
        <div class="layout">
            <div class="sidebar">
                <a href="/profile">👤 Profile</a>
                <a href="/genres">📚 Genres</a>
                <a href="/story">✍ Make Your Own Story</a>
                <a href="/settings">⚙ Settings</a>
                <a href="/logout">🚪 Logout</a>
            </div>

            <div class="content">
                <div class="glow-box" style="max-width:850px;text-align:center;">
                    <img src="{{ url_for('static', filename='J.png') }}" width="300"><br><br>

                    <h2>Account successfully created!</h2>
                    <h3>Welcome {{ user }}!</h3>

                    <br><br>

                    <button class="genre-btn" onclick="location.href='/genre/Fantasy'">Fantasy</button>
                    <button class="genre-btn" onclick="location.href='/genre/Romance'">Romance</button>
                    <button class="genre-btn" onclick="location.href='/genre/Mystery'">Mystery</button>
                    <button class="genre-btn" onclick="location.href='/genre/Sci-Fi'">Sci-Fi</button>
                </div>
            </div>
        </div>
        """ + BASE_END,
        user=user
    )

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()

        con = get_db()
        con.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )
        con.commit()
        con.close()

        session["user"] = name
        return redirect("/")

    return render_template_string(
        base_start() + """
        <div style="max-width:520px;margin:90px auto;" class="glow-box">
            <h2>Create an Account</h2>

            <form method="post">
                <input name="name" placeholder="Name" required>
                <input name="email" type="email" placeholder="Email" required>
                <input name="password" type="password" placeholder="Password" required>

                <br>

                <button class="glow-btn">Submit</button>
            </form>

            <p style="margin-top:18px;">
                If you already have an account, <a href="/">Sign In</a>
            </p>
        </div>
        """ + BASE_END
    )

# ---------- OTHER ROUTES ----------
@app.route("/genre/<genre>")
def genre_page(genre):
    return render_template_string(
        base_start() + f"""
        <div style="max-width:900px;margin:90px auto;" class="glow-box">
            <h1>{genre}</h1>
            <p>Curated book reviews appear here.</p>
        </div>
        """ + BASE_END
    )

@app.route("/story")
def story():
    return render_template_string(
        base_start() + """
        <div style="max-width:900px;margin:90px auto;" class="glow-box">
            <h1>Make Your Own Story</h1>
            <textarea rows="14" placeholder="Begin your story here..."></textarea>
        </div>
        """ + BASE_END
    )

@app.route("/profile")
def profile():
    return render_template_string(
        base_start() + """
        <div style="max-width:600px;margin:90px auto;" class="glow-box">
            <h2>Profile Page</h2>
        </div>
        """ + BASE_END
    )

@app.route("/settings")
def settings():
    return render_template_string(
        base_start() + """
        <div style="max-width:600px;margin:90px auto;" class="glow-box">
            <h2>Settings</h2>
        </div>
        """ + BASE_END
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
