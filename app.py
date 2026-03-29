from flask import Flask, render_template_string, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"
DB = "restaurant.db"


# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tables(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_no INTEGER,
        seats INTEGER,
        price INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        table_no INTEGER,
        date TEXT,
        time TEXT,
        amount INTEGER
    )
    """)

    conn.commit()
    conn.close()


# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = u
            return redirect("/dashboard")

    return render_template_string("""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<body class="bg-dark text-light">
<div class="container mt-5" style="max-width:400px">
<div class="card bg-secondary p-4">
<h3>Restaurant Login</h3>
<form method="post">
<input class="form-control mb-3" name="username" placeholder="Username">
<input class="form-control mb-3" name="password" type="password" placeholder="Password">
<button class="btn btn-warning w-100">Login</button>
</form>
<a href='/register' class="btn btn-outline-light mt-3">Register</a>
</div>
</div>
""")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("INSERT INTO users(username,password) VALUES (?,?)", (u, p))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template_string("""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<body class="bg-dark text-light">
<div class="container mt-5" style="max-width:400px">
<div class="card bg-secondary p-4">
<h3>Register</h3>
<form method="post">
<input class="form-control mb-3" name="username">
<input class="form-control mb-3" name="password" type="password">
<button class="btn btn-success w-100">Register</button>
</form>
</div>
</div>
""")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return render_template_string("""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<body class='bg-dark text-light'>
<div class='container mt-5'>
<h2>Welcome {{user}}</h2>
<br>
<a class='btn btn-primary' href='/tables'>Tables</a>
<a class='btn btn-success' href='/book'>Book</a>
<a class='btn btn-warning' href='/my'>My Bookings</a>
<a class='btn btn-danger' href='/logout'>Logout</a>
</div>
""", user=session["user"])


# ---------------- TABLES ----------------

@app.route("/tables")
def tables():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT table_no,seats,price FROM tables")
    data = cur.fetchall()
    conn.close()

    html = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<body class='bg-dark text-light'>
<div class='container mt-5'>
<h2>Tables</h2>
<table class='table table-dark'>
<tr><th>Table</th><th>Seats</th><th>Price</th></tr>
"""

    for t in data:
        html += f"<tr><td>{t[0]}</td><td>{t[1]}</td><td>₹{t[2]}</td></tr>"

    html += "</table><a href='/dashboard' class='btn btn-light'>Back</a>"
    return html


# ---------------- BOOK ----------------

@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        session["table"] = request.form["table"]
        session["date"] = request.form["date"]
        session["time"] = request.form["time"]
        return redirect("/payment")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT table_no,seats,price FROM tables")
    tables = cur.fetchall()
    conn.close()

    options = ""
    for t in tables:
        options += f"<option value='{t[0]}'>Table {t[0]} ({t[1]} seats) - ₹{t[2]}</option>"

    return render_template_string(f"""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<body class='bg-dark text-light'>
<div class='container mt-5'>
<h2>Book Table</h2>
<form method='post'>
<select class='form-control mb-3' name='table'>
{options}
</select>
<input class='form-control mb-3' type='date' name='date' required>
<input class='form-control mb-3' type='time' name='time' required>
<button class='btn btn-success'>Proceed to Payment</button>
</form>
</div>
""")


# ---------------- PAYMENT ----------------

@app.route("/payment")
def payment():
    table = session.get("table")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT price FROM tables WHERE table_no=?", (table,))
    price = cur.fetchone()[0]
    conn.close()

    return render_template_string(f"""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<body class='bg-dark text-light'>
<div class='container mt-5'>
<div class='card bg-secondary p-4'>
<h3>Payment</h3>
<h4>Amount: ₹{price}</h4>
<p>Demo Payment</p>
<a class='btn btn-success' href='/pay_success'>Pay Now</a>
</div>
</div>
""")


# ---------------- PAYMENT SUCCESS ----------------

@app.route("/pay_success")
def pay_success():
    table = session.get("table")
    date = session.get("date")
    time = session.get("time")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT price FROM tables WHERE table_no=?", (table,))
    price = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO bookings(user,table_no,date,time,amount) VALUES(?,?,?,?,?)",
        (session["user"], table, date, time, price),
    )

    conn.commit()
    conn.close()

    return redirect("/my")


# ---------------- MY BOOKINGS ----------------

@app.route("/my")
def my():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings WHERE user=?", (session["user"],))
    data = cur.fetchall()
    conn.close()

    html = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<body class='bg-dark text-light'>
<div class='container mt-5'>
<h2>My Bookings</h2>
<table class='table table-dark'>
<tr><th>Table</th><th>Date</th><th>Time</th><th>Amount</th><th></th></tr>
"""

    for b in data:
        html += f"<tr><td>{b[2]}</td><td>{b[3]}</td><td>{b[4]}</td><td>₹{b[5]}</td><td><a class='btn btn-danger btn-sm' href='/cancel/{b[0]}'>Cancel</a></td></tr>"

    html += "</table><a href='/dashboard' class='btn btn-light'>Back</a>"
    return html


# ---------------- CANCEL ----------------

@app.route("/cancel/<id>")
def cancel(id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/my")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- SEED TABLES ----------------

def seed_tables():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tables")
    if cur.fetchone()[0] == 0:
        tables = [
            (1,2,100),
            (2,2,100),
            (3,4,200),
            (4,4,200),
            (5,6,300),
            (6,6,300),
            (7,8,400),
            (8,8,400),
            (9,10,500),
            (10,12,600)
        ]

        for t in tables:
            cur.execute("INSERT INTO tables(table_no,seats,price) VALUES(?,?,?)", t)

    conn.commit()
    conn.close()


# ---------------- MAIN ----------------

if __name__ == "__main__":
    init_db()
    seed_tables()
    app.run(debug=True)