from __future__ import annotations

import argparse

from app.services.youtube.client import resolve_channel_by_handle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("handle")
    ns = parser.parse_args()
    result = resolve_channel_by_handle(ns.handle)
    print(result)


if __name__ == "__main__":
    main()
