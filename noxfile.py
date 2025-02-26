import nox

nox.options.sessions = ["tests", "lint", "type_check"]
nox.options.reuse_existing_virtualenvs = True

PYTHON_VERSIONS = ["3.10", "3.11", "3.12"]

@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
def tests(session):
    """
    Install dependencies via Poetry and run the test suite with pytest.
    """
    # Install Poetry in this session environment
    session.run("pip", "install", "poetry", external=True)
    # Use Poetry to install all dependencies (including dev/test)
    session.run("poetry", "install", "--no-root", external=True)
    # Run tests
    session.run("pytest", external=True)

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

@nox.session(venv_backend="uv" ,python=PYTHON_VERSIONS )
def release(session):
    """
    Prepare a release: update version, create tag, build and publish.
    """
    session.install("poetry", "twine", "build")
    # Ensure clean working directory
    session.run("git", "diff", "--exit-code", external=True, success_codes=[0, 1])
    # Build package
    session.run("poetry", "build", external=True)
    # Publish to PyPI (will prompt for credentials)
    if session.interactive:
        session.run("twine", "upload", "dist/*", external=True)
