
import io
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import date

from flask import Flask, render_template, request, flash, redirect, url_for, make_response

app = Flask(__name__)
app.secret_key = "cloud-cost-project-key"
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_costs.db")


@contextmanager
def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with get_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS cost_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                compute REAL NOT NULL,
                storage REAL NOT NULL,
                network REAL NOT NULL,
                monthly REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                monthly_budget REAL
            )
        """)
        connection.execute("INSERT OR IGNORE INTO settings (id, monthly_budget) VALUES (1, NULL)")


def get_budget():
    with get_db() as connection:
        row = connection.execute("SELECT monthly_budget FROM settings WHERE id = 1").fetchone()
    return row["monthly_budget"] if row else None


init_db()


@app.route("/", methods=["GET", "POST"])
def dashboard():
    compute, storage, network = 4000.0, 1000.0, 500.0
    monthly = compute + storage + network
    yearly = monthly * 12
    status = "Cost Under Control"
    current_month = date.today().strftime("%Y-%m")
    estimate_month = request.form.get("month", current_month)

    if request.method == "POST":
        try:
            compute = float(request.form.get("compute", 0))
            storage = float(request.form.get("storage", 0))
            network = float(request.form.get("network", 0))
            if any(value < 0 or value > 1000000000 for value in (compute, storage, network)):
                raise ValueError
            if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", estimate_month):
                raise ValueError

            monthly = compute + storage + network
            yearly = monthly * 12
            with get_db() as connection:
                connection.execute(
                    """INSERT INTO cost_history (month, compute, storage, network, monthly)
                       VALUES (?, ?, ?, ?, ?)""",
                    (estimate_month, compute, storage, network, monthly),
                )
        except (ValueError, TypeError):
            flash("Enter valid non-negative costs and select a valid month.")
            compute, storage, network = 4000.0, 1000.0, 500.0
            monthly = compute + storage + network
            yearly = monthly * 12

    budget = get_budget()
    over_budget = budget is not None and monthly > budget
    if over_budget:
        status = "Over Monthly Budget"
    elif monthly > 10000:
        status = "High Cost Alert"

    with get_db() as connection:
        history = connection.execute(
            "SELECT * FROM cost_history ORDER BY created_at DESC, id DESC LIMIT 20"
        ).fetchall()
        months = [row["month"] for row in connection.execute(
            "SELECT DISTINCT month FROM cost_history ORDER BY month DESC"
        ).fetchall()]
        first_month, second_month = request.args.get("month_a", ""), request.args.get("month_b", "")
        comparison = None
        if first_month and second_month:
            comparison = [connection.execute(
                "SELECT * FROM cost_history WHERE month = ? ORDER BY created_at DESC, id DESC LIMIT 1",
                (selected_month,),
            ).fetchone() for selected_month in (first_month, second_month)]

    return render_template(
        "dashboard.html", compute=compute, storage=storage, network=network,
        monthly=monthly, yearly=yearly, status=status, budget=budget,
        over_budget=over_budget, estimate_month=estimate_month, history=history,
        months=months, first_month=first_month, second_month=second_month,
        comparison=comparison,
    )


@app.route("/budget", methods=["POST"])
def set_budget():
    raw_budget = request.form.get("budget", "").strip()
    try:
        budget = float(raw_budget) if raw_budget else None
        if budget is not None and (budget < 0 or budget > 1000000000):
            raise ValueError
        with get_db() as connection:
            connection.execute("UPDATE settings SET monthly_budget = ? WHERE id = 1", (budget,))
    except (ValueError, TypeError):
        flash("Enter a valid budget between ₹0 and ₹1,000,000,000.")
    return redirect(url_for("dashboard"))


@app.route("/report/<int:record_id>.pdf")
def download_report(record_id):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    with get_db() as connection:
        record = connection.execute(
            "SELECT * FROM cost_history WHERE id = ?", (record_id,)
        ).fetchone()
    if record is None:
        return "Cost report not found", 404

    output = io.BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm)
    styles = getSampleStyleSheet()
    rows = [
        ["Cost category", "Estimated monthly cost"],
        ["Compute", f"₹{record['compute']:,.2f}"],
        ["Storage", f"₹{record['storage']:,.2f}"],
        ["Network", f"₹{record['network']:,.2f}"],
        ["Total", f"₹{record['monthly']:,.2f}"],
    ]
    table = Table(rows, colWidths=[90 * mm, 75 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123c69")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f0f8")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 9),
    ]))
    document.build([
        Paragraph("Cloud Cost Summary", styles["Title"]), Spacer(1, 8 * mm),
        Paragraph(f"Estimate month: {record['month']}", styles["Normal"]),
        Paragraph(f"Saved: {record['created_at']}", styles["Normal"]),
        Spacer(1, 6 * mm), table,
    ])
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=cloud-cost-{record['month']}.pdf"
    return response


if __name__ == "__main__":
    app.run(debug=True)
