# Newsletter Portal

Public newsletter library for Morad Yousuf Behbehani, with a staff dashboard.

- **Readers** browse covers; clicking a cover downloads that newsletter's PDF directly. No login. Visits and downloads are counted anonymously.
- **Managers** sign in to upload newsletters and view the dashboard.
- **Admins** can do everything a manager can, plus edit/delete newsletters and create/edit/delete users.

Stack: PostgreSQL · FastAPI (managed with `uv`) · React + Vite + TypeScript. No Docker.

```
newsletter-portal/
├── backend/
│   ├── pyproject.toml          # uv project
│   ├── .env.example
│   ├── app/
│   │   ├── main.py             # app, startup (tables + first admin), serves frontend build
│   │   ├── core/               # config, security (bcrypt/JWT), login throttle, errors
│   │   ├── db/                 # engine/session, Base
│   │   ├── models/             # User, Newsletter, Visit, Download
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── services/           # covers, storage, newsletters, users, visitors, stats
│   │   └── api/                # deps (auth/roles) + routes
│   ├── storage/                # uploaded PDFs + generated covers (git-ignored)
│   └── tests/
└── frontend/
    ├── vite.config.ts          # dev proxy: /api -> :8000
    └── src/                    # api client, auth context, pages, components, styles
```

## Run it (development)

Prerequisites: PostgreSQL, [uv](https://docs.astral.sh/uv/), Node 20+.

```bash
# 1. Database
createdb newsletters            # or: psql -c "CREATE DATABASE newsletters;"

# 2. Backend
cd backend
cp .env.example .env
#   edit .env: set DATABASE_URL, SECRET_KEY and FIRST_ADMIN_PASSWORD
#   SECRET_KEY: python -c "import secrets; print(secrets.token_urlsafe(48))"
uv sync
uv run uvicorn app.main:app --reload --port 8010

# 3. Frontend (second terminal)
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

On first start the tables are created and an admin is made from `FIRST_ADMIN_USERNAME` / `FIRST_ADMIN_PASSWORD` (only when there are no users). Sign in at `/login`, then create managers under **Dashboard → Users**. API docs: http://localhost:8000/docs.

## Run it (production, single process)

```bash
cd frontend && npm install && npm run build      # outputs frontend/dist
cd ../backend
# in .env set COOKIE_SECURE=true (when served over HTTPS)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
```

If `frontend/dist` exists, FastAPI serves the React app and the API from the same origin, so no CORS setup is needed. Put nginx/Caddy in front for HTTPS and set `client_max_body_size 60m` (uploads allow 50 MB). Back up `backend/storage/` along with the database.

## How the main features work

**Cover generation.** On upload, the first page of the PDF is rendered (PyMuPDF) and center-cropped/scaled with Pillow to one fixed size, saved as JPEG. A custom image goes through the *same* crop, so all covers match. The ratio and size are in `.env`: `COVER_ASPECT_WIDTH`, `COVER_ASPECT_HEIGHT`, `COVER_WIDTH_PX` (default 16:9, 1280×720 to match the existing cards and slide decks). Admins can later change the cover, or replace the PDF, from **Dashboard → Newsletters**.

**Anonymous analytics (no login).** The server gives each browser a random first-party cookie (`visitor_id`, HttpOnly, SameSite=Lax, 1 year). The public pages call `POST /api/track/visit` on load; downloads are counted inside `GET /api/newsletters/{id}/download`. Unique visitors = distinct cookie ids. Only a salted hash of the IP is stored, never the raw address. Obvious bots/crawlers are ignored, and signed-in staff aren't counted. Cookie-clearing or a second browser counts as a new visitor, which is the normal limit of cookie-based counting.

**Auth.** `POST /api/auth/login` returns a bearer JWT that expires after 8 hours (`ACCESS_TOKEN_EXPIRE_MINUTES=480`). The user is re-read from the database on every request, so disabling/deleting/demoting someone takes effect immediately. The UI also signs out on expiry. Login is throttled (5 failures per 15 min per IP + username, in memory).

| Action | Public | Manager | Admin |
| --- | :-: | :-: | :-: |
| Browse, view, download newsletters | ✓ | ✓ | ✓ |
| Upload newsletter | | ✓ | ✓ |
| View dashboard | | ✓ | ✓ |
| Edit / delete newsletters, replace PDF or cover | | | ✓ |
| Create / edit / delete users | | | ✓ |
| Change own password | | ✓ | ✓ |

Safeguards: you can't delete, demote or deactivate yourself, and the last active admin can't be removed.

## Tests

```bash
cd backend && uv run pytest
```

Covers cover-cropping (needs no database), PDF rendering, passwords and token expiry.

## Notes

- Replace `frontend/public/logo.svg` with the official logo file (same name). The one included is a placeholder.
- Tables are created automatically with `create_all`. Before changing the schema in a live system, add Alembic migrations.
- `npm run typecheck` runs the TypeScript checker; `npm run build` doesn't block on it.
