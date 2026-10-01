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
OAUTH_PROVIDER_NAME=Google
OAUTH_CLIENT_ID=your-oauth-client-id
OAUTH_CLIENT_SECRET=your-oauth-client-secret
OAUTH_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration
OAUTH_SCOPE=openid email profile
ADMIN_EMAILS=admin@example.com
```

4. Run the app locally.

```powershell
python app.py
```

## Auth and Admin

The app supports password login, OAuth login, and `user` / `admin` roles. The first registered account becomes an admin automatically. Any email in `ADMIN_EMAILS` also receives admin access when it registers or signs in with OAuth.

Admin password - july@123

For Google OAuth, add this callback URL in the Google OAuth client:

```text
http://localhost:5000/auth/callback
```

If you already have an existing database, run `migrations/001_add_auth.sql` once. `db.create_all()` creates tables for a fresh database, but it does not add new columns to existing tables.

## Production

Run with Waitress:

```powershell
python serve.py
```

The production environment should provide `SECRET_KEY` and `DATABASE_URL` as environment variables. Do not commit your real `.env` file.
