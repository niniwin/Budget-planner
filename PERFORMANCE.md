# Performance on Render Free

The free service still sleeps after 15 minutes without traffic. These changes
reduce application work after it wakes; they cannot remove Render's wake-up wait.

## Changes

- Planner totals are calculated in SQL instead of loading every matching record.
- Daily summaries fetch one aggregate row per day instead of every transaction.
- Month filters use date ranges that can use ordinary database indexes.
- Transaction indexes support both admin date searches and per-user date searches.
- Plotly imports only when the monthly report is opened. Its versioned JavaScript
  loads from Plotly's CDN instead of being embedded in every report response.
  The first chart visit still downloads the library and requires access to that CDN.
- Removed unused Bootstrap/Popper JavaScript; existing interactions use budget.js.
- Local static files have a one-hour browser cache, and external style/font hosts
  get early connection hints. Bump asset URL versions when changing CSS or JS.
- Existing databases can skip automatic table checks on application startup.

## Apply to the existing deployment

1. Deploy the updated code using your normal workflow.
2. Run each statement in `migrations/003_performance_indexes.sql` against PostgreSQL
   separately, outside a transaction. These indexes are not automatically added to
   existing tables by `db.create_all()`. No existing records are modified.
3. Once the database tables exist, set `AUTO_CREATE_TABLES=false` in Render's
   environment settings. The default remains true for fresh installations.
4. If the database is also on Render, use its internal connection URL when both
   services are in the same region. Do not share database credentials in chat.

## Remaining checks requiring the deployed service

- Measure the first request after inactivity separately from immediate refreshes.
- In browser Network tools, compare document waiting time with CSS/font/chart
  download time. External CDN speed depends on the user's network.
- Check the web service and database regions and database connection latency.
- Notes and admin user lists still load all rows; paginate these if they become
  large. CSV backup deliberately exports every visible transaction.
- Password reset sends email synchronously, so that request depends on the mail
  server's speed. Password hashing during login is intentional security work.
- Monthly reports still aggregate all visible history and build a chart per
  request. Measure before adding caching, which must respect user permissions
  and invalidate when transactions change.

## Local regression checks

Run `python -B -m unittest discover -s tests -v` in the project virtual environment.
Tests use an isolated in-memory SQLite database, never the deployed database.
PostgreSQL index execution plans and actual Render timings need live verification.

References:
- https://render.com/docs/free
- https://render.com/docs/postgresql-creating-connecting
