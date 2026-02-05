"""Command-line interface for the OSRS backend."""

import click
import uvicorn


@click.group()
def main():
    """OSRS Backend - Unified HTTP API and ML inference server."""
    pass


@main.command()
@click.option("--http-host", default=None, help="HTTP server host")
@click.option("--http-port", default=None, type=int, help="HTTP server port")
@click.option("--tcp-host", default=None, help="TCP server host")
@click.option("--tcp-port", default=None, type=int, help="TCP server port")
@click.option("--http-only", is_flag=True, help="Only start HTTP server")
@click.option("--tcp-only", is_flag=True, help="Only start TCP server")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve(http_host, http_port, tcp_host, tcp_port, http_only, tcp_only, reload):
    """Start the unified server (HTTP + TCP)."""
    from osrs_backend.config import get_settings
    from osrs_backend.utils.logging import setup_logging

    setup_logging()
    settings = get_settings()

    # Override settings if provided
    host = http_host or settings.http_host
    port = http_port or settings.http_port

    if tcp_only:
        import asyncio
        from osrs_backend.main import _run_tcp_only

        click.echo(f"Starting TCP-only server on {tcp_host or settings.tcp_host}:{tcp_port or settings.tcp_port}")
        asyncio.run(_run_tcp_only())
    else:
        click.echo(f"Starting unified server...")
        click.echo(f"  HTTP API: http://{host}:{port}")
        if not http_only:
            click.echo(f"  TCP Inference: {tcp_host or settings.tcp_host}:{tcp_port or settings.tcp_port}")

        uvicorn.run(
            "osrs_backend.main:app",
            host=host,
            port=port,
            reload=reload,
        )


@main.command()
def worker():
    """Start the ARQ background worker."""
    import subprocess
    import sys

    click.echo("Starting ARQ worker...")
    subprocess.run(
        [sys.executable, "-m", "arq", "osrs_backend.workers.arq_worker.WorkerSettings"],
        check=True,
    )


@main.command()
@click.pass_context
@click.argument("args", nargs=-1)
def train(ctx, args):
    """Start ML training (delegates to pvp-ml)."""
    try:
        from pvp_ml.run_train_job import main as train_main

        click.echo("Starting training...")
        train_main(list(args))
    except ImportError:
        click.echo("Error: pvp_ml not installed. Install it with: pip install -e ../pvp-ml")
        ctx.exit(1)


@main.command("serve-api")
@click.pass_context
@click.argument("args", nargs=-1)
def serve_api(ctx, args):
    """Start standalone ML API server (legacy, use 'serve' instead)."""
    try:
        from pvp_ml.api import main as api_main

        click.echo("Starting legacy ML API server...")
        api_main(list(args))
    except ImportError:
        click.echo("Error: pvp_ml not installed. Install it with: pip install -e ../pvp-ml")
        ctx.exit(1)


@main.command("eval")
@click.pass_context
@click.argument("args", nargs=-1)
def evaluate(ctx, args):
    """Evaluate a trained model (delegates to pvp-ml)."""
    try:
        from pvp_ml.evaluate import main as eval_main

        click.echo("Starting evaluation...")
        eval_main(list(args))
    except ImportError:
        click.echo("Error: pvp_ml not installed. Install it with: pip install -e ../pvp-ml")
        ctx.exit(1)


if __name__ == "__main__":
    main()
