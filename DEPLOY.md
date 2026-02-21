# Deploy Scriptura Loquens on Vultr with EasyPanel + PostgreSQL

This guide walks you through deploying the **backend server** on Vultr using EasyPanel and PostgreSQL. The React client is deployed separately on Netlify.

## Overview

- **EasyPanel**: Server control panel (like a self-hosted Heroku) on Vultr Marketplace
- **PostgreSQL**: Managed via EasyPanel's built-in Postgres service
- **Server**: Flask API only (client on Netlify)

## Step 1: Deploy Vultr + EasyPanel

1. Go to [Vultr Marketplace - EasyPanel](https://www.vultr.com/marketplace/apps/easypanel/)
2. Click **Deploy** and choose a plan (minimum **2GB RAM**)
3. Select a region and deploy
4. Wait ~5 minutes for the server to boot
5. Access EasyPanel at `http://YOUR_SERVER_IP:3000`
6. Create an admin account on first login

## Step 2: Add PostgreSQL

1. In EasyPanel, click **Create** → **New project** → name it `scriptura`
2. In the project, click **+ Service** → **Postgres**
3. Name it `postgres` (or `db`)
4. Click **Deploy** to start the database
5. Go to the **Credentials** tab and copy:
   - `POSTGRES_USER` (usually `postgres`)
   - `POSTGRES_PASSWORD`
   - `POSTGRES_DB` (usually `postgres`)
6. (Optional) Expose a port if you need remote DB access; otherwise keep it internal

Connection string format:
```
postgresql://POSTGRES_USER:POSTGRES_PASSWORD@postgres:5432/POSTGRES_DB
```

EasyPanel creates a DNS name `postgres` for the Postgres service within the same project, so use `postgres` as the host.

## Step 3: Deploy the Server

1. In the same project, click **+ Service** → **App**
2. **Source**: Connect your GitHub repo (source path: `server/`) or upload a zip containing:
   - `Dockerfile`
   - `.dockerignore`
   - `app/`
   - `requirements.txt`
   - `run.py`
3. **Build** tab:
   - Build method: **Dockerfile**
   - Dockerfile path: `Dockerfile` (at root of server folder)
4. **Domains & Proxy**:
   - Add your domain (e.g. `app.yourdomain.com`) or use the auto-generated one
   - **Proxy port**: `5000` (Flask listens on 5000)
   - Enable **HTTPS** (Let's Encrypt)
5. **Mounts** (required for uploads and audio):
   - Type: **Volume**
   - Mount path: `/app/uploads`
   - Name: `uploads`
   - Add another:
   - Mount path: `/app/audio`
   - Name: `audio`

## Step 4: Environment Variables

In the App service → **Environment** tab, add:

| Variable | Value | Required |
|----------|-------|----------|
| `SECRET_KEY` | A long random string (e.g. from `openssl rand -hex 32`) | Yes |
| `DATABASE_URL` | `postgresql://postgres:PASSWORD@postgres:5432/postgres` | Yes |
| `ADMIN_EMAIL` | Your admin login email | Yes |
| `ADMIN_PASSWORD` | Strong admin password | Yes |
| `FRONTEND_URL` | Your Netlify URL (e.g. `https://scriptura.netlify.app`) | Yes |
| `GOOGLE_GEMINI_API_KEY` | Your Gemini API key (from AI Studio) | Yes* |
| `TTS_PROVIDER` | `edge` or `google` or `elevenlabs` | Yes |
| `PORT` | `5000` (EasyPanel sets this automatically) | Optional |
| `MAX_CONTENT_LENGTH_MB` | `100` | Optional |
| `MAX_PDF_PAGES` | `5` | Optional |

\* Required for character detection. For TTS you can use `edge` (free) or configure Google/ElevenLabs.

**Netlify**: In your Netlify project, set `REACT_APP_API_URL` to your API domain (e.g. `https://api.yourdomain.com/api`).

## Step 5: Deploy

1. Save all settings
2. Click **Deploy**
3. Watch the **Logs** tab for build progress
4. When ready, open your domain in the browser

## Troubleshooting

### Database connection errors
- Ensure `DATABASE_URL` uses `postgres` as host (the internal service name)
- PostgreSQL must be running before the app starts

### 500 errors after idle
If the app fails after being idle, Docker may kill DB connections. The app uses `pool_pre_ping` to handle this. If issues persist, restart the app service.

### Uploads / audio not persisting
Verify the **Mounts** are set correctly and paths match `/app/uploads` and `/app/audio`.

### CORS errors
Set `FRONTEND_URL` to the exact URL users visit (with `https://`).

## Local development with PostgreSQL

To test against PostgreSQL locally:

```bash
# Start Postgres (Docker)
docker run -d --name scriptura-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=scriptura_loquens \
  -p 5432:5432 postgres:16

# In server/.env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scriptura_loquens
```

Then run migrations via `init_db()` (automatic on app startup) or Flask-Migrate if you add it.
