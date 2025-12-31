"""CLI for Simba."""

import argparse
import uvicorn


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Simba - Customer Service Assistant",
        prog="simba",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Server command
    server_parser = subparsers.add_parser("server", help="Run the API server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    server_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    if args.command == "server":
        uvicorn.run(
            "simba.api.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
