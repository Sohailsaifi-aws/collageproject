from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from datetime import datetime
from config import DB_CONFIG, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ------------------------------
#     DATABASE CONNECTION
# ------------------------------
def get_db():
    return mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database']
    )


# ------------------------------
#         LOGIN SYSTEM
# ------------------------------
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form["username"]
        p = request.form["password"]

        if u == "admin" and p == "admin123":
            session['admin'] = True
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))


# ------------------------------
#          DASHBOARD
# ------------------------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM books")
    books = cur.fetchall()

    return render_template("dashboard.html", books=books)


# ------------------------------
#          BOOKS CRUD
# ------------------------------
@app.route("/books")
def books():
    if not session.get("admin"):
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM books")
    books = cur.fetchall()
    return render_template("books.html", books=books)


@app.route("/books/add", methods=["GET","POST"])
def add_book():
    if not session.get("admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        quantity = request.form["quantity"]

        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO books(title, author, isbn, quantity) VALUES (%s,%s,%s,%s)",
                    (title, author, isbn, quantity))
        db.commit()

        flash("Book added successfully", "success")
        return redirect(url_for("books"))

    return render_template("add_book.html")


@app.route("/books/edit/<int:id>", methods=["GET","POST"])
def edit_book(id):
    if not session.get("admin"):
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        quantity = request.form["quantity"]

        cur.execute("UPDATE books SET title=%s, author=%s, isbn=%s, quantity=%s WHERE id=%s",
                    (title, author, isbn, quantity, id))
        db.commit()

        flash("Book updated", "success")
        return redirect(url_for("books"))

    cur.execute("SELECT * FROM books WHERE id=%s", (id,))
    book = cur.fetchone()
    return render_template("edit_book.html", book=book)


@app.route("/books/delete/<int:id>")
def delete_book(id):
    if not session.get("admin"):
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM books WHERE id=%s", (id,))
    db.commit()

    flash("Book deleted successfully", "success")
    return redirect(url_for("books"))


# ------------------------------
#          ISSUE BOOK
# ------------------------------
@app.route("/issue", methods=["GET","POST"])
def issue():
    if not session.get("admin"):
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        roll = request.form["roll_no"]
        student_name = request.form["student_name"]
        contact = request.form["contact"]
        book_id = request.form["book_id"]

        # Check student exists
        cur.execute("SELECT * FROM students WHERE roll_no=%s", (roll,))
        student = cur.fetchone()

        if not student:
            cur.execute("INSERT INTO students(name, roll_no, contact) VALUES (%s,%s,%s)",
                        (student_name, roll, contact))
            db.commit()
            student_id = cur.lastrowid
        else:
            student_id = student["id"]

        # Check book availability
        cur.execute("SELECT * FROM books WHERE id=%s", (book_id,))
        book = cur.fetchone()

        if book["quantity"] > 0:
            cur.execute("INSERT INTO issued_books(student_id, book_id, issue_date) VALUES(%s,%s,%s)",
                        (student_id, book_id, datetime.utcnow().date()))

            cur.execute("UPDATE books SET quantity = quantity - 1 WHERE id=%s", (book_id,))
            db.commit()

            flash("Book issued successfully", "success")
        else:
            flash("Book Not Available", "danger")

        return redirect(url_for("dashboard"))

    # Load available books
    cur.execute("SELECT * FROM books WHERE quantity > 0")
    books = cur.fetchall()

    return render_template("issue_book.html", books=books)


# ------------------------------
#          RETURN BOOK
# ------------------------------
@app.route("/returns", methods=["GET","POST"])
def returns():
    if not session.get("admin"):
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    # -------- Return Book POST --------
    if request.method == "POST":
        issue_id = request.form["issue_id"]

        cur.execute("SELECT * FROM issued_books WHERE id=%s", (issue_id,))
        issue = cur.fetchone()

        if not issue or issue["return_date"] is not None:
            flash("Invalid Operation", "danger")
            return redirect(url_for("returns"))

        today = datetime.utcnow().date()
        issue_days = (today - issue["issue_date"]).days

        fine = 0
        if issue_days > 14:
            fine = (issue_days - 14) * 5

        cur.execute("UPDATE issued_books SET return_date=%s, fine=%s WHERE id=%s",
                    (today, fine, issue_id))

        cur.execute("UPDATE books SET quantity = quantity + 1 WHERE id=%s",
                    (issue["book_id"],))
        db.commit()

        flash(f"Book Returned | Fine: Rs {fine}", "success")
        return redirect(url_for("returns"))

    # -------- Show Issued Books --------
    cur.execute("""
        SELECT 
            issued_books.id,
            issued_books.issue_date,
            books.title AS book_title,
            students.name AS student_name,
            students.roll_no AS student_roll
        FROM issued_books
        JOIN books ON issued_books.book_id = books.id
        JOIN students ON issued_books.student_id = students.id
        WHERE issued_books.return_date IS NULL
    """)

    issues = cur.fetchall()
    return render_template("returns.html", issues=issues)


# ------------------------------
#          APP RUN
# ------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000 , debug=True)
