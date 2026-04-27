from flask import Blueprint,request,jsonify,render_template
from models import db
from models.transaction import Transaction
from models.category import Category
from datetime import datetime
from sqlalchemy import extract

budget_bp=Blueprint('budget',__name__)


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
    page = max(int(request.args.get('page', 1)),1)
    per_page = 10

    query = Transaction.query

    # 📅 Filter by month
    if month_str:
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
    # 📄 Pagination
    pagination = query.order_by(Transaction.date.desc())\
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

@budget_bp.route("/planner")
def planner():
    current_month = datetime.now().strftime("%B")
    return render_template("budget.html", month=current_month)

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