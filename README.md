# Habit Friends Backend

A FastAPI backend for a habit-tracking app with friends, integrated with Supabase for authentication.

## Features

- JWT authentication via Supabase
- Habit CRUD operations (Create, Read, Update, Delete) per user
- PostgreSQL database (Supabase)
- Image upload for habits

## Installation

### Environment Variables

Copy `.env` and set the following environment variables:

- `DATABASE_URL`: PostgreSQL connection string from Supabase (e.g., `postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres`)
- `SUPABASE_URL`: Your Supabase project URL (e.g., `https://[project].supabase.co`)

### Local Development

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the server:
   ```
   uvicorn main:app --reload
   ```

The API will be available at http://127.0.0.1:8000

### Docker

1. Build and run with Docker Compose:
   ```
   docker-compose up --build
   ```

The API will be available at http://localhost:8000 (or your VPS IP:8000)

## API Endpoints

### Habits
- POST /habits/ - Create a new habit (requires Bearer token)
- GET /habits/{habit_id} - Get a habit by ID (requires Bearer token)
- GET /habits/ - Get all habits for the authenticated user (requires Bearer token)
- PUT /habits/{habit_id} - Update a habit (requires Bearer token)
- DELETE /habits/{habit_id} - Delete a habit (requires Bearer token)

## Authentication

All habit endpoints require a Bearer token obtained from Supabase authentication. Include the token in the Authorization header: `Authorization: Bearer <token>`

## Database

The app uses SQLite database (`habit_friends.db`) which is created automatically on first run.