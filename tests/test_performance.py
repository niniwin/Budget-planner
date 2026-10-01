import os
import unittest
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from flask import template_rendered


class PerformanceRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Never connect to the configured production database during tests.
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite://", "AUTO_CREATE_TABLES": "false"}):
            from app import app
        from models import db
        cls.app = app
        cls.db = db
        app.config.update(TESTING=True, SECRET_KEY="test-only")

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            cls.db.engine.dispose()

    def setUp(self):
        from models.transaction import Transaction
        from models.user import User
        self.context = self.app.app_context()
        self.context.push()
        self.db.create_all()
        self.db.session.add_all([
            User(id=1, username="one", role="user"),
            User(id=2, username="two", role="user"),
            User(id=3, username="admin", role="admin"),
        ])
        self.db.session.add_all([
            Transaction(user_id=1, date=date(2024, 2, 29), type="income", amount=Decimal("1.25"))
            for _ in range(35)
        ] + [
            Transaction(user_id=1, date=date(2024, 2, 1), type="expense", amount=Decimal("2.10")),
            Transaction(user_id=2, date=date(2024, 2, 29), type="income", amount=Decimal("100")),
            Transaction(user_id=1, date=date(2024, 3, 1), type="income", amount=Decimal("999")),
            Transaction(user_id=1, date=date(2024, 12, 31), type="income", amount=Decimal("5")),
            Transaction(user_id=1, date=date(2025, 1, 1), type="income", amount=Decimal("7")),
        ])
        self.db.session.commit()
        self.client = self.app.test_client()
        self.login(1)

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.context.pop()

    def login(self, user_id):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(user_id)
            session["_fresh"] = True

    def page_context(self, url):
        captured = {}
        def record(sender, template, context, **extra):
            captured.update(context)
        with template_rendered.connected_to(record, self.app):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return captured

    def test_planner_totals_cover_all_pages_and_keep_user_scope(self):
        context = self.page_context('/planner?month=2024-02')
        self.assertEqual(len(context['transactions']), 30)
        self.assertEqual(context['pagination'].total, 36)
        self.assertEqual(context['total_income'], Decimal('43.75'))
        self.assertEqual(context['total_expense'], Decimal('2.10'))
        self.assertEqual(context['balance'], Decimal('41.65'))

    def test_admin_totals_include_other_users(self):
        self.login(3)
        context = self.page_context('/planner?month=2024-02')
        self.assertEqual(context['total_income'], Decimal('143.75'))

    def test_daily_summary_groups_dates_and_keeps_decimals(self):
        context = self.page_context('/budget/daily-summary?month=2024-02')
        self.assertEqual(list(context['daily_summary']), ['2024-02-01', '2024-02-29'])
        self.assertEqual(context['daily_summary']['2024-02-29']['income'], Decimal('43.75'))
        self.assertEqual(context['balance'], Decimal('41.65'))

    def test_date_range_includes_both_endpoints(self):
        for path in ('/planner', '/budget/daily-summary'):
            context = self.page_context(path + '?start_date=2024-02-29&end_date=2024-03-01')
            self.assertEqual(context['total_income'], Decimal('1042.75'))

    def test_december_boundary_and_empty_month(self):
        for path in ('/planner', '/budget/daily-summary'):
            context = self.page_context(path + '?month=2024-12')
            self.assertEqual(context['total_income'], Decimal('5'))
            context = self.page_context(path + '?month=2024-11')
            self.assertEqual(context['balance'], 0)

    def test_assets_cached_and_login_does_not_load_unused_libraries(self):
        response = self.client.get('/static/js/budget.js')
        self.assertEqual(response.cache_control.max_age, 3600)
        response.close()
        self.client.get('/logout')
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'bootstrap.min.js', response.data)
        self.assertNotIn(b'popper.min.js', response.data)

    def test_monthly_report_renders_with_external_chart_library(self):
        # date_trunc is PostgreSQL-specific: supply its result for this render test.
        with patch('routes.report_routes.visible_transactions_query') as query:
            query.return_value.with_entities.return_value.group_by.return_value.order_by.return_value.all.return_value = [
                SimpleNamespace(month=date(2024, 2, 1), income=Decimal('43.75'), expense=Decimal('2.10'))
            ]
            context = self.page_context('/report/monthly_report')
        self.assertEqual(context['balance'], 41.65)
        self.assertIn('https://cdn.plot.ly/', context['chart'])
        self.assertLess(len(context['chart'].encode()), 20000)


if __name__ == '__main__':
    unittest.main()
