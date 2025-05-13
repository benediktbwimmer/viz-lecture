# date_cli_example.py
"""
Simple CLI utility that accepts a --date argument and prints it back to the user.

Examples
--------
$ python date_cli_example.py --date 2025-05-13
You entered: 2025-05-13

$ python date_cli_example.py -d "13/05/2025"
You entered: 2025-05-13

The script uses `argparse` for argument parsing and `python-dateutil`
(install via ``pip install python-dateutil``) for flexible date parsing.
"""


import argparse
from datetime import date
from dateutil import parser


def parse_args() -> argparse.Namespace:
    """Configure and parse command‑line arguments."""
    cli = argparse.ArgumentParser(description="Echo a supplied date.")
    cli.add_argument(
        "-d",
        "--date",
        required=True,
        help="Date to echo back (accepted in many common formats, e.g. 2025‑05‑13 or 13/05/2025)",
    )
    return cli.parse_args()


def main() -> None:
    args = parse_args()

    try:
        parsed: date = parser.parse(args.date).date()
    except (ValueError, OverflowError) as err:
        raise SystemExit(f"Error: Unable to parse '{args.date}' as a date.\n{err}") from err

    print(f"You entered: {parsed.isoformat()}")


if __name__ == "__main__":
    main()
