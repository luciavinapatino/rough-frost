# Recipe App - Django + PostgreSQL

A simple Django webapp for managing and sharing recipes with PostgreSQL database support.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- PostgreSQL (optional; SQLite is used by default for local development)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

The application automatically defaults to SQLite for local development. To use PostgreSQL:

Edit `.env` and set the following variables:
- `DB_ENGINE`: Set to `postgresql` to use PostgreSQL (default: `sqlite`)
- `DB_NAME`: PostgreSQL database name (default: `recipeapp_db`)
- `DB_USER`: PostgreSQL username (default: `postgres`)
- `DB_PASSWORD`: PostgreSQL password (default: `postgres`)
- `DB_HOST`: Database host (default: `localhost`)
- `DB_PORT`: Database port (default: `5432`)
- `SECRET_KEY`: Secret key for Django (required; change for production)
- `DEBUG`: Set to `True` for development, `False` for production

**For deployment platforms (Render, Heroku, etc.):** These services provide a `DATABASE_URL` environment variable automatically. The application detects and uses this if present, overriding individual database settings.

### 3. Run Migrations

Navigate to the django-project directory and create database tables:

```bash
cd django-project
python manage.py migrate
```

(Optional) Seed the database with test data:

```bash
python3 seed_data.py
```

### 4. Start the Development Server

```bash
python manage.py runserver
```

The app will be available at `http://localhost:8000`

## Deployment

### To Heroku or Render

This project includes a `Procfile` configured to run with Gunicorn. When deploying to Heroku or Render:

1. Ensure these environment variables are set on the platform:
   - `SECRET_KEY` (generate a new secure key, do NOT use the dev default)
   - `DEBUG` (set to `False`)
   - `DATABASE_URL` (automatically provided by the platform for managed databases)

2. The platform will automatically run migrations during deployment.

3. Gunicorn is included in `requirements.txt` and configured in the `Procfile`.

## Project Structure

```
rough-frost/
├── README.md                   # This file
├── Procfile                    # Production deployment configuration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── docs/                       # Documentation
│   ├── definition-of-done.md   # Sprint completion criteria
│   ├── definition-of-ready.md  # Story readiness criteria
│   ├── team-charter.md         # Team roles and agreements
│   └── sprints/                # Sprint reviews and planning
├── scripts/
│   └── migrate_and_smoke.sh    # Database setup and smoke test
└── django-project/
    ├── manage.py               # Django management script
    ├── db.sqlite3              # Local SQLite database (dev only)
    ├── seed_data.py            # Test data generator
    ├── recipeapp/              # Django project configuration
    │   ├── settings.py         # Settings (database, apps, middleware, etc.)
    │   ├── urls.py             # Main URL routing
    │   ├── wsgi.py             # WSGI configuration for production
    │   └── asgi.py             # ASGI configuration (async support)
    └── recipes/                # Main recipes application
        ├── models.py           # Database models (Recipe, Tag, Step, Favorite)
        ├── views.py            # View functions (home, create_recipe, recipe_detail)
        ├── urls.py             # App URL routing
        ├── forms.py            # Form classes (RecipeForm)
        ├── admin.py            # Django admin configuration
        ├── apps.py             # App configuration
        ├── tests.py            # Unit tests
        ├── migrations/         # Database migrations
        └── templates/          # HTML templates
            ├── home.html       # Recipe listing and search
            ├── create_recipe.html   # Recipe creation form
            └── recipe_detail.html   # Individual recipe display
```

## Features

- **Recipe Management**: Create, view, and search recipes
- **Flexible Search**: PostgreSQL full-text search when available; falls back to basic search for SQLite
- **Tags**: Categorize recipes with custom tags
- **Steps**: Detailed, numbered cooking instructions
- **User Favorites**: Save favorite recipes with personal notes
- **Django Admin**: Manage recipes, tags, steps, and favorites through the admin panel

## Database Configuration

The application automatically detects the available database based on environment variables:

1. **Production (Recommended)**: Uses `DATABASE_URL` if available
2. **PostgreSQL**: Set `DB_ENGINE=postgresql` and individual `DB_*` variables
3. **SQLite (Default)**: Used for local development if no other configuration is provided

## Notes for Developers

- **Search Optimization**: PostgreSQL provides weighted full-text search. On SQLite, search uses case-insensitive substring matching.
- **Database Queries**: Views use `select_related()` and `prefetch_related()` for optimal query performance.
- **Test Data**: Run `seed_data.py` to populate the database with sample recipes.
- **Smoke Test**: Run `scripts/migrate_and_smoke.sh` to verify database connectivity and basic ORM functionality.
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

