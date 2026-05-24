"""Single command entry point for the Python matrix host."""

from __future__ import annotations

import sys

from src.golden_model import main as run_golden_model
from src.host_uart import main as run_uart_host


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "uart":
        sys.argv.pop(1)
        run_uart_host()
        return

    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        sys.argv.pop(1)

    run_golden_model()


if __name__ == "__main__":
    main()
