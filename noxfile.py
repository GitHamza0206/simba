import nox
from datetime import datetime
import subprocess
import re
import os
import sys
import shutil

nox.options.sessions = ["tests", "lint", "type_check"]
nox.options.reuse_existing_virtualenvs = True

PYTHON_VERSIONS = ["3.12"]

@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
def tests(session):
    """
    Install dependencies via Poetry and run the test suite with pytest (only inside /simba).
    """
    # Install Poetry in this session environment
    session.run("pip", "install", "poetry", external=True)
    # Use Poetry to install all dependencies (including dev/test)
    session.run("poetry", "install", external=True)
    # Run tests only inside the simba directory
    session.run("pytest", "simba", external=True)

@nox.session(venv_backend="uv")
def lint(session):
    """
    Install flake8 and run lint checks.
    """
    # Install flake8 into this session environment
    session.install("flake8")
    # Lint the 'simba' package folder using config from pyproject.toml
    session.run("flake8", "simba", external=True)

@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
def format(session):
    """
    Format code using black and isort.
    """
    session.install("black", "isort")
    # Format code with black
    session.run("black", "simba", "tests", external=True)
    # Sort imports with isort (compatible with black)
    session.run("isort", "--profile=black", "simba", "tests", external=True)

@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
def type_check(session):
    """
    Run static type checking with mypy.
    """
    session.install("mypy")
    # Install dependencies via Poetry
    session.run("pip", "install", "poetry", external=True)
    session.run("poetry", "install", "--no-root", external=True)
    # Run mypy
    session.run("mypy", "simba", external=True)

@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
def security(session):
    """
    Run security checks with bandit and safety.
    """
    session.install("bandit", "safety")
    # Check for common security issues with bandit
    session.run("bandit", "-r", "simba", external=True)
    # Check dependencies for known vulnerabilities
    session.run("safety", "check", external=True)

@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
def docs(session):
    """
    Build documentation with Sphinx.
    """
    session.install("sphinx", "sphinx-rtd-theme")
    # Install dependencies via Poetry
    session.run("pip", "install", "poetry", external=True)
    session.run("poetry", "install", "--no-root", external=True)
    # Build docs
    session.run("sphinx-build", "docs", "docs/_build", external=True)

@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")        
def dev(session):
    """
    Set up a development environment with all tools.
    """
    # Install Poetry
    session.run("pip", "install", "poetry", external=True)
    # Install all dependencies including dev dependencies
    session.run("poetry", "install", external=True)
    # Install pre-commit hooks
    session.install("pre-commit")
    session.run("pre-commit", "install", external=True)

@nox.session(venv_backend="uv" ,python=PYTHON_VERSIONS)
def coverage(session):
    """
    Generate test coverage report.
    """
    session.install("pytest", "pytest-cov")
    # Install dependencies via Poetry
    session.run("pip", "install", "poetry", external=True)
    session.run("poetry", "install", "--no-root", external=True)
    # Run tests with coverage
    session.run("pytest", "--cov=simba", "--cov-report=html", external=True)
    # Open the coverage report (works on most systems)
    session.run("python", "-m", "webbrowser", "-t", "htmlcov/index.html", external=True)

@nox.session(venv_backend="uv", python=PYTHON_VERSIONS)
def release(session):
    """
    Build and publish the package to PyPI.
    Uses token authentication via environment variables:
      TWINE_USERNAME=__token__
      TWINE_PASSWORD=your-api-token
    """
    # Install build and twine
    session.install("build", "twine")
    
    # Clean up previous builds
    if os.path.exists("dist"):
        session.log("Cleaning up previous builds...")
        shutil.rmtree("dist")
    
    # Build package with standard build module
    session.log("Building package...")
    session.run("python", "-m", "build")
    
    # Check if we have credentials for PyPI
    if os.environ.get("TWINE_USERNAME") and os.environ.get("TWINE_PASSWORD"):
        session.log("Uploading to PyPI...")
        # For token authentication, TWINE_USERNAME should be "__token__"
        # and TWINE_PASSWORD should be the API token
        session.run("twine", "upload", "dist/*", external=True)
    else:
        session.log("TWINE_USERNAME and TWINE_PASSWORD environment variables not set.")
        session.log("For PyPI token authentication:")
        session.log("  TWINE_USERNAME=__token__")
        session.log("  TWINE_PASSWORD=your-api-token")
        session.log("Skipping upload.")

# The following sessions are commented out as we now use Release Please
# for automated changelog generation and release management

# @nox.session
# def changelog(session):
#     """Generate changelog from git commit history."""
#     # Install required packages
#     session.install("gitchangelog", "pystache")
#     
#     # Ensure we're using conventional commits format
#     session.log("Generating changelog from git history...")
#     
#     # Run gitchangelog and output to CHANGELOG.md
#     session.run("gitchangelog", external=True, stdout=open("CHANGELOG.md", "w"))
#     
#     # Log success
#     session.log("Changelog generated successfully at CHANGELOG.md")
#     
#     # Optionally commit the changes if in CI
#     if os.environ.get("CI") == "true":
#         try:
#             # Configure git
#             session.run("git", "config", "--global", "user.name", "CI Bot", external=True)
#             session.run("git", "config", "--global", "user.email", "ci@example.com", external=True)
#             
#             # Check if there are changes
#             result = session.run("git", "diff", "--name-only", "CHANGELOG.md", 
#                                external=True, silent=True, success_codes=[0, 1])
#             
#             if result and "CHANGELOG.md" in result:
#                 session.run("git", "add", "CHANGELOG.md", external=True)
#                 session.run("git", "commit", "-m", "docs: update changelog [skip ci]", external=True)
#                 session.run("git", "push", external=True)
#                 session.log("Committed and pushed changelog updates")
#             else:
#                 session.log("No changes to changelog detected")
#         except Exception as e:
#             session.log(f"Warning: Could not commit changelog: {e}")

# @nox.session
# def release_changelog(session):
#     """Prepare changelog for a release."""
#     if not session.posargs:
#         session.error("Please provide a version number: nox -s release_changelog -- 1.2.3")
#     
#     version = session.posargs[0]
#     today = datetime.now().strftime("%Y-%m-%d")
#     
#     session.log(f"Preparing changelog for version {version}...")
#     
#     # Install required packages
#     session.install("gitchangelog", "pystache")
#     
#     # Generate the changelog
#     session.run("gitchangelog", external=True, stdout=open("CHANGELOG.md", "w"))
#     
#     # Read the content
#     with open("CHANGELOG.md", "r") as f:
#         content = f.read()
#     
#     # Replace the first "Unreleased" with the version number
#     updated_content = content.replace("Unreleased", f"{version} - {today}", 1)
#     
#     # Write back the content
#     with open("CHANGELOG.md", "w") as f:
#         f.write(updated_content)
#     
#     session.log(f"Changelog prepared for version {version}")
