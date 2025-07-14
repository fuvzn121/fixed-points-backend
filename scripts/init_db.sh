#!/bin/bash

echo "🚀 Starting PostgreSQL with Docker Compose..."
docker-compose up -d postgres

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

echo "📝 Creating initial migration..."
cd fixed-points-backend
uv run alembic revision --autogenerate -m "Initial migration"

echo "🔄 Running migrations..."
uv run alembic upgrade head

echo "✅ Database setup complete!"