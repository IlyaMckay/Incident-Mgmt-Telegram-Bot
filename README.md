# Incident Management Telegram Bot

This microservices-based Incident Management Telegram Bot facilitates incident reporting via Telegram and incident management via admin web page.

[Backend](tg_backend/main.py) is built on `Python` utilizing following technologies:
- `http.server` as HTTP server classes.
- Custom HTTP requests handler that implements `RESTful` API endpoints for managing users, incidents, and comments.
- [SQL_Connector](tg_backend/sql_connector.py):
  - `psycopg2` as a PostgreSQL database adapter.


[Telegram bot](tg_bot_api/bot.py) is built on `Python` utilizing following technologies:
- `Python Telegram Bot` as a wrapper.
- `Requests` as requests HTTP Library.

Click on [Telegram Bot](https://t.me/@tele4crm_bot) to open in telegram.


[Admin Page](tg_bot_admin/main.py) is built on `Python` utilizing following technologies:
- `Flask`framework for the backend.
- `Jinja2` as a template engine for rendering frontend views.
- `Requests` as requests HTTP Library.

Click on [Admin Page](https://admin_bot.cfapps.us10-001.hana.ondemand.com) to open.
