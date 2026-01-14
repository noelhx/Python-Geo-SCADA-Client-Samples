
"""
Unified Geo SCADA script: runs the same code from either environment.

Usage (stand-alone):
  GEOSCADA_HOST=localhost GEOSCADA_PORT=5481 GEOSCADA_USER=user GEOSCADA_PASS=pass python unified_geoscada.py

Usage (server-side in Geo SCADA):
  Geo SCADA calls execute(program_path, program_name, trigger_type, geo_scada_args, connection, ...)

Notes:
- Place your application logic inside run_workflow(connection, context).
- 'context' carries invocation details (program_path, trigger_type, args, etc.) when available.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import os
import sys
import time

# Commonly used imports (available in both environments)
from geoscada.lib.variant import *  # noqa: F401,F403
from geoscada.client.interface_scx import InterfaceScx
from geoscada.client.types import QueryStatus, ImportOptions  # noqa: F401

# Try to import items that are only needed/available outside the server context
try:
    from geoscada.client import ConnectionManager
except Exception:
    ConnectionManager = None  # type: ignore

# Try to import server-side types; if not present, we’re likely running stand-alone
try:
    import geo_scada_types  # Provides ProgramTrigger etc. when running inside Geo SCADA
except Exception:
    geo_scada_types = None  # type: ignore


# ----------------------------
# Core, environment-agnostic logic
# ----------------------------
def run_workflow(connection: InterfaceScx, context: Dict[str, Any]) -> None:
    """
    Put your actual business logic here. This will be called with a valid
    InterfaceScx 'connection' regardless of environment.

    'context' contains optional keys:
      program_path, program_name, trigger_type, geo_scada_args, argv, invoked_from
    """
    # Example placeholder logic: replace with real operations
    # e.g., browsing objects, reading points, performing queries, imports, etc.
    # status: QueryStatus = ...
    # opts: ImportOptions = ...

    # ---- BEGIN USER CODE ----
    print(f"[{datetime.now(timezone.utc).isoformat()}] run_workflow invoked from: {context.get('invoked_from')}")
    # Example: no-op delay
    time.sleep(0.1)
    # ---- END USER CODE ----


# ----------------------------
# Server-side entry point (called by Geo SCADA)
# ----------------------------
def execute(
    program_path: str,
    program_name: str,
    trigger_type: "geo_scada_types.ProgramTrigger",
    geo_scada_args: Dict[str, Any],
    connection: Optional[InterfaceScx],
    *args,
    **kwargs
) -> None:
    """
    Geo SCADA server-side entry point. Geo SCADA passes us an existing 'connection'.
    """
    invoked_from = "server"
    ctx = {
        "program_path": program_path,
        "program_name": program_name,
        "trigger_type": trigger_type,
        "geo_scada_args": geo_scada_args,
        "argv": sys.argv,
        "invoked_from": invoked_from,
    }

    if connection is None:
        raise RuntimeError("Server-side execute() was called without a connection")

    run_workflow(connection, ctx)


# ----------------------------
# Stand-alone entry point (python unified_geoscada.py)
# ----------------------------
def main() -> None:
    """
    Stand-alone launcher. Establishes a ConnectionManager session, logs on, and
    invokes the same run_workflow() as the server path.
    """
    if ConnectionManager is None:
        raise RuntimeError(
            "ConnectionManager is not available. Ensure the 'geoscada.client' package "
            "is installed and accessible for stand-alone execution."
        )

    host = os.getenv("GEOSCADA_HOST", "localhost")
    port = int(os.getenv("GEOSCADA_PORT", "5481"))
    appname = os.getenv("GEOSCADA_APPNAME", "Unified Geo SCADA Script")
    user = os.getenv("GEOSCADA_USER", "")
    passwd = os.getenv("GEOSCADA_PASS", "")

    invoked_from = "stand-alone"
    ctx = {
        "program_path": None,
        "program_name": None,
        "trigger_type": None,
        "geo_scada_args": {},
        "argv": sys.argv,
        "invoked_from": invoked_from,
    }

    # Establish connection and run
    with ConnectionManager(host, port, appname) as connection:
        if not user or not passwd:
            raise RuntimeError(
                "Missing credentials. Set GEOSCADA_USER and GEOSCADA_PASS environment variables."
            )
        connection.log_on(user, passwd)
        run_workflow(connection, ctx)


if __name__ == "__main__":
    # If invoked directly, we run as stand-alone.
    main()
