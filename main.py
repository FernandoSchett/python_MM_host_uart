"""Entry point for generating matrix inputs, expected outputs, and metadata."""

from __future__ import annotations

try:
    from src.golden_model import main as run_golden_model
except ImportError:
    from .src.golden_model import main as run_golden_model


def main() -> None:
    run_golden_model()


if __name__ == "__main__":
    main()
