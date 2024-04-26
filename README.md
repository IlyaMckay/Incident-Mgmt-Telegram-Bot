# Incident Management Telegram Bot

This microservices-based Telegram Bot simplifies incident reporting and management, all deployed within the SAP Business Technology Platform (BTP) environment utilizing Cloud Foundry for deployment. The database is hosted on Neon.

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

## Dependencies
```
psycopg2==2.9.9
python-telegram-bot==21.0.1
requests==2.31.0
flask==3.0.2
```
## Contributors

- Ilya Makeev
- [Micellius](https://github.com/micellius) as a Mentor

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](https://github.com/cult2rologist/TETRIS/blob/main/LICENCE) file for details.
