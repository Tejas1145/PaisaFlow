import sqlite3
from datetime import date as dt_date
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("expenses.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            monthly_budget REAL NOT NULL
        )
    """)
    conn.execute("INSERT OR IGNORE INTO settings (id, monthly_budget) VALUES (1, 5000)")
    conn.commit()
    conn.close()

init_db()

def detect_category(title):
    t = title.lower()
    if any(word in t for word in ["hotel", "room", "stay", "resort", "lodge", "oyo", "booking"]):
        return "Hotel"
    elif any(word in t for word in ["chai", "coffee", "food", "lunch", "dinner", "pizza", "burger", "snacks", "nashto"]):
        return "Food"
    elif any(word in t for word in ["petrol", "diesel", "bus", "auto", "rickshaw", "train", "uber", "ola", "ticket"]):
        return "Travel"
    elif any(word in t for word in ["bill", "recharge", "electricity", "wifi", "rent", "gas"]):
        return "Bills"
    elif any(word in t for word in ["clothes", "shoes", "amazon", "flipkart", "shopping", "mall"]):
        return "Shopping"
    return "Other"

@app.route("/")
def home():
    conn = get_db()
    expenses = conn.execute("SELECT * FROM expenses ORDER BY date DESC, id DESC").fetchall()
    budget_row = conn.execute("SELECT monthly_budget FROM settings WHERE id = 1").fetchone()
    income = float(budget_row["monthly_budget"]) if budget_row else 5000.0
    total_expense = float(sum(exp["amount"] for exp in expenses))
    total_balance = income - total_expense
    saving = max(0.0, total_balance)

    cat_totals = {}
    unique_dates = set()
    for exp in expenses:
        cat = exp["category"]
        cat_totals[cat] = cat_totals.get(cat, 0) + exp["amount"]
        if exp["date"]:
            unique_dates.add(exp["date"])

    top_category = max(cat_totals, key=cat_totals.get) if cat_totals else "N/A"
    top_amount = float(cat_totals[top_category]) if cat_totals else 0.0
    daily_avg = round(total_expense / len(unique_dates), 2) if unique_dates else 0.0

    conn.close()
    return render_template(
        "index.html",
        expenses=expenses,
        income=income,
        total_expense=total_expense,
        total_balance=total_balance,
        saving=saving,
        cat_labels=list(cat_totals.keys()),
        cat_values=list(cat_totals.values()),
        top_category=top_category,
        top_amount=top_amount,
        daily_avg=daily_avg
    )

@app.route("/add", methods=["POST"])
def add_expense():
    title = request.form["title"]
    amount = float(request.form["amount"])
    category = request.form["category"]
    date = request.form.get("date") or dt_date.today().strftime("%Y-%m-%d")

    if category == "Auto":
        category = detect_category(title)

    conn = get_db()
    conn.execute("INSERT INTO expenses (title, amount, category, date) VALUES (?, ?, ?, ?)",
                 (title, amount, category, date))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_expense(id):
    conn = get_db()
    if request.method == "POST":
        title = request.form["title"]
        amount = float(request.form["amount"])
        category = request.form["category"]
        date = request.form.get("date") or dt_date.today().strftime("%Y-%m-%d")

        conn.execute(
            "UPDATE expenses SET title = ?, amount = ?, category = ?, date = ? WHERE id = ?",
            (title, amount, category, date, id)
        )
        conn.commit()
        conn.close()
        return redirect("/")

    expense = conn.execute("SELECT * FROM expenses WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template("edit.html", expense=expense)

@app.route("/delete/<int:id>")
def delete_expense(id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/set_budget", methods=["POST"])
def set_budget():
    new_budget = float(request.form["budget"])
    conn = get_db()
    conn.execute("UPDATE settings SET monthly_budget = ? WHERE id = 1", (new_budget,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
