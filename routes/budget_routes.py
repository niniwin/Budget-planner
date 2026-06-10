from flask import Blueprint, Response, request, jsonify, render_template
from models import db
from models.transaction import Transaction
from models.category import Category
from datetime import datetime,date
from sqlalchemy import extract, func
import csv
from io import StringIO

budget_bp=Blueprint('budget',__name__)


@budget_bp.route('/backup/transactions.csv')
def backup_transactions():
    transactions = Transaction.query.order_by(Transaction.date.asc()).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'type', 'date', 'description', 'amount'])

    for t in transactions:
        writer.writerow([
            t.id,
            t.type,
            t.date.strftime('%Y-%m-%d') if t.date else '',
            t.description or '',
            t.amount
        ])

    filename = f"transactions-backup-{date.today().strftime('%Y-%m-%d')}.csv"

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
@budget_bp.route('/add-transaction',methods=['POST'])
def add_transaction():
    print(request.form)
    types=request.form.getlist('type[]')
    dates=request.form.getlist('date[]')
    descriptions=request.form.getlist('description[]')
    amounts=request.form.getlist('amount[]')

   

    #save income
    for i in range(len(dates)):
        if dates[i]:
            db.session.add(Transaction(
                type=types[i],
                date=dates[i],
                description=descriptions[i],
                amount=amounts[i]

            ))
               
    db.session.commit()

    return jsonify({"message":"Transaction added!"})

@budget_bp.route('/transactions',methods=['GET'])
def get_transactions():
   
    month_str = request.args.get('month')   # format: 2026-04
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = max(int(request.args.get('page', 1)),1)
    per_page = 25

    query = Transaction.query

    # Filter by month
    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        query = query.filter(Transaction.date.between(start, end))

    elif month_str:
        try:
           
            year, month_num = map(int, month_str.split('-'))
            start_date = datetime(year, month_num, 1)

            if month_num == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month_num + 1, 1)

            query = query.filter(
                Transaction.date >= start_date,
                Transaction.date < end_date
            )
        except ValueError:
            return jsonify({"error": "Invalid month format. Use YYYY-MM"}), 400
    # Pagination
    pagination = query.order_by(Transaction.date.asc())\
                      .paginate(page=page, per_page=per_page, error_out=False)

    result = []
    for t in pagination.items:
        result.append({
            "id": t.id,
            "amount": t.amount,
            "date": t.date.isoformat(),
            "description": t.description,
            "type": t.type
        })

    return jsonify({
        "data": result,
        "total_pages": pagination.pages,
        "current_page": page
    })
@budget_bp.route("/")
@budget_bp.route("/planner")
def planner():
    selected_month = request.args.get("month")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = max(int(request.args.get("page", 1)), 1)
    per_page = 25

    if not selected_month:
        selected_month = date.today().strftime("%Y-%m")

    query = Transaction.query

    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        query = query.filter(Transaction.date.between(start, end))

    elif selected_month:
        year, month_num = selected_month.split("-")
        query = query.filter(
            func.extract("year", Transaction.date) == int(year),
            func.extract("month", Transaction.date) == int(month_num)
        )

    pagination = query.order_by(Transaction.date.asc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    transactions = pagination.items

    summary_transactions = query.all()
    total_income = sum(t.amount for t in summary_transactions if t.type == "income")
    total_expense = sum(t.amount for t in summary_transactions if t.type == "expense")
    balance = total_income - total_expense

    daily_summary = {}

    for t in summary_transactions:
        day = t.date.strftime("%Y-%m-%d")

        if day not in daily_summary:
            daily_summary[day] = {
                "income": 0,
                "expense": 0
            }

        if t.type == "income":
            daily_summary[day]["income"] += t.amount
        else:
            daily_summary[day]["expense"] += t.amount

    month_display = datetime.strptime(selected_month, "%Y-%m").strftime("%B")

    return render_template(
        "budget.html",
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        daily_summary=daily_summary,
        month=selected_month,
        month_display=month_display,
        pagination=pagination
    )

@budget_bp.route('/update/<int:id>', methods=['PUT'])
def update_transaction(id):
    data = request.get_json()

    t = Transaction.query.get(id)
    if not t:
        return jsonify({"error":"Transaction not found"}),404
    t.date = data['date']
    t.description = data['description']
    t.amount = data['amount']

    db.session.commit()

    return jsonify({"message": "Updated"})

@budget_bp.route('/delete/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)

    db.session.delete(transaction)
    db.session.commit()

    return jsonify({"success": True}), 200

def get_monthly_report(month=None, start_date=None, end_date=None):
    query = Transaction.query

    if month:
        query = query.filter(func.strftime("%Y-%m", Transaction.date) == month)

    if start_date:
        query = query.filter(Transaction.date >= start_date)

    if end_date:
        query = query.filter(Transaction.date <= end_date)

    transactions = query.order_by(Transaction.date.asc()).all()

    report = {}

    for t in transactions:
        day = t.date.strftime("%Y-%m-%d")

        if day not in report:
            report[day] = {
                "date": day,
                "income": 0,
                "expense": 0,
                "balance": 0
            }

        if t.type == "income":
            report[day]["income"] += t.amount
        elif t.type == "expense":
            report[day]["expense"] += t.amount

        report[day]["balance"] = (
            report[day]["income"] - report[day]["expense"]
        )

    return list(report.values())

@budget_bp.route("/budget/monthly-report")
def monthly_report():
    month = request.args.get("month")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not month:
        month=date.today().strftime("%Y-%m")

    report_data = get_monthly_report(
        month=month,
        start_date=start_date,
        end_date=end_date
    )

    total_income = sum(row["income"] for row in report_data)
    total_expense = sum(row["expense"] for row in report_data)
    balance = total_income - total_expense

    return render_template(
        "budget/monthly_report.html",
        report_data=report_data,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        month=month
    )

@budget_bp.route("/budget/daily-summary")
def daily_summary():
    selected_month = request.args.get("month")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = max(int(request.args.get("page", 1)), 1)
    per_page = 25

    if not selected_month:
        selected_month = date.today().strftime("%Y-%m")

    query = Transaction.query

    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        query = query.filter(Transaction.date.between(start, end))
        period_display = f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"
    else:
        year, month_num = selected_month.split("-")
        query = query.filter(
            func.extract("year", Transaction.date) == int(year),
            func.extract("month", Transaction.date) == int(month_num)
        )
        period_display = datetime.strptime(selected_month, "%Y-%m").strftime("%B")

    transactions = query.order_by(Transaction.date.asc()).all()

    daily_summary = {}

    for t in transactions:
        day = t.date.strftime("%Y-%m-%d")

        if day not in daily_summary:
            daily_summary[day] = {"income": 0, "expense": 0, "balance": 0}

        if t.type == "income":
            daily_summary[day]["income"] += t.amount
        else:
            daily_summary[day]["expense"] += t.amount

        daily_summary[day]["balance"] = daily_summary[day]["income"] - daily_summary[day]["expense"]

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
        period_display=period_display
    )




