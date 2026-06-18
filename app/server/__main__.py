"""Entry point for LearnAgent web server."""

import click
import uvicorn


@click.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to listen on")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the LearnAgent web server."""
    uvicorn.run(
        "app.server.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


if __name__ == "__main__":
    serve()
