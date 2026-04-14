from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Gate bag pipeline CLI")
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["help", "review-ui", "train", "infer-bag"],
    )
    args = parser.parse_args()
    if args.command == "help":
        parser.print_help()


if __name__ == "__main__":
    main()
