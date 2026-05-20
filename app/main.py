"""Module entrypoint for `python -m app.main`."""

from app.entrypoint.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
