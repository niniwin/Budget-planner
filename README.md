# Budget Planner

A Flask daily ledger app for recording income and expenses, filtering transactions by date, and viewing budget reports.

## Setup

1. Create and activate a virtual environment.

```powershell
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file from `.env.example` and fill in your real values.

```env
SECRET_KEY=your-generated-secret-key
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

4. Run the app locally.

```powershell
python app.py
```

## Production

Run with Waitress:

```powershell
python serve.py
```

The production environment should provide `SECRET_KEY` and `DATABASE_URL` as environment variables. Do not commit your real `.env` file.
