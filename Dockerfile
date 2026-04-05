# ---------- STEP 1: BUILD NEXT.JS ----------
FROM node:18 AS frontend

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend ./
RUN npm run build


# ---------- STEP 2: PYTHON BACKEND ----------
FROM python:3.10-slim

WORKDIR /app

# copy backend + all files
COPY . .

# install python deps
RUN pip install --no-cache-dir -r requirements.txt

# install node for running Next.js
RUN apt-get update && apt-get install -y nodejs npm

# copy built frontend from previous stage
COPY --from=frontend /app/frontend .//frontend

# go to frontend folder
WORKDIR /app/frontend

# expose HF required port
EXPOSE 8000

# run Next.js (UI)
CMD ["npm", "start"]