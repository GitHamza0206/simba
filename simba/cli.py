import os
import subprocess
import sys
from pathlib import Path

import click


@click.group()
def cli():
    """Simba CLI: Manage your Simba application."""


@cli.command("server")
def run_server():
    """Run the Simba FastAPI server."""
    click.echo("Starting Simba server...")
    from dotenv import load_dotenv

    from simba.__main__ import create_app

    load_dotenv()
    app = create_app()
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)


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
