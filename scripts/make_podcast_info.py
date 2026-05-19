#!/usr/bin/env python3
"""Write a copy-friendly title and description TXT for podcast outputs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate podcast title/description TXT.")
    parser.add_argument("--title", required=True, help="Podcast title.")
    parser.add_argument("--description", required=True, help="Podcast description.")
    parser.add_argument("--output", required=True, help="Output txt path.")
    args = parser.parse_args()

    title = clean(args.title)
    description = clean(args.description)
    if not title:
        raise SystemExit("title cannot be empty")
    if not description:
        raise SystemExit("description cannot be empty")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        f"标题：\n{title}\n\n简介：\n{description}\n",
        encoding="utf-8",
        newline="\n",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
