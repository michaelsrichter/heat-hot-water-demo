FROM node:24-bookworm-slim AS frontend-build
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY docs/ /src/docs/
COPY backend/app /src/backend/app
COPY backend/data /src/backend/data
COPY src/hpd-review-agent /src/src/hpd-review-agent
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000
WORKDIR /app
COPY backend/pyproject.toml ./backend/pyproject.toml
COPY backend/app ./backend/app
COPY backend/data ./backend/data
RUN pip install --no-cache-dir ./backend
COPY --from=frontend-build /src/frontend/dist ./backend/app/static
ENV PYTHONPATH=/app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
