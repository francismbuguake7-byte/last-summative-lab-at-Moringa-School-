# Productivity Events API

A session-authenticated Flask API for users to manage their own productivity events. It includes bcrypt password hashing, SQLite persistence, ownership-based authorization, paginated event listings, and database migrations.

## Requirements

- Python 3.8.13 or newer
- Pipenv

## Installation and setup

```bash
pipenv install
pipenv shell
```

Set a unique secret key before running outside local development. The app refuses to start with the development fallback when `FLASK_ENV=production`:

```bash
export SECRET_KEY="replace-with-a-long-random-secret"
```

The default database is `instance/productivity.db`. To use another database, set `DATABASE_URL` (for example, `sqlite:///productivity.db`).

Apply the included database migration:

```bash
flask --app app db upgrade
```

When you change a model, create and apply a new migration:

```bash
flask --app app db migrate -m "Describe the schema change"
flask --app app db upgrade
```

Create a demo account and sample events:

```bash
python seed.py
```

The seed command creates `demo` with password `DemoPass123!` and three events. Use this account only for local development.

## Run

```bash
flask --app app run
```

The API listens on `http://127.0.0.1:5000`. Browser clients must send requests with credentials enabled so the session cookie is included. Cookies are HTTP-only and use `SameSite=Lax`; set `COOKIE_SECURE=true` when serving the API over HTTPS.

For a browser frontend on another origin, the default allowed origin is `http://localhost:3000`. Set `CORS_ORIGINS` to a comma-separated list of trusted origins to change it; credentialed requests are enabled only for those origins.

## Authentication

Authentication uses Flask's signed session cookie. Send JSON with the `Content-Type: application/json` header.

| Method | Path | Description |
|---|---|---|
| `POST` | `/signup` | Create an account with `username` and `password`; signs in the new user. |
| `POST` | `/login` | Authenticate with `username` and `password`. |
| `POST` | `/logout` | Clear the current session. |
| `GET` | `/check_session` | Return the currently authenticated user, or `401`. |
| `GET` | `/me` | Alias for `/check_session`. |

Usernames are trimmed and case-insensitive. Passwords must be between 8 and 72 UTF-8 bytes and are stored as bcrypt hashes. Signup returns `409` if the username is already taken; invalid credentials return `401`.

## Event endpoints

Every event endpoint requires an authenticated session. Events are scoped to their owner; another user's event is treated as not found.

| Method | Path | Description |
|---|---|---|
| `GET` | `/events?page=1&per_page=10` | List the current user's events, ordered by ID. `per_page` must be between 1 and 100. |
| `POST` | `/events` | Create an event. Requires a non-empty `title`; `description` is optional. |
| `PATCH` | `/events/<id>` | Update the event's `title` and/or `description`. |
| `DELETE` | `/events/<id>` | Delete an owned event; returns `204` on success. |

Event objects contain `id`, `title`, `description`, and `created_at`. The list response has this shape:

```json
{
  "events": [
    {
      "id": 1,
      "title": "Plan the week",
      "description": "Set priorities",
      "created_at": "2026-10-31T12:00:00+00:00"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 1,
    "pages": 1
  }
}
```

## Example

```bash
curl -i -c cookies.txt -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"Password123!"}' \
  http://127.0.0.1:5000/signup

curl -i -b cookies.txt -H 'Content-Type: application/json' \
  -d '{"title":"Plan the week","description":"Set priorities"}' \
  http://127.0.0.1:5000/events

curl -i -b cookies.txt 'http://127.0.0.1:5000/events?page=1&per_page=10'
```

## Tests

```bash
pipenv run pytest
```
