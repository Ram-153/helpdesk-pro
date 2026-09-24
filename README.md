# HelpDesk Pro

HelpDesk Pro is a REST API-based help desk and ticket management system built with Python and Flask.

It provides role-based access for customers, support agents, and administrators, with ticket management, attachments, notifications, dashboards, and administrative controls.

## Features

* User registration and login
* JWT-based authentication
* Role-based access control
* Customer ticket creation
* Ticket assignment to support agents
* Ticket status workflow
* Ticket comments
* Ticket attachments
* Ticket priority and category management
* Agent dashboard and analytics
* Customer and agent notifications
* Mark notifications as read
* Admin user management
* Admin role management
* Admin account activation/deactivation
* Admin ticket assignment
* Admin statistics
* REST API architecture
* Automated API testing with pytest

## Technology Stack

* Python
* Flask
* Flask-SQLAlchemy
* Flask-JWT-Extended
* Flask-CORS
* SQLite
* Pytest
* Pytest-Flask
* python-dotenv

## User Roles

### Customer

Customers can:

* Register and log in
* Create support tickets
* View their tickets
* View ticket details
* Add comments
* Upload attachments
* Receive ticket-related notifications

### Agent

Agents can:

* Log in
* View assigned tickets
* Update ticket status
* Add comments
* Work with ticket attachments
* View dashboard information
* Receive ticket-related notifications

### Admin

Administrators can:

* View users
* Create users
* View individual users
* Change user roles
* Activate/deactivate users
* View available agents
* Assign tickets to agents
* View system statistics

## Ticket Workflow

Tickets follow a controlled workflow based on their current state.

```text
OPEN
  |
  v
ASSIGNED
  |
  v
IN_PROGRESS
  |
  v
RESOLVED
  |
  v
CLOSED
```

## Project Structure

```text
helpdesk-pro/
|
|-- app/
|   |-- models/
|   |   |-- attachment.py
|   |   |-- comment.py
|   |   |-- notification.py
|   |   |-- ticket.py
|   |   `-- user.py
|   |
|   |-- routes/
|   |   |-- admin.py
|   |   |-- attachment.py
|   |   |-- auth.py
|   |   |-- dashboard.py
|   |   |-- health.py
|   |   |-- notification.py
|   |   `-- ticket.py
|   |
|   |-- services/
|   |   `-- attachment_service.py
|   |
|   |-- extensions.py
|   `-- __init__.py
|
|-- config/
|   |-- __init__.py
|   `-- settings.py
|
|-- tests/
|   |-- conftest.py
|   |-- test_admin.py
|   |-- test_attachments.py
|   |-- test_auth.py
|   |-- test_dashboard.py
|   |-- test_health.py
|   |-- test_notifications.py
|   |-- test_ticket.py
|   `-- test_ticket_workflow.py
|
|-- .env.example
|-- .gitignore
|-- requirements.txt
`-- run.py
```

## Testing

The project includes automated API tests using pytest and pytest-flask.

Run the complete test suite with:

```powershell
pytest -q
```

The current test suite contains 48 tests.

## Configuration

Create a `.env` file in the project root based on `.env.example`.

Example:

```text
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=sqlite:///helpdesk.db
```

Do not commit `.env` files or real secrets to Git.

## Running the Application

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the Flask application:

```powershell
python run.py
```

The API runs locally on:

```text
http://127.0.0.1:5000
```

## Project Status

HelpDesk Pro currently includes:

* Authentication and authorization
* Ticket management
* Ticket attachments
* Dashboard and analytics
* Notifications
* Administrative management
* Automated testing
* Production-oriented configuration
* Git-based source control
