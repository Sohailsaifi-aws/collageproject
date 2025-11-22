from datetime import datetime, date

@app.route("/returns", methods=["GET","POST"])
def returns():
    if not session.get("admin"):
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    # -------- Return Book POST --------
    if request.method == "POST":
        issue_id = request.form["issue_id"]

        # Get issued book record
        cur.execute("SELECT * FROM issued_books WHERE id=%s", (issue_id,))
        issue = cur.fetchone()

        if not issue or issue["return_date"] is not None:
            flash("Invalid Operation", "danger")
            return redirect(url_for("returns"))

        # Dates
        issued_on = issue["issue_date"]
        today = date.today()

        days_used = (today - issued_on).days

        # Fine Rule: 7 days free, after that Rs 5/day
        free_days = 7
        rate = 5

        if days_used > free_days:
            fine = (days_used - free_days) * rate
        else:
            fine = 0

        # Update return info
        cur.execute(
            "UPDATE issued_books SET return_date=%s, fine=%s WHERE id=%s",
            (today, fine, issue_id)
        )

        # Quantity increase
        cur.execute(
            "UPDATE books SET quantity = quantity + 1 WHERE id=%s",
            (issue["book_id"],)
        )

        db.commit()

        flash(f"Book Returned Successfully | Fine: Rs {fine}", "success")
        return redirect(url_for("returns"))

    # -------- Show all non-returned books --------
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
