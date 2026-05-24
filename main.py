"""Entry point for the matrix host tools.

For now this runs the golden model. Later this can grow into the UART host
that sends matrix/matrix_inputs.txt to the FPGA and checks matrix/matrix_outputs.txt.
"""

from __future__ import annotations

try:
    from src.golden_model import main as run_golden_model
except ImportError:
    from .src.golden_model import main as run_golden_model


def main() -> None:
    run_golden_model()


if __name__ == "__main__":
    main()
