# List available commands
default:
    @just --list --unsorted

# Run the API server
[group("api")]
api *ARGS:
    uv run fastapi run src/pytixl/api/app.py --reload
