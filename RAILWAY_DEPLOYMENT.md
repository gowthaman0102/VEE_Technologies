# Railway Deployment

This repository contains two deployable services. Deploy them as two Railway services from the same GitHub repository.

## Backend service

1. Create a Railway service from this repository.
2. Set **Root Directory** to `/backend`.
3. Railpack will install `requirements.txt` and use `backend/Procfile`:

   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. Add the production database, Redis, and application secrets as Railway variables.
5. Add `CORS_ORIGINS` with the frontend service URL, for example:

   `https://your-frontend-service.up.railway.app`

6. Generate a public domain for the backend and verify `/api/v1/health`.

## Frontend service

1. Create a second Railway service from the same repository.
2. Set **Root Directory** to `/frontend`.
3. Railpack will install `package-lock.json`, build Next.js, and use `frontend/Procfile`:

   `npm run start -- --hostname 0.0.0.0 --port $PORT`

4. Set `NEXT_PUBLIC_API_BASE_URL` to the backend public URL plus `/api/v1`, for example:

   `https://your-backend-service.up.railway.app/api/v1`

5. Redeploy the frontend after setting that variable because Next.js embeds `NEXT_PUBLIC_*` values during the build.

The original Railpack error occurred because Railway was pointed at the repository root. The root contains both `backend/` and `frontend/`, so Railpack cannot infer one application to build. Each service must use its corresponding root directory.
