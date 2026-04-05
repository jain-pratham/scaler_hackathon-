# ---------- STEP 1: BUILD FRONTEND ----------
FROM node:22 AS frontend

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build


# ---------- STEP 2: BACKEND ----------
FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# install node (for next start)
RUN apt-get update && apt-get install -y nodejs npm

# copy frontend build
COPY --from=frontend /app ./

EXPOSE 8000

# RUN BOTH BACKEND + FRONTEND
ENV PYTHON_BACKEND_URL=http://127.0.0.1:8001
CMD bash -c "uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 & npx next start -p 8000"