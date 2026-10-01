from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import case, func

from models import db
from models.transaction import Transaction


report_bp = Blueprint("report", __name__)


def visible_transactions_query():
    query = db.session.query(Transaction)
    if current_user.is_admin:
        return query
    return query.filter(Transaction.user_id == current_user.id)


@report_bp.route("/report/monthly_report")
@login_required
def monthly_report():
    # Other pages do not need to import the charting library at startup.
    import plotly.graph_objects as go

    month = func.date_trunc("month", Transaction.date).label("month")
    results = (
        visible_transactions_query()
        .with_entities(
            month,
            func.sum(
                case(
                    (Transaction.type == "income", Transaction.amount),
                    else_=0,
                )
            ).label("income"),
            func.sum(
                case(
                    (Transaction.type == "expense", Transaction.amount),
                    else_=0,
                )
            ).label("expense"),
        )
        .group_by(month)
        .order_by(month)
        .all()
    )

    months = []
    incomes = []
    expenses = []

    total_income = 0
    total_expense = 0

    for row in results:
        months.append(row.month.strftime("%b %Y"))
        incomes.append(float(row.income or 0))
        expenses.append(float(row.expense or 0))

        total_income += float(row.income or 0)
        total_expense += float(row.expense or 0)

    balance = total_income - total_expense

    fig = go.Figure()

    fig.add_bar(
        x=months,
        y=incomes,
        name="Income",
        marker_color="#2ecc71",
        text=incomes,
        texttemplate="%{text:.2f}",
        textposition="outside",
    )

    fig.add_bar(
        x=months,
        y=expenses,
        name="Expense",
        marker_color="#e74c3c",
        text=expenses,
        texttemplate="%{text:.2f}",
        textposition="outside",
    )
    max_value = max(incomes + expenses) if incomes or expenses else 0

    fig.update_layout(
        title={
            "text": "Monthly Income vs Expense Report",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 24},
        },
        xaxis_title="Month",
        yaxis_title="Amount",
        template="plotly_white",
        barmode="group",
        bargap=0.25,
        hovermode="x unified",
        height=550,
        autosize=True,
        legend=dict(itemclick=False, itemdoubleclick=False),
        uirevision="monthly_report",
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(
        showgrid=True,
        gridcolor="lightgray",
        range=[0, max_value * 1.15],
        autorange=False,
    )

    chart = fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True})

    report_data = [
        {
            "date": months[index],
            "income": incomes[index],
            "expense": expenses[index],
            "balance": incomes[index] - expenses[index],
        }
        for index in range(len(months))
    ]

    return render_template(
        "report/monthly_report.html",
        report_data=report_data,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        chart=chart,
    )
