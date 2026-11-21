#!/usr/bin/env python3
"""Ponto de entrada da plataforma acadêmica."""
from app.cli import main
from app.db import init_database
from app.http_server import PanelHandler
from app.permissions import require_role
from app.utils import HTTPError


if __name__ == "__main__":
    main()
