from argparse import ArgumentParser
import sys

from types import ModuleType
from typing import Dict, List
from pathlib import Path
import pyperclip as pyperclip

import app.queries as QUERIES_MODULE
from app.queries import QuerySpec

def get_query_specs_by_name(mod: ModuleType) -> Dict[str, QuerySpec]:
    """Return {spec.name: QuerySpec} mapping, so you do not need the variable name."""
    return {
        obj.name: obj
        for _, obj in vars(mod).items()
        if isinstance(obj, QuerySpec)
    }

def _paths_from_spec(spec) -> list[Path]:
    """
    Resolve the ordered list of SQL file paths from a QuerySpec.
    Supports either spec.files() or spec.sql_file_sequence + spec.sql_folder.
    """
    if hasattr(spec, "files") and callable(getattr(spec, "files")):
        return [Path(p) for p in spec.files()]

    seq = getattr(spec, "sql_file_sequence", None)
    base = getattr(spec, "sql_folder", Path("."))
    if seq is None:
        raise ValueError("Spec missing sql_file_sequence or files()")
    return [Path(base) / f for f in seq]

if __name__ == "__main__":
    
    args = ArgumentParser()
    args.add_argument("--query_name", type=str, required=True, help="Name of the query to get sql from")
    parsed = args.parse_args()

    queries_by_name = get_query_specs_by_name(QUERIES_MODULE)

    if parsed.query_name not in queries_by_name:
        raise ValueError(f"Query name '{parsed.query_name}' not found in app.queries")
    spec = queries_by_name[parsed.query_name]

    combined_parts: list[str] = []

    print(f"# SQL files for query '{spec.name}':")
    for sql_file in _paths_from_spec(spec):
        try:
            content = Path(sql_file).read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"-- WARNING: missing {sql_file}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"-- ERROR reading {sql_file}: {e}", file=sys.stderr)
            continue

        header = f"-- {Path(sql_file).name}\n"
        block = header + content.rstrip() + "\n\n"
        print(block, end="")
        combined_parts.append(block)

    combined = "".join(combined_parts)

    pyperclip.copy(combined)
    print(f"# Combined SQL for {spec.name} has been copied to your clipboard.")
