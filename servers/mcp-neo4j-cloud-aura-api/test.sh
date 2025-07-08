if [ -f .env ]; then
    uv run --env-file .env pytest tests
else
    uv run pytest tests
fi
