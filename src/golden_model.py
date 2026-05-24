"""Golden reference model for signed integer matrix multiplication."""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

try:
    from .matrix_io import MatrixTest, multiply_matrices, signed_range_for_width
    from .matrix_io import write_expected_file, write_input_file
    from .project_config import DEFAULT_ENV_FILE, load_matrix_config
except ImportError:
    from matrix_io import MatrixTest, multiply_matrices, signed_range_for_width
    from matrix_io import write_expected_file, write_input_file
    from project_config import DEFAULT_ENV_FILE, load_matrix_config


DEFAULT_EXAMPLE_A = [[1, 2], [3, 4]]
DEFAULT_EXAMPLE_B = [[5, 6], [7, 8]]


def parse_args() -> argparse.Namespace:
    env_parser = argparse.ArgumentParser(add_help=False)
    env_parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_FILE,
        help="Configuration file with shared defaults. Default: py_matrix_host/.env",
    )
    env_args, _ = env_parser.parse_known_args()
    config = load_matrix_config(env_args.env_file)

    parser = argparse.ArgumentParser(
        description="Generate signed INT matrix tests and golden C = A x B results.",
        parents=[env_parser],
    )
    parser.add_argument("--n", type=int, default=config.n, help=f"Matrix size N. Default: {config.n}")
    parser.add_argument(
        "--data-width",
        type=int,
        default=config.data_width,
        help=f"Input element width for A/B. Default: {config.data_width}",
    )
    parser.add_argument(
        "--acc-width",
        type=int,
        default=config.acc_width,
        help=f"Accumulator/output width for C. Default: {config.acc_width}",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=config.seed,
        help=f"Random seed. Default: {config.seed}",
    )
    parser.add_argument(
        "--min-value",
        type=int,
        default=config.min_value,
        help=f"Minimum generated A/B value. Default: {config.min_value}",
    )
    parser.add_argument(
        "--max-value",
        type=int,
        default=config.max_value,
        help=f"Maximum generated A/B value. Default: {config.max_value}",
    )
    parser.add_argument(
        "--num-tests",
        type=int,
        default=config.num_tests,
        help=f"Number of test vectors. Default: {config.num_tests}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=config.output_dir,
        help=f"Directory for generated matrix files. Default: {config.output_dir}",
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        default=None,
        help="Optional explicit path for matrix_inputs.txt.",
    )
    parser.add_argument(
        "--expected-file",
        "--output-file",
        dest="expected_file",
        type=Path,
        default=None,
        help="Optional explicit path for matrix_expected.txt.",
    )
    example_group = parser.add_mutually_exclusive_group()
    example_group.add_argument(
        "--example",
        dest="example",
        action="store_true",
        default=config.example,
        help="Use the fixed 2x2 example as TEST 0. Only valid with --n 2.",
    )
    example_group.add_argument(
        "--no-example",
        dest="example",
        action="store_false",
        help="Disable the fixed 2x2 example, even if EXAMPLE=true in .env.",
    )
    parser.add_argument(
        "--print-matrices",
        action="store_true",
        help="Print full matrices after generation. Disabled by default to avoid flooding N=128 runs.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.n <= 0:
        raise ValueError("--n must be greater than zero")
    if args.num_tests <= 0:
        raise ValueError("--num-tests must be greater than zero")
    if args.data_width <= 0:
        raise ValueError("--data-width must be greater than zero")
    if args.acc_width <= 0:
        raise ValueError("--acc-width must be greater than zero")
    if args.min_value > args.max_value:
        raise ValueError("--min-value must be less than or equal to --max-value")
    if args.example and args.n != 2:
        raise ValueError("--example is only valid with --n 2")

    signed_min, signed_max = signed_range_for_width(args.data_width)
    if args.min_value < signed_min or args.max_value > signed_max:
        raise ValueError(
            f"A/B values must fit signed INT{args.data_width}: "
            f"{signed_min}..{signed_max}"
        )


def generate_matrix(
    rng: random.Random, n: int, min_value: int, max_value: int
) -> list[list[int]]:
    return [[rng.randint(min_value, max_value) for _ in range(n)] for _ in range(n)]


def generate_test_vectors(args: argparse.Namespace) -> list[MatrixTest]:
    rng = random.Random(args.seed)
    tests: list[MatrixTest] = []

    for index in range(args.num_tests):
        if args.example and index == 0:
            a = DEFAULT_EXAMPLE_A
            b = DEFAULT_EXAMPLE_B
        else:
            a = generate_matrix(rng, args.n, args.min_value, args.max_value)
            b = generate_matrix(rng, args.n, args.min_value, args.max_value)

        tests.append(MatrixTest(index=index, a=a, b=b, c=multiply_matrices(a, b)))

    return tests


def write_metadata(
    path: Path,
    args: argparse.Namespace,
    *,
    input_file: Path,
    expected_file: Path,
) -> None:
    metadata = {
        "run_id": f"golden_seed_{args.seed}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "N": args.n,
        "DATA_WIDTH": args.data_width,
        "ACC_WIDTH": args.acc_width,
        "num_tests": args.num_tests,
        "seed": args.seed,
        "min_value": args.min_value,
        "max_value": args.max_value,
        "input_type": f"signed_int{args.data_width}",
        "output_type": f"signed_int{args.acc_width}",
        "layout": "row-major",
        "files": {
            "matrix_inputs": str(input_file),
            "matrix_expected": str(expected_file),
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def print_matrix(name: str, matrix: list[list[int]]) -> None:
    print(f"{name} =")
    for row in matrix:
        print("  " + " ".join(f"{value:6d}" for value in row))
    print()


def main() -> None:
    args = parse_args()
    validate_args(args)

    output_dir = args.output_dir
    input_file = args.input_file or (output_dir / "matrix_inputs.txt")
    expected_file = args.expected_file or (output_dir / "matrix_expected.txt")
    metadata_file = output_dir / "metadata.json"

    tests = generate_test_vectors(args)
    write_input_file(
        input_file,
        tests,
        n=args.n,
        data_width=args.data_width,
        acc_width=args.acc_width,
        seed=args.seed,
        min_value=args.min_value,
        max_value=args.max_value,
    )
    write_expected_file(expected_file, tests, n=args.n, acc_width=args.acc_width)
    write_metadata(metadata_file, args, input_file=input_file, expected_file=expected_file)

    if args.print_matrices:
        for test in tests:
            print(f"TEST {test.index}")
            print_matrix("A", test.a or [])
            print_matrix("B", test.b or [])
            print_matrix("C = A x B", test.c or [])

    print(f"Generated {len(tests)} test(s) with N={args.n}, DATA_WIDTH={args.data_width}, ACC_WIDTH={args.acc_width}")
    print(f"Wrote inputs to:   {input_file}")
    print(f"Wrote expected to: {expected_file}")
    print(f"Wrote metadata to: {metadata_file}")


if __name__ == "__main__":
    main()
