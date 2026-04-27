from models import db

class DailySummary(db.Model):
    __tablename__ = 'daily_summary'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    total_income = db.Column(db.Float, default=0)
    total_expense = db.Column(db.Float, default=0)


class MonthlyReport(db.Model):
    __tablename__ = 'monthly_report'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    month = db.Column(db.Integer)
    total_income = db.Column(db.Float, default=0)
    total_expense = db.Column(db.Float, default=0)