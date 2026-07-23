# SikaTrack PWA (Svelte + Vite)

The installable Progressive Web App frontend for SikaTrack, talking to the
Django REST API in `../api/`. It shares an origin with Django (via the dev
proxy below, or Django's own static files in production), so auth is plain
session cookies + CSRF — no token handling.

## Development

Run Django and Vite side by side:

```bash
# Terminal 1 — from the repo root
pipenv run python manage.py runserver

# Terminal 2 — from frontend/
npm install
npm run dev
```

Visit `http://localhost:5173`. Requests to `/api/*` are proxied to Django
on port 8000 (see `vite.config.js`), so the browser only ever talks to one
origin.

## Building for production

```bash
npm run build
```

Outputs to `../static/app/` (gitignored — it's a build artifact, not
source). Django serves the built shell at `/app/` and the static assets it
references from `/static/app/...` via its existing staticfiles app; no
extra Django config is needed once the build exists. Deploys must run
`npm run build` before `collectstatic`.

## Routing

Client-side routing is hash-based (`svelte-spa-router`), e.g. `/app/#/holdings`
— this keeps the Django side to a single `/app/` route with no wildcard
path capture or server-side route awareness required.

## PWA

`vite-plugin-pwa` generates the manifest and service worker at build time.
API requests are never cached by the service worker (`NetworkOnly`) — the
app should always show fresh portfolio data when online; the service
worker exists only to make the app shell installable and load instantly.

The bundled icons in `public/icons/` are solid-color placeholders — swap
them for real branded icons before shipping an install prompt to users.
