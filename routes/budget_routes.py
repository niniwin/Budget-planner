from datetime import date, datetime
from io import StringIO
import csv

from flask import Blueprint, Response, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import case, func

from models import db
from models.note import Note
from models.transaction import Transaction


budget_bp = Blueprint("budget", __name__)


def filter_month(query, selected_month):
    year, month = map(int, selected_month.split("-"))
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return query.filter(Transaction.date >= start, Transaction.date < end)


def amount_totals():
    return (
        func.coalesce(func.sum(case((Transaction.type == "income", Transaction.amount), else_=0)), 0).label("income"),
        func.coalesce(func.sum(case((Transaction.type == "expense", Transaction.amount), else_=0)), 0).label("expense"),
    )


def visible_transactions_query():
    query = Transaction.query
    if current_user.is_admin:
        return query
    return query.filter(Transaction.user_id == current_user.id)


def visible_notes_query():
    query = Note.query
    if current_user.is_admin:
        return query
    return query.filter(Note.user_id == current_user.id)


@budget_bp.route("/backup/transactions.csv")
@login_required
def backup_transactions():
    transactions = visible_transactions_query().order_by(Transaction.date.asc()).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "type", "date", "description", "amount"])

    for transaction in transactions:
        writer.writerow([
            transaction.id,
            transaction.type,
            transaction.date.strftime("%Y-%m-%d") if transaction.date else "",
            transaction.description or "",
            transaction.amount,
        ])

    filename = f"transactions-backup-{date.today().strftime('%Y-%m-%d')}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@budget_bp.route("/add-transaction", methods=["POST"])
@login_required
def add_transaction():
    types = request.form.getlist("type[]")
    dates = request.form.getlist("date[]")
    descriptions = request.form.getlist("description[]")
    amounts = request.form.getlist("amount[]")

    for index in range(len(dates)):
        if dates[index]:
            db.session.add(Transaction(
                type=types[index],
                date=dates[index],
                description=descriptions[index],
                amount=amounts[index],
                user_id=current_user.id,
            ))

    db.session.commit()

    return jsonify({"message": "Transaction added!"})


@budget_bp.route("/transactions", methods=["GET"])
@login_required
def get_transactions():
    month_str = request.args.get("month")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = max(int(request.args.get("page", 1)), 1)
    per_page = 30

    query = visible_transactions_query()

    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        query = query.filter(Transaction.date.between(start, end))
    elif month_str:
        try:
            year, month_num = map(int, month_str.split("-"))
            start = datetime(year, month_num, 1)

            if month_num == 12:
                end = datetime(year + 1, 1, 1)
            else:
                end = datetime(year, month_num + 1, 1)

            query = query.filter(Transaction.date >= start, Transaction.date < end)
        except ValueError:
            return jsonify({"error": "Invalid month format. Use YYYY-MM"}), 400

    pagination = query.order_by(Transaction.date.asc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    result = []
    for transaction in pagination.items:
        result.append({
            "id": transaction.id,
            "amount": transaction.amount,
            "date": transaction.date.isoformat(),
            "description": transaction.description,
            "type": transaction.type,
        })

    return jsonify({
        "data": result,
        "total_pages": pagination.pages,
        "current_page": page,
    })


@budget_bp.route("/")
@budget_bp.route("/planner")
@login_required
def planner():
    selected_month = request.args.get("month")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = max(int(request.args.get("page", 1)), 1)
    per_page = 30

    if not selected_month:
        selected_month = date.today().strftime("%Y-%m")

    query = visible_transactions_query()

    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        query = query.filter(Transaction.date.between(start, end))
    elif selected_month:
        query = filter_month(query, selected_month)

    pagination = query.order_by(Transaction.date.asc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )
    transactions = pagination.items

    totals = query.with_entities(*amount_totals()).one()
    total_income = totals.income
    total_expense = totals.expense
    balance = total_income - total_expense
    month_display = datetime.strptime(selected_month, "%Y-%m").strftime("%B")

    return render_template(
        "budget.html",
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        month=selected_month,
        month_display=month_display,
        pagination=pagination,
    )


@budget_bp.route("/update/<int:id>", methods=["PUT"])
@login_required
def update_transaction(id):
    data = request.get_json()

    transaction = visible_transactions_query().filter(Transaction.id == id).first()
    if not transaction:
        return jsonify({"error": "Transaction not found"}), 404

    transaction.date = data["date"]
    transaction.description = data["description"]
    transaction.amount = data["amount"]

    db.session.commit()

    return jsonify({"message": "Updated"})


@budget_bp.route("/delete/<int:id>", methods=["DELETE"])
@login_required
def delete_transaction(id):
    transaction = visible_transactions_query().filter(Transaction.id == id).first_or_404()

    db.session.delete(transaction)
    db.session.commit()

    return jsonify({"success": True}), 200


@budget_bp.route("/budget/daily-summary")
@login_required
def daily_summary():
    selected_month = request.args.get("month")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not selected_month:
        selected_month = date.today().strftime("%Y-%m")

    query = visible_transactions_query()

    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        query = query.filter(Transaction.date.between(start, end))
        period_display = f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"
    else:
        query = filter_month(query, selected_month)
        period_display = datetime.strptime(selected_month, "%Y-%m").strftime("%B")

    rows = (
        query.with_entities(Transaction.date, *amount_totals())
        .group_by(Transaction.date)
        .order_by(Transaction.date.asc())
        .all()
    )
    daily_summary = {
        row.date.strftime("%Y-%m-%d"): {
            "income": row.income,
            "expense": row.expense,
            "balance": row.income - row.expense,
        }
        for row in rows
    }

    total_income = sum(day["income"] for day in daily_summary.values())
    total_expense = sum(day["expense"] for day in daily_summary.values())
    balance = total_income - total_expense

    return render_template(
        "budget/daily_summary.html",
        daily_summary=daily_summary,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        month=selected_month,
        period_display=period_display,
    )


@budget_bp.route("/show-note")
@login_required
def show_note():
    notes = visible_notes_query().order_by(Note.id.desc()).all()
    return render_template("budget/note.html", notes=notes)


@budget_bp.route("/add-note", methods=["POST"])
@login_required
def add_note():
    note_text = request.form["note"]
    db.session.add(Note(content=note_text, user_id=current_user.id))
    db.session.commit()
    return redirect(url_for("budget.show_note"))


@budget_bp.route("/edit-note/<int:id>", methods=["POST"])
@login_required
def edit_note(id):
    note = visible_notes_query().filter(Note.id == id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404
    note.content = request.form["note"]
    db.session.commit()
    return redirect(url_for("budget.show_note"))


@budget_bp.route("/delete-note/<int:id>", methods=["POST"])
@login_required
def delete_note(id):
    note = visible_notes_query().filter(Note.id == id).first_or_404()
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("budget.show_note"))
