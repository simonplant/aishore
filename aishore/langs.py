"""Per-language knowledge: gate-weakening patterns and type declarations. Unknown extensions get none."""
from __future__ import annotations

import ast
import re
from pathlib import Path

JS = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")

CHEATS: dict[tuple[str, ...], list[tuple[str, str]]] = {
    (".py",): [
        (r"pytest\.mark\.(skip|skipif|xfail)|pytest\.(skip|xfail)\(", "skip/xfail added"),
        (r"#\s*type:\s*ignore", "type: ignore added"),
        (r"#\s*pyright:\s*ignore", "pyright: ignore added"),
        (r"#\s*noqa", "noqa added"),
        (r"pragma:\s*no\s*cover", "pragma: no cover added"),
        (r"(approx|isclose)\(.*\b(rel|abs)(_tol)?\s*=", "tolerance set or changed"),
        (r"^\s*assert\s+True\b", "assert True added"),
    ],
    JS: [
        (r"\b(it|test|describe)\.(skip|only|todo)\b|\bx(it|test|describe)\(", "skip/only added"),
        (r"@ts-(ignore|expect-error|nocheck)", "ts suppression added"),
        (r"eslint-disable", "eslint-disable added"),
        (r"(istanbul|c8|v8)\s+ignore", "coverage ignore added"),
        (r"toBeCloseTo\(.*,", "tolerance set or changed"),
        (r"expect\((true|1)\)\.toBe(Truthy)?\(", "assert true added"),
    ],
    (".go",): [
        (r"\bt\.Skip(Now|f)?\(", "skip added"),
        (r"//\s*nolint", "nolint added"),
    ],
    (".rs",): [
        (r"#\[ignore\b", "ignore added"),
        (r"#!?\[allow\(", "allow added"),
    ],
    (".sh", ".bash"): [
        (r"shellcheck\s+disable", "shellcheck disable added"),
    ],
}

TYPE_DECL: dict[tuple[str, ...], str] = {
    JS: r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)",
    (".go",): r"^type\s+(\w+)\s+(?:struct|interface)\b",
    (".rs",): r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:struct|enum|trait)\s+(\w+)",
}


SHEBANG = {"python": ".py", "node": ".js", "bash": ".sh", "sh": ".sh", "zsh": ".sh"}


def ext(path: str, root: Path | None = None) -> str:
    """File extension, or one implied by the shebang of an extensionless script."""
    suffix = Path(path).suffix
    if suffix or root is None or not (root / path).is_file():
        return suffix
    with (root / path).open("rb") as fh:
        first = fh.readline(200).decode(errors="replace")
    if not first.startswith("#!"):
        return ""
    words = first[2:].replace("/", " ").split()
    return next((SHEBANG[w.rstrip("0123456789.")] for w in reversed(words) if w.rstrip("0123456789.") in SHEBANG), "")


def cheats(path: str, root: Path | None = None) -> list[tuple[str, str]]:
    e = ext(path, root)
    return next((v for k, v in CHEATS.items() if e in k), [])


def type_names(path: str, source: str, root: Path | None = None) -> set[str]:
    """Class-like declarations in a source file. Raises SyntaxError for unparsable Python."""
    ext_ = ext(path, root)
    if ext_ == ".py":
        return {n.name for n in ast.walk(ast.parse(source)) if isinstance(n, ast.ClassDef)}
    pat = next((v for k, v in TYPE_DECL.items() if ext_ in k), None)
    return set(re.findall(pat, source, re.M)) if pat else set()
