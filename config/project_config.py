"""Shared project configuration loaded from a .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class MatrixConfig:
    n: int
    num_tests: int
    data_width: int
    acc_width: int
    seed: int
    min_value: int
    max_value: int
    output_dir: Path
    input_file: Path
    expected_file: Path
    example: bool


def load_env_file(path: Path = DEFAULT_ENV_FILE) -> None:
    if not path.exists():
        return

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .env line {line_number}: expected KEY=VALUE")

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")

        if not key:
            raise ValueError(f"Invalid .env line {line_number}: empty key")

        os.environ[key] = value


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    raise ValueError(f"{name} must be a boolean, got {value!r}")


def env_path(name: str, default: str | Path, base_dir: Path) -> Path:
    path = Path(os.environ.get(name, str(default)))
    if path.is_absolute():
        return path
    return base_dir / path


def signed_range_for_width(width: int) -> tuple[int, int]:
    if width <= 0:
        raise ValueError("DATA_WIDTH must be greater than zero")
    return -(2 ** (width - 1)), (2 ** (width - 1)) - 1


def load_matrix_config(env_file: Path = DEFAULT_ENV_FILE) -> MatrixConfig:
    env_file = Path(env_file)
    load_env_file(env_file)

    base_dir = PROJECT_ROOT
    data_width = env_int("DATA_WIDTH", 8)
    acc_width = env_int("ACC_WIDTH", 32)
    signed_min, signed_max = signed_range_for_width(data_width)
    output_dir = env_path("MATRIX_OUTPUT_DIR", "matrix", base_dir)

    # ROWS_A is accepted only as a compatibility fallback for older local env files.
    n = env_int("N", env_int("ROWS_A", 128))

    return MatrixConfig(
        n=n,
        num_tests=env_int("NUM_TESTS", 1),
        data_width=data_width,
        acc_width=acc_width,
        seed=env_int("SEED", 123),
        min_value=env_int("MIN_VALUE", signed_min),
        max_value=env_int("MAX_VALUE", signed_max),
        output_dir=output_dir,
        input_file=env_path("MATRIX_INPUT_FILE", output_dir / "matrix_inputs.txt", base_dir),
        expected_file=env_path(
            "MATRIX_EXPECTED_FILE",
            os.environ.get("MATRIX_OUTPUT_FILE", str(output_dir / "matrix_expected.txt")),
            base_dir,
        ),
        example=env_bool("EXAMPLE", False),
    )
