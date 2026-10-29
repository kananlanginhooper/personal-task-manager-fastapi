# The UI comes from the sibling clone of personal-task-manager-angular, passed in as the "ui-src" build context
# (docker-compose.yml sets it to ../personal-task-manager-angular).
FROM node:20-slim AS ui
WORKDIR /ui
COPY --from=ui-src package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY --from=ui-src angular.json tsconfig.json tsconfig.app.json ./
COPY --from=ui-src src ./src
COPY --from=ui-src public ./public
RUN npx ng build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UI_DIR=/app/ui FORWARDED_ALLOW_IPS=127.0.0.1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY --from=ui /ui/dist/personal-task-manager/browser ./ui

# readable by the app user whatever the modes were in the clone it was built from
RUN chmod -R a+rX /app && useradd --system --uid 10001 app
USER app

EXPOSE 8095
# --proxy-headers: behind a reverse proxy (TLS ending there), X-Forwarded-Proto/For from FORWARDED_ALLOW_IPS are honored
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8095 --proxy-headers --forwarded-allow-ips \"$FORWARDED_ALLOW_IPS\""]
