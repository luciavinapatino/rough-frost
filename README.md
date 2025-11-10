# Recipe App - Django + PostgreSQL

A simple Django webapp with PostgreSQL database connection.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL installed and running
- pip (Python package manager)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL Database

Make sure PostgreSQL is running on your machine, then create a database:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE recipeapp_db;

# Exit psql
\q
```

### 3. Configure Environment Variables

Copy the example environment file and update it with your database credentials:

```bash
cp .env.example .env
```

Edit `.env` and update the database settings if needed:
- `DB_NAME`: Your PostgreSQL database name (default: `recipeapp_db`)
- `DB_USER`: Your PostgreSQL username (default: `postgres`)
- `DB_PASSWORD`: Your PostgreSQL password (default: `postgres`)
- `DB_HOST`: Database host (default: `localhost`)
- `DB_PORT`: Database port (default: `5432`)
- `SECRET_KEY`: A secret key for Django (generate a new one for production)
- `DEBUG`: Set to `True` for development, `False` for production

### 4. Run Migrations

Navigate to the django-project directory and run migrations to create database tables:

```bash
cd django-project
python manage.py migrate
```

### 5. Start the Development Server

```bash
python manage.py runserver
```

The app will be available at `http://localhost:8000`

## Project Structure

```
rough-frost/
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── README.md                # This file
└── django-project/
    ├── manage.py            # Django management script
    ├── recipeapp/           # Django project settings
    │   ├── settings.py      # Project configuration
    │   ├── urls.py          # Main URL routing
    │   └── wsgi.py          # WSGI configuration
    └── recipes/             # Recipes app
        ├── views.py         # View functions
        ├── urls.py          # App URL routing
        └── templates/       # HTML templates
            └── home.html    # Home page template
```

## Next Steps

- Add recipe models
- Create recipe views and templates
- Add user authentication
- Implement recipe search functionality

