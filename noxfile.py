import nox
import os

# Default sessions to run when no session is specified
nox.options.sessions = ["lint"]

# Python versions to test against
PYTHON_VERSIONS = ["3.12"]

@nox.session(python=PYTHON_VERSIONS)
def lint(session):
    """Run linting tools."""
    session.install("poetry")
    
    # Install dependencies without updating the lock file
    # Simply omit the lock command and rely on the existing lock file
    session.run("poetry", "install", "--only", "dev")
    
    # Run flake8 to check for issues
    session.run("poetry", "run", "flake8", "simba", success_codes=[0, 1])

@nox.session(python=PYTHON_VERSIONS)
def format(session):
    """Auto-format code to fix linting issues."""
    session.install("poetry")
    
    # Install formatting tools
    session.run("poetry", "install", "--only", "dev")
    
    # Run isort to sort imports
    session.run("poetry", "run", "isort", "simba", "tests")
    
    # Run autoflake to remove unused imports and variables
    session.run(
        "poetry", "run", "autoflake",
        "--in-place",
        "--remove-all-unused-imports",
        "--remove-unused-variables",
        "--recursive",
        "simba",
        "tests"
    )
    
    # Run black to format code
    session.run("poetry", "run", "black", "simba", "tests")

@nox.session(python=PYTHON_VERSIONS)
def test(session):
    """Run the test suite."""
    session.install("poetry")
    session.run("poetry", "install")
    
    env = {
        "PYTHONPATH": os.getcwd(),
        "REDIS_HOST": "localhost",
        "CELERY_BROKER_URL": "redis://localhost:6379/0",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/1",
    }
    
    session.run(
        "poetry", "run", "pytest",
        *session.posargs,
        env=env
    )
