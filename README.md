# Site Monitoring Bot

This project is a site monitoring application that checks the availability of user-specified websites and notifies users via Telegram when a site becomes unavailable. It includes a Telegram bot for user interaction and a web interface for administrators to view monitored sites. The application uses FastAPI for the web server, aiogram for the Telegram bot, SQLAlchemy for database interactions, and PostgreSQL as the database, all containerized with Docker.

## Features

- **Telegram Bot**:
  - Commands: `/start`, `/add <url>`, `/delete <url>`, `/delete_<id>`, `/list`.
  - Inline buttons: "Add site" and "List sites" for adding and viewing monitored sites.
  - Modal confirmation for site deletion to prevent accidental removals.
  - URL validation using the `validators` library.
  - Notifications about site availability changes (e.g., HTTP errors, redirects).
- **Web Interface**:
  - Displays a list of monitored sites with their status and last checked time.
  - Supports site deletion with a modal confirmation dialog.
  - Protected by basic HTTP authentication.
- **Monitoring**:
  - Periodically checks site availability (default interval: 60 seconds, configurable via database).
  - Stores site status, last checked time, and last notified time in the database.
- **Database**:
  - Uses PostgreSQL for persistent storage.
  - Tables: `users`, `sites`, `system_settings`.
- **Deployment**:
  - Containerized with Docker and Docker Compose.
  - Configurable via environment variables (`.env`).

## Project Structure

```
site-monitoring/
├── bot/
│   ├── bot.py              # Main bot logic, initializes aiogram and monitoring
│   ├── handlers.py         # Telegram command and callback handlers
│   ├── keyboard.py         # Inline keyboard definitions
│   ├── monitoring.py       # Site monitoring logic
├── models/
│   ├── models.py           # SQLAlchemy models for database tables
├── web/
│   ├── main.py             # FastAPI web server
│   ├── templates/
│   │   ├── sites.html      # HTML template for web interface
├── config.py               # Configuration loading from .env
├── init_db.py             # Database initialization script
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not tracked in git)
└── README.markdown        # Project documentation
```

## Requirements

- Docker and Docker Compose
- Python 3.11 (if running without Docker)
- PostgreSQL 15 (managed via Docker)
- Telegram account and bot token (from BotFather)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd site-monitoring
   ```

2. **Create a `.env` file**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration:
   ```
   TELEGRAM_TOKEN=your_bot_token
   DATABASE_URL=postgresql+psycopg2://user:password@db:5432/monitor
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=admin
   ```

3. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d --build
   ```

4. **Verify services**:
   - Telegram bot: Interact with the bot via Telegram.
   - Web interface: Open `http://localhost:8000/sites` and log in with `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
   - Database: Check tables with:
     ```bash
     docker exec -it monitoring-db-1 psql -U user -d monitor -c "\dt"
     ```

## Usage

### Telegram Bot
1. **Start the bot**:
   - Send `/start` to register and see available commands.
   - Response: Welcome message with inline buttons ("Add site", "List sites").

2. **Add a site**:
   - Use `/add <url>` (e.g., `/add https://example.com`) or click "Add site" and enter a URL.
   - URLs are validated; invalid URLs are rejected.
   - Response: Confirmation that the site is added or already exists.

3. **List sites**:
   - Use `/list` or click "List sites".
   - Response: List of sites with status, last checked time, and deletion commands (e.g., `/delete_1`).

4. **Delete a site**:
   - Use `/delete <url>` (e.g., `/delete https://example.com`) or `/delete_<id>` (e.g., `/delete_1`).
   - A confirmation prompt with "Yes, Delete" and "Cancel" buttons appears.
   - Response: Confirmation of deletion or cancellation.

5. **Notifications**:
   - Receive Telegram messages when a site's availability changes (e.g., becomes unavailable due to HTTP errors or redirects).

### Web Interface
1. **Access the interface**:
   - Open `http://localhost:8000/sites`.
   - Log in with `ADMIN_USERNAME` and `ADMIN_PASSWORD`.

2. **View sites**:
   - See a table of all monitored sites with URL, status, and last checked time.

3. **Delete a site**:
   - Click "Delete" next to a site.
   - Confirm deletion in a modal dialog.
   - The page reloads with the updated site list.

### Database Management
- **Initialize database**:
  - The `init_db.py` script runs automatically on bot startup to create tables and set default settings (e.g., `check_interval=60`).
- **Restore a database dump**:
  ```bash
  docker cp dump.sql monitoring-db-1:/dump.sql
  docker exec -it monitoring-db-1 psql -U user -d monitor -f /dump.sql
  ```
  - For binary dumps (`.dump`):
    ```bash
    docker cp dump.dump monitoring-db-1:/dump.dump
    docker exec -it monitoring-db-1 pg_restore -U user -d monitor --verbose /dump.dump
    ```
  - Clear existing data if needed:
    ```bash
    docker exec -it monitoring-db-1 psql -U user -d monitor -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    ```

## Development

### Dependencies
Install dependencies locally (if not using Docker):
```bash
pip install -r requirements.txt
```

### Key Files
- **bot/bot.py**: Initializes the Telegram bot and monitoring loop.
- **bot/handlers.py**: Handles Telegram commands and callbacks (`/start`, `/add`, `/delete`, `/list`, inline buttons).
- **bot/monitoring.py**: Checks site availability and sends notifications.
- **web/main.py**: FastAPI server for the web interface.
- **init_db.py**: Sets up the PostgreSQL database with tables and default settings.
- **models/models.py**: SQLAlchemy models for `users`, `sites`, and `system_settings`.

### Adding Features
- **Progress Bar for Notifications**: Implement WebSocket in `web/main.py` to show real-time notification progress.
- **Site Availability Charts**: Add Chart.js to `web/templates/sites.html` for visualizing site uptime.
- **Enhanced Monitoring**: Add support for custom check intervals per site or more detailed status checks (e.g., response time).

## Troubleshooting
- **Bot not responding**:
  - Check logs: `docker-compose logs bot`.
  - Verify `TELEGRAM_TOKEN` in `.env`.
  - Ensure PostgreSQL is running: `docker-compose logs db`.
- **Database errors**:
  - Check tables: `docker exec -it monitoring-db-1 psql -U user -d monitor -c "\dt"`.
  - Verify `system_settings`: `docker exec -it monitoring-db-1 psql -U user -d monitor -c "SELECT * FROM system_settings;"`.
- **Web interface issues**:
  - Check logs: `docker-compose logs web`.
  - Verify `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
- **Restoring dump fails**:
  - Ensure dump format (SQL or binary) and compatibility with PostgreSQL 15.
  - Check for `CREATE DATABASE` in SQL dumps and remove if necessary.

## Contributing
1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`.
3. Commit changes: `git commit -m "Add feature"`.
4. Push to the branch: `git push origin feature-name`.
5. Create a pull request.

## License
This project is licensed under the MIT License.