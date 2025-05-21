import os
import subprocess
import sys
from pathlib import Path

import click


@click.group()
def cli():
    """Simba CLI: Manage your Simba application."""


@cli.command("server")
@click.option('--reload', is_flag=True, default=False, help='Enable auto-reload for development.')
def run_server(reload):
    """Run the Simba FastAPI server."""
    click.echo("Starting Simba server..." + (" (with reload)" if reload else ""))
    from dotenv import load_dotenv

    load_dotenv()
    import uvicorn
    if reload:
        # Use import string for reload mode
        uvicorn.run("simba.__main__:app", host="0.0.0.0", port=5005, workers=1, reload=True)
    else:
        from simba.__main__ import create_app
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=5005, workers=1)


@cli.command("worker")
def run_worker():
    """Run the Celery worker for parsing tasks."""
    click.echo("Starting Celery worker for parsing tasks...")
    os.system("celery -A simba.core.celery_config worker -Q parsing,summaries,ingestion --loglevel=info ")

@cli.command("parsers")
def run_parsers():
    """Run the Celery worker for parsing tasks."""
    click.echo("Starting Celery worker for parsing tasks...")
    os.system("celery -A simba.core.celery_config.celery_app worker --loglevel=info -Q parsing")


@cli.command("front")
def run_frontend():
    """Run the React frontend development server."""
    # Look for frontend directory at the root level
    current_dir = Path.cwd()
    frontend_dir = current_dir / "frontend"

    if not frontend_dir.exists():
        click.echo(
            "Error: Frontend directory not found. Please make sure you're in the project root directory."
        )
        return

    os.chdir(frontend_dir)

    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        click.echo("Installing dependencies...")
        subprocess.run("npm install", shell=True, check=True)

    click.echo("Starting React frontend...")
    subprocess.run("npm run dev", shell=True)


@cli.command("help")
def show_help():
    """Show help for Simba CLI."""
    click.echo(cli.get_help(ctx=click.get_current_context()))


def main():
    if len(sys.argv) == 1:
        show_help()
    else:
        cli()


if __name__ == "__main__":
    main()
