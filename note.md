# run postgres with pgvector
docker run -e POSTGRES_USER=yg2404 \
           -e POSTGRES_PASSWORD=123 \
           -e POSTGRES_DB=llm_rag \
           --name pgsql \
           -p 5432:5432 \
           -d pgvector/pgvector:0.8.1-pg18-trixie

# connect to the database
psql -h localhost -U yg2404 -d llm_rag -p 5432

# add pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

# add open-webui database and user
CREATE DATABASE openwebui_db;
CREATE USER openwebui WITH ENCRYPTED PASSWORD 'openwebui_password';
GRANT ALL PRIVILEGES ON DATABASE openwebui_db TO openwebui;

# run open-webui with postgres database
docker run -d --name openwebui_postgres \
  -p 8080:8080 \
  -e DB_TYPE=postgres \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=5432 \
  -e DB_NAME=openwebui_db \
  -e DB_USER=openwebui \
  -e DB_PASSWORD=openwebui_password \
  openwebui/open-webui:latest

