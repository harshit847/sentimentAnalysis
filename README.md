# Sentiment SaaS (FastAPI + Next.js)

Full-stack sentiment and emotion analysis: **VADER** for text, **FER + OpenCV** for faces, **Web Speech API** on the client for voice (transcript analyzed as text), **OpenAI** for explanations (optional), **MongoDB** for history, **JWT** authentication.

## Architecture

| Layer | Stack |
|--------|--------|
| Frontend | Next.js 14 (App Router), Tailwind CSS, Recharts |
| Backend | FastAPI, Motor (async MongoDB) |
| Auth | JWT (Bearer tokens, `Authorization` header) |

## API overview

| Prefix | Purpose |
|--------|---------|
| `POST /auth/register`, `POST /auth/login` | Sign up / sign in (returns `access_token`) |
| `GET /auth/me`, `PATCH /auth/me` | Profile |
| `POST /analyze/text` | JSON `{ "text": "..." }` |
| `POST /analyze/face` | `multipart/form-data` image field `file` |
| `POST /analyze/voice` | JSON `{ "text": "...", "locale": "optional" }` (transcribed speech) |
| `GET /history` | Paginated list (`limit`, `skip`, `analysis_type`) |
| `GET /history/export/csv` | CSV download |
| `DELETE /history/{id}` | Delete one record |
| `GET /analytics?days=30` | Stats + distributions + daily trend |

Interactive docs: `http://127.0.0.1:8000/docs` (when the API is running).

## Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas URI)
- Optional: OpenAI API key for AI explanations

## Backend setup

1. **Virtual environment**

```powershell
cd sentiment-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. **Environment**

Copy `.env.example` to `.env` and set at least:

- `MONGO_URI` — e.g. `mongodb://localhost:27017` or Atlas connection string  
- `JWT_SECRET` — long random string in production  
- `OPENAI_API_KEY` — optional; if empty, explanations use built-in fallbacks  
- `CORS_ORIGINS` — include your Next.js origin, e.g. `http://localhost:3000`

3. **Run the API**

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health checks: `GET /health`, `GET /db-health`.

## Frontend setup

1. **Install and env**

```powershell
cd web
npm install
copy .env.local.example .env.local
```

Edit `.env.local`:

- `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` (must match your FastAPI base URL)

2. **Run the app**

```powershell
npm run dev
```

Open `http://localhost:3000`. Register a user, then use **Dashboard**, **Analyze** (text / camera / voice), **History**, **Analytics**, and **Profile**.

## Integration notes

- **CORS**: The API allows origins listed in `CORS_ORIGINS`. For production, set this to your real web origin(s) only.
- **Auth**: After login/register, the SPA stores the JWT in `localStorage` and sends `Authorization: Bearer <token>` on API calls.
- **Voice**: The browser transcribes speech; the app sends the transcript to `POST /analyze/voice`. Use Chrome/Edge for best Web Speech API support.
- **Camera**: Face analysis uses a single JPEG frame uploaded to `POST /analyze/face` (same idea as the legacy `camera.html` demo).
- **Legacy data**: Older history documents without `user_id` will not appear for logged-in users; new analyses are always scoped by user.

## Production hints

- Use a strong `JWT_SECRET`, HTTPS, and restricted `CORS_ORIGINS`.
- Consider httpOnly cookies instead of `localStorage` for tokens if you add a BFF or same-site deployment pattern.
- Scale MongoDB and tune indexes (`user_id` + `timestamp` are created on startup).
