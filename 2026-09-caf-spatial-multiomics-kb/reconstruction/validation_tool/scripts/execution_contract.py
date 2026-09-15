"""Shared execution-evidence contracts used by runner, finalizer, and validator."""

from __future__ import annotations

import ast
import importlib.machinery
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


SEED_LONG_OPTIONS = (
    "--seed",
    "--random-seed",
    "--random_seed",
    "--random-state",
    "--random_state",
    "--rng-seed",
    "--rng_seed",
)

_SEED_LONG_OPTIONS_CASEFOLDED = {option.casefold() for option in SEED_LONG_OPTIONS}
_AMBIGUOUS_SHORT_SEED_OPTIONS = {"-s", "-r"}
_DASH_CONFUSABLES = "\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d"
_DEPENDENCY_NAME_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$"
)
_UNKNOWN_DEPENDENCY_VERSIONS = {
    "",
    "unknown",
    "unreported",
    "missing",
    "not_available",
    "n/a",
    "latest",
    "any",
    "*",
}
_DEPENDENCY_PROBE_MARKER = "__OMICOS_DEPENDENCY_PROBE__="
PYTHON_IMPORT_ENVIRONMENT_VARIABLES = (
    "PYTHONHOME",
    "PYTHONPATH",
    "PYTHONSAFEPATH",
    "PYTHONCASEOK",
    "PYTHONUSERBASE",
    "PYTHONBREAKPOINT",
    "PYTHONWARNINGS",
    "PYTHONSTARTUP",
    "PYTHONINSPECT",
)


def _normalize_option_dashes(value: str) -> str:
    return value.translate(str.maketrans({character: "-" for character in _DASH_CONFUSABLES}))


def _seed_option_kind(token: str) -> tuple[str, str | None]:
    """Classify a token as confirmed, ambiguous, or unrelated.

    Only exact, case-sensitive canonical long options are confirmed. Prefixes,
    case variants, common short aliases, single-dash spellings, and Unicode-dash
    confusables are ambiguous because their target-parser semantics are unknown.
    """

    normalized = _normalize_option_dashes(token)
    raw_name, separator, inline = normalized.partition("=")
    if raw_name in SEED_LONG_OPTIONS and normalized == token:
        return "confirmed", inline if separator else None

    folded = raw_name.casefold()
    canonical_prefix = (
        raw_name.startswith("--")
        and len(raw_name) > 2
        and any(option.casefold().startswith(folded) for option in SEED_LONG_OPTIONS)
    )
    case_variant = folded in _SEED_LONG_OPTIONS_CASEFOLDED
    long_segments = {
        segment
        for segment in re.split(r"[-_]", folded.lstrip("-"))
        if segment
    }
    explicit_seed_like_long = raw_name.startswith("--") and bool(
        long_segments & {"seed", "rng"}
    )
    short_head = raw_name[:2].casefold() if len(raw_name) >= 2 else ""
    short_seed_like = (
        short_head in _AMBIGUOUS_SHORT_SEED_OPTIONS
        and (
            len(raw_name) == 2
            or separator
            or raw_name[2:3].isdigit()
            or raw_name[2:3] in {"+", "-"}
        )
    )
    single_dash_long = raw_name.startswith("-") and not raw_name.startswith("--") and any(
        term in folded for term in ("seed", "random", "rng")
    )
    confusable = normalized != token and any(
        term in folded for term in ("seed", "random", "rng")
    )
    if (
        canonical_prefix
        or case_variant
        or explicit_seed_like_long
        or short_seed_like
        or single_dash_long
        or confusable
    ):
        return "ambiguous", inline if separator else None
    return "unrelated", None


def argv_seed_bindings(
    argv: Any, entrypoint: Any
) -> tuple[list[str], bool]:
    """Return exact entrypoint seed bindings and invalid/ambiguous-option state.

    Parsing begins after the declared entrypoint and stops at the first ``--``
    terminator. A recorded integer seed qualifies only when callers require at
    least one returned binding and all values agree.
    """

    if (
        not isinstance(argv, list)
        or any(not isinstance(value, str) or not value for value in argv)
        or not isinstance(entrypoint, str)
        or not entrypoint
        or entrypoint not in argv
    ):
        return [], True

    values: list[str] = []
    invalid_or_ambiguous = False
    index = argv.index(entrypoint) + 1
    while index < len(argv):
        token = argv[index]
        if token == "--":
            break
        kind, inline = _seed_option_kind(token)
        if kind == "unrelated":
            index += 1
            continue
        if kind == "ambiguous":
            invalid_or_ambiguous = True
            index += 1
            continue

        if "=" in token:
            if inline is None or inline == "":
                invalid_or_ambiguous = True
            else:
                values.append(inline)
            index += 1
            continue
        if index + 1 >= len(argv) or not argv[index + 1] or argv[index + 1] == "--":
            invalid_or_ambiguous = True
            index += 1
            continue
        values.append(argv[index + 1])
        index += 2
    return values, invalid_or_ambiguous


def normalized_dependency_name(value: str) -> str:
    """Return the PEP 503-style identity used to detect ambiguous duplicates."""

    return re.sub(r"[-_.]+", "-", value.strip()).casefold()


def dependency_contract_errors(dependencies: Any) -> list[str]:
    """Validate a concrete, unambiguous dependency/version inventory."""

    if not isinstance(dependencies, list) or not dependencies:
        return ["dependencies must be a non-empty array"]
    errors: list[str] = []
    seen: dict[str, int] = {}
    for index, dependency in enumerate(dependencies):
        label = f"dependencies[{index}]"
        if not isinstance(dependency, dict) or set(dependency) != {"name", "version"}:
            errors.append(f"{label} must contain exactly name and version")
            continue
        name = dependency.get("name")
        version = dependency.get("version")
        if (
            not isinstance(name, str)
            or not _DEPENDENCY_NAME_RE.fullmatch(name.strip())
        ):
            errors.append(f"{label}.name is not a valid distribution name")
            continue
        if (
            not isinstance(version, str)
            or version.strip().casefold() in _UNKNOWN_DEPENDENCY_VERSIONS
            or any(character.isspace() or ord(character) < 32 for character in version)
        ):
            errors.append(f"{label}.version must be a concrete whitespace-free version")
        identity = normalized_dependency_name(name)
        if identity in seen:
            errors.append(
                f"{label}.name duplicates normalized dependency identity from "
                f"dependencies[{seen[identity]}]: {identity}"
            )
        else:
            seen[identity] = index
    return errors


def normalized_python_child_environment(
    environment: dict[str, str] | None = None,
) -> tuple[dict[str, str], list[str]]:
    """Remove variables that can silently change Python import/execution behavior."""

    child_environment = dict(os.environ if environment is None else environment)
    removed: list[str] = []
    for variable in PYTHON_IMPORT_ENVIRONMENT_VARIABLES:
        if variable in child_environment:
            child_environment.pop(variable, None)
            removed.append(variable)
    return child_environment, removed


def _python_probe_prefix(
    command_argv: list[str], entrypoint: str, working_directory: Path,
    environment: dict[str, str],
) -> tuple[list[str], str | None]:
    if entrypoint not in command_argv:
        return [], "command_argv does not contain the declared entrypoint"
    entrypoint_index = command_argv.index(entrypoint)
    prefix = list(command_argv[:entrypoint_index])
    if not prefix:
        return [], "command_argv does not identify a Python launcher"
    launcher = Path(prefix[0])
    if launcher.is_absolute():
        resolved_launcher = launcher.resolve()
    elif any(separator in prefix[0] for separator in ("/", "\\")):
        resolved_launcher = (working_directory / launcher).resolve()
    else:
        located = shutil.which(prefix[0], path=environment.get("PATH"))
        if located is None:
            return [], f"Python launcher is unavailable: {prefix[0]}"
        resolved_launcher = Path(located).resolve()
    if not resolved_launcher.is_file():
        return [], f"Python launcher is unavailable: {prefix[0]}"
    prefix[0] = str(resolved_launcher)
    return prefix, None


def verify_python_dependency_versions(
    command_argv: Any,
    entrypoint: Any,
    dependencies: Any,
    working_directory: Path,
    environment: dict[str, str],
) -> tuple[list[dict[str, str]], dict[str, str], list[str]]:
    """Observe dependency versions through the exact child-Python launcher.

    The probe runs outside the project directory with import-affecting Python
    environment variables removed. Every declared version must be observable
    and exactly equal; the Python interpreter itself is mandatory.
    """

    errors = dependency_contract_errors(dependencies)
    if errors:
        return [], {}, errors
    if (
        not isinstance(command_argv, list)
        or any(not isinstance(token, str) or not token for token in command_argv)
        or not isinstance(entrypoint, str)
        or not entrypoint
    ):
        return [], {}, ["command_argv and entrypoint cannot support a dependency probe"]
    if Path(entrypoint).suffix.casefold() != ".py":
        return [], {}, ["dependency observation is currently supported only for Python entrypoints"]

    dependency_list = list(dependencies)
    identities = {
        normalized_dependency_name(str(item["name"])) for item in dependency_list
    }
    if "python" not in identities:
        return [], {}, ["dependencies must include the executed Python interpreter version"]
    prefix, prefix_error = _python_probe_prefix(
        command_argv, entrypoint, working_directory.resolve(), environment
    )
    if prefix_error:
        return [], {}, [prefix_error]

    names = [str(item["name"]) for item in dependency_list]
    probe_source = (
        "import importlib.metadata as m,json,platform,sys\n"
        "names=json.loads(sys.argv[1])\n"
        "versions={}\n"
        "errors={}\n"
        "for name in names:\n"
        " key=name.casefold().replace('_','-').replace('.','-')\n"
        " try:\n"
        "  versions[name]=platform.python_version() if key=='python' else m.version(name)\n"
        " except Exception as exc:\n"
        "  errors[name]=type(exc).__name__\n"
        "payload={'versions':versions,'errors':errors,'implementation':platform.python_implementation(),"
        "'python_version':platform.python_version()}\n"
        f"print({_DEPENDENCY_PROBE_MARKER!r}+json.dumps(payload,sort_keys=True,separators=(',',':')))\n"
    )
    try:
        with tempfile.TemporaryDirectory(prefix="omicos-dependency-probe-") as probe_dir:
            process = subprocess.run(
                [*prefix, "-c", probe_source, json.dumps(names, separators=(",", ":"))],
                cwd=probe_dir,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                shell=False,
                check=False,
            )
    except (OSError, subprocess.SubprocessError) as exc:
        return [], {}, [f"dependency version probe could not run: {type(exc).__name__}"]
    if process.returncode != 0:
        return [], {}, [
            f"dependency version probe exited with status {process.returncode}"
        ]
    marker_lines = [
        line[len(_DEPENDENCY_PROBE_MARKER) :]
        for line in process.stdout.splitlines()
        if line.startswith(_DEPENDENCY_PROBE_MARKER)
    ]
    if len(marker_lines) != 1:
        return [], {}, ["dependency version probe did not emit one unambiguous result"]
    try:
        payload = json.loads(marker_lines[0])
    except json.JSONDecodeError:
        return [], {}, ["dependency version probe emitted invalid JSON"]
    if not isinstance(payload, dict):
        return [], {}, ["dependency version probe emitted an invalid result"]
    observed = payload.get("versions")
    probe_errors = payload.get("errors")
    if not isinstance(observed, dict) or not isinstance(probe_errors, dict):
        return [], {}, ["dependency version probe omitted required result fields"]

    verified: list[dict[str, str]] = []
    for dependency in dependency_list:
        name = str(dependency["name"])
        declared = str(dependency["version"])
        actual = observed.get(name)
        if name in probe_errors or not isinstance(actual, str) or not actual:
            errors.append(f"dependency version is not observable in the child runtime: {name}")
            continue
        if actual != declared:
            errors.append(
                f"dependency version mismatch for {name}: declared {declared}, observed {actual}"
            )
            continue
        verified.append({"name": name, "version": actual})
    implementation = {
        "implementation": str(payload.get("implementation", "")),
        "python_version": str(payload.get("python_version", "")),
    }
    if not all(implementation.values()):
        errors.append("dependency version probe omitted Python implementation metadata")
    return verified, implementation, errors


def _within_root(root: Path, candidate: Path) -> Path | None:
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


_PYTHON_IMPORT_SUFFIXES = tuple(
    dict.fromkeys(
        (
            *importlib.machinery.EXTENSION_SUFFIXES,
            *importlib.machinery.SOURCE_SUFFIXES,
            *importlib.machinery.BYTECODE_SUFFIXES,
        )
    )
)


def _first_python_import_file(root: Path, stem: Path) -> Path | None:
    for suffix in _PYTHON_IMPORT_SUFFIXES:
        candidate = _within_root(root, stem.parent / f"{stem.name}{suffix}")
        if candidate is not None and candidate.is_file():
            return candidate
    return None


def _local_module_files(root: Path, import_root: Path, module: str) -> list[Path]:
    parts = [part for part in module.split(".") if part]
    if not parts:
        return []
    cursor = import_root
    imported: list[Path] = []
    for index, part in enumerate(parts):
        leaf = index == len(parts) - 1
        package_dir = _within_root(root, cursor / part)
        package_init = (
            _first_python_import_file(root, package_dir / "__init__")
            if package_dir is not None and package_dir.is_dir()
            else None
        )
        module_file = _first_python_import_file(root, cursor / part)
        if package_init is not None:
            imported.append(package_init)
            cursor = package_dir
            continue
        if module_file is not None:
            if not leaf:
                return []
            imported.append(module_file)
            return list(dict.fromkeys(imported))
        if package_dir is not None and package_dir.is_dir():
            cursor = package_dir
            continue
        return []
    return list(dict.fromkeys(imported))


def _dotted_call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def python_local_import_closure(
    project_root: Path, entrypoint: Path
) -> tuple[list[Path], list[str]]:
    """Return a recursive, project-contained Python import closure.

    Dynamic imports and project-root path mutation are explicit gaps. External
    imports are not returned; callers inventory them separately as dependencies.
    """

    root = project_root.resolve()
    start = _within_root(root, entrypoint)
    if start is None or not start.is_file():
        return [], ["entrypoint is unavailable or escapes the project root"]
    if start.suffix.lower() != ".py":
        return [start], [
            "automatic recursive local-code closure is currently supported only for Python entrypoints"
        ]

    pending = [start]
    visited: set[Path] = set()
    gaps: list[str] = []
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        if current.suffix.lower() != ".py":
            gaps.append(
                "compiled or bytecode local module cannot be recursively audited: "
                + current.relative_to(root).as_posix()
            )
            continue
        try:
            tree = ast.parse(current.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, SyntaxError) as exc:
            gaps.append(f"cannot parse local code file {current.relative_to(root).as_posix()}: {exc}")
            continue

        call_aliases: dict[str, str] = {}
        possible_aliases: dict[str, set[str]] = {}

        def remember_alias(name: str, dotted: str) -> bool:
            if not name or not dotted:
                return False
            values = possible_aliases.setdefault(name, set())
            before = len(values)
            values.add(dotted)
            return len(values) != before

        def possible_dotted_names(node: ast.AST) -> set[str]:
            dotted = _dotted_call_name(node)
            if not dotted:
                return set()
            names = {dotted}
            head, separator, tail = dotted.partition(".")
            for replacement in possible_aliases.get(head, set()):
                names.add(replacement + (f".{tail}" if separator else ""))
            return names

        for import_node in ast.walk(tree):
            if isinstance(import_node, ast.Import):
                for alias in import_node.names:
                    local_name = alias.asname or alias.name.split(".", 1)[0]
                    call_aliases[local_name] = alias.name
                    remember_alias(local_name, alias.name)
            elif (
                isinstance(import_node, ast.ImportFrom)
                and import_node.level == 0
                and import_node.module
            ):
                for alias in import_node.names:
                    local_name = alias.asname or alias.name
                    dotted = f"{import_node.module}.{alias.name}"
                    call_aliases[local_name] = dotted
                    remember_alias(local_name, dotted)
        changed = True
        while changed:
            changed = False
            for statement in tree.body:
                if (
                    not isinstance(statement, ast.Assign)
                    or len(statement.targets) != 1
                    or not isinstance(statement.targets[0], ast.Name)
                ):
                    continue
                dotted = _dotted_call_name(statement.value)
                head, separator, tail = dotted.partition(".")
                if head in call_aliases:
                    dotted = call_aliases[head] + (f".{tail}" if separator else "")
                target = statement.targets[0].id
                if dotted and call_aliases.get(target) != dotted:
                    call_aliases[target] = dotted
                    changed = True

        changed = True
        while changed:
            changed = False
            for statement in ast.walk(tree):
                target: ast.Name | None = None
                value: ast.AST | None = None
                if (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                ):
                    target = statement.targets[0]
                    value = statement.value
                elif isinstance(statement, ast.AnnAssign) and isinstance(
                    statement.target, ast.Name
                ):
                    target = statement.target
                    value = statement.value
                if target is None or value is None:
                    continue
                for dotted in possible_dotted_names(value):
                    changed = remember_alias(target.id, dotted) or changed

        plugin_factories = {
            "importlib.metadata.EntryPoint",
            "importlib.metadata.entry_points",
            "pkg_resources.EntryPoint.parse",
            "pkg_resources.iter_entry_points",
        }
        unpickler_factories = {
            "pickle.Unpickler",
            "_pickle.Unpickler",
            "dill.Unpickler",
        }
        plugin_objects: set[str] = set()
        unpickler_objects: set[str] = set()
        plugin_load_callables: set[str] = set()
        unpickler_load_callables: set[str] = set()

        def factory_result(
            expression: ast.AST, factories: set[str], object_aliases: set[str]
        ) -> bool:
            if isinstance(expression, ast.Name):
                return expression.id in object_aliases
            if isinstance(expression, ast.Subscript):
                return factory_result(expression.value, factories, object_aliases)
            if isinstance(expression, ast.Call):
                names = possible_dotted_names(expression.func)
                if names & factories:
                    return True
                if isinstance(expression.func, ast.Attribute) and expression.func.attr in {
                    "select",
                    "get",
                    "values",
                }:
                    return factory_result(
                        expression.func.value, factories, object_aliases
                    )
                if names & {"list", "tuple", "iter", "next", "sorted", "reversed"}:
                    return any(
                        factory_result(argument, factories, object_aliases)
                        for argument in expression.args
                    )
            return False

        changed = True
        while changed:
            changed = False
            for statement in ast.walk(tree):
                target: ast.Name | None = None
                value: ast.AST | None = None
                if (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                ):
                    target = statement.targets[0]
                    value = statement.value
                elif isinstance(statement, ast.AnnAssign) and isinstance(
                    statement.target, ast.Name
                ):
                    target = statement.target
                    value = statement.value
                elif isinstance(statement, (ast.For, ast.AsyncFor)) and isinstance(
                    statement.target, ast.Name
                ):
                    target = statement.target
                    value = statement.iter
                elif isinstance(statement, ast.comprehension) and isinstance(
                    statement.target, ast.Name
                ):
                    target = statement.target
                    value = statement.iter
                if target is None or value is None:
                    continue
                if factory_result(value, plugin_factories, plugin_objects):
                    before = len(plugin_objects)
                    plugin_objects.add(target.id)
                    changed = changed or len(plugin_objects) != before
                if factory_result(value, unpickler_factories, unpickler_objects):
                    before = len(unpickler_objects)
                    unpickler_objects.add(target.id)
                    changed = changed or len(unpickler_objects) != before
                if (
                    isinstance(value, ast.Attribute)
                    and value.attr == "load"
                    and factory_result(value.value, plugin_factories, plugin_objects)
                ) or (
                    isinstance(value, ast.Name)
                    and value.id in plugin_load_callables
                ):
                    before = len(plugin_load_callables)
                    plugin_load_callables.add(target.id)
                    changed = changed or len(plugin_load_callables) != before
                if (
                    isinstance(value, ast.Attribute)
                    and value.attr == "load"
                    and factory_result(value.value, unpickler_factories, unpickler_objects)
                ) or (
                    isinstance(value, ast.Name)
                    and value.id in unpickler_load_callables
                ):
                    before = len(unpickler_load_callables)
                    unpickler_load_callables.add(target.id)
                    changed = changed or len(unpickler_load_callables) != before

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = _dotted_call_name(node.func)
                head, separator, tail = call_name.partition(".")
                if head in call_aliases:
                    call_name = call_aliases[head] + (f".{tail}" if separator else "")
                call_names = possible_dotted_names(node.func)
                if call_name:
                    call_names.add(call_name)
                plugin_loader = (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "load"
                    and factory_result(
                        node.func.value, plugin_factories, plugin_objects
                    )
                ) or (
                    isinstance(node.func, ast.Name)
                    and node.func.id in plugin_load_callables
                )
                unpickler_loader = (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "load"
                    and factory_result(
                        node.func.value, unpickler_factories, unpickler_objects
                    )
                ) or (
                    isinstance(node.func, ast.Name)
                    and node.func.id in unpickler_load_callables
                )
                dynamic_import = (
                    any(
                        name == "__import__" or name.endswith(".__import__")
                        for name in call_names
                    )
                    or any(name.endswith(".import_module") for name in call_names)
                    or bool(
                        call_names
                        & {
                            "pkgutil.resolve_name",
                            "pydoc.locate",
                            "unittest.mock.patch",
                            "importlib.util.find_spec",
                            "importlib.resources.files",
                            "importlib.resources.open_binary",
                            "importlib.resources.open_text",
                            "importlib.resources.read_binary",
                            "importlib.resources.read_text",
                        }
                    )
                )
                dynamic_code_loader = (
                    bool(
                        call_names
                        & {
                        "runpy.run_path",
                        "runpy.run_module",
                        "importlib.util.spec_from_file_location",
                        "exec",
                        "eval",
                        "compile",
                        "builtins.exec",
                        "builtins.eval",
                        "builtins.compile",
                        "ctypes.CDLL",
                        "ctypes.PyDLL",
                        "ctypes.WinDLL",
                        "ctypes.OleDLL",
                        "ctypes.cdll.LoadLibrary",
                        "ctypes.pydll.LoadLibrary",
                        "ctypes.windll.LoadLibrary",
                        "ctypes.oledll.LoadLibrary",
                        "numpy.ctypeslib.load_library",
                        "torch.ops.load_library",
                        "tensorflow.load_op_library",
                        "llvmlite.binding.load_library_permanently",
                    }
                    )
                    or any(name.endswith(".SourceFileLoader") for name in call_names)
                    or any(name.endswith(".SourcelessFileLoader") for name in call_names)
                    or any(name in {"load_module", "exec_module"} for name in call_names)
                    or any(name.endswith(".load_module") for name in call_names)
                    or any(name.endswith(".exec_module") for name in call_names)
                    or any(name.endswith(".dlopen") for name in call_names)
                    or bool(
                        call_names
                        & {
                            "pickle.load",
                            "pickle.loads",
                            "_pickle.load",
                            "_pickle.loads",
                            "dill.load",
                            "dill.loads",
                            "cloudpickle.load",
                            "cloudpickle.loads",
                            "joblib.load",
                            "sklearn.externals.joblib.load",
                            "torch.load",
                            "pandas.read_pickle",
                            "shelve.open",
                            "yaml.load",
                            "skops.io.load",
                        }
                    )
                    or plugin_loader
                    or unpickler_loader
                )
                subprocess_loader = bool(
                    call_names
                    & {
                        "os.system",
                        "os.popen",
                        "subprocess.run",
                        "subprocess.Popen",
                        "subprocess.call",
                        "subprocess.check_call",
                        "subprocess.check_output",
                    }
                ) or any(
                    name.startswith("os.exec") or name.startswith("os.spawn")
                    for name in call_names
                )
                getattr_loader = (
                    call_name == "getattr"
                    and len(node.args) >= 2
                    and isinstance(node.args[1], ast.Constant)
                    and isinstance(node.args[1].value, str)
                    and (
                        node.args[1].value
                        in {
                        "run_path",
                        "run_module",
                        "import_module",
                        "spec_from_file_location",
                        "SourceFileLoader",
                        "SourcelessFileLoader",
                        "resolve_name",
                        "locate",
                        "find_spec",
                        "CDLL",
                        "PyDLL",
                        "WinDLL",
                        "OleDLL",
                        "LoadLibrary",
                        "load_library",
                        "load_module",
                        "exec_module",
                        "dlopen",
                        "load",
                        "loads",
                        "exec",
                        "eval",
                        "compile",
                        "__import__",
                        "system",
                        "popen",
                    }
                        or node.args[1].value.startswith("exec")
                        or node.args[1].value.startswith("spawn")
                    )
                )
                partial_loader = (
                    call_name in {"functools.partial", "partial"}
                    and bool(node.args)
                    and any(
                        any(term in name for name in possible_dotted_names(node.args[0]))
                        for term in (
                            "run_path",
                            "run_module",
                            "import_module",
                            "spec_from_file_location",
                            "SourceFileLoader",
                            "SourcelessFileLoader",
                            "load_module",
                            "exec_module",
                            "CDLL",
                            "PyDLL",
                            "WinDLL",
                            "OleDLL",
                            "LoadLibrary",
                            "load_library",
                            "dlopen",
                        )
                    )
                )
                numpy_pickle_loader = (
                    bool(call_names & {"numpy.load"})
                    and any(
                        keyword.arg == "allow_pickle"
                        and isinstance(keyword.value, ast.Constant)
                        and keyword.value.value is True
                        for keyword in node.keywords
                    )
                )
                import_state_bases = {
                    "sys.path",
                    "sys.meta_path",
                    "sys.path_hooks",
                    "sys.path_importer_cache",
                    "sys.modules",
                }
                mutating_methods = {
                    "append",
                    "extend",
                    "insert",
                    "remove",
                    "pop",
                    "clear",
                    "sort",
                    "reverse",
                    "update",
                    "setdefault",
                    "__setitem__",
                    "__delitem__",
                }
                path_mutation = any(
                    name == "site.addsitedir"
                    or any(
                        name == f"{base}.{method}"
                        for base in import_state_bases
                        for method in mutating_methods
                    )
                    or any(
                        name.endswith(f".__path__.{method}")
                        or name == f"__path__.{method}"
                        for method in mutating_methods
                    )
                    for name in call_names
                )
                setattr_import_state = (
                    bool(call_names & {"setattr", "builtins.setattr", "delattr", "builtins.delattr"})
                    and len(node.args) >= 2
                    and isinstance(node.args[1], ast.Constant)
                    and isinstance(node.args[1].value, str)
                    and (
                        node.args[1].value
                        in {"path", "meta_path", "path_hooks", "path_importer_cache", "modules", "__import__", "__path__"}
                    )
                )
                if dynamic_import:
                    gaps.append(
                        f"dynamic import in {current.relative_to(root).as_posix()} line {node.lineno}"
                    )
                if dynamic_code_loader or numpy_pickle_loader:
                    gaps.append(
                        f"dynamic code loader {call_name} in {current.relative_to(root).as_posix()} line {node.lineno}"
                    )
                if getattr_loader or partial_loader:
                    gaps.append(
                        f"indirect dynamic code loader in {current.relative_to(root).as_posix()} line {node.lineno}"
                    )
                if subprocess_loader:
                    gaps.append(
                        f"subprocess code path {call_name} in {current.relative_to(root).as_posix()} line {node.lineno}"
                    )
                if path_mutation or setattr_import_state:
                    gaps.append(
                        f"Python import-state mutation in {current.relative_to(root).as_posix()} line {node.lineno}"
                    )
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete)):
                if isinstance(node, ast.Assign):
                    targets = node.targets
                elif isinstance(node, ast.Delete):
                    targets = node.targets
                else:
                    targets = [node.target]
                for target in targets:
                    target_base = target.value if isinstance(target, ast.Subscript) else target
                    target_names = possible_dotted_names(target_base)
                    if any(
                        name
                        in {
                            "sys.path",
                            "sys.meta_path",
                            "sys.path_hooks",
                            "sys.path_importer_cache",
                            "sys.modules",
                            "builtins.__import__",
                            "__builtins__.__import__",
                            "__path__",
                        }
                        or name.endswith(".__path__")
                        for name in target_names
                    ):
                        gaps.append(
                            f"Python import-state assignment in {current.relative_to(root).as_posix()} line {node.lineno}"
                        )
                        break
            if (
                isinstance(node, ast.Subscript)
                and isinstance(node.slice, ast.Constant)
                and isinstance(node.slice.value, str)
                and node.slice.value in {"exec", "eval", "compile", "__import__"}
                and _dotted_call_name(node.value)
                in {"__builtins__", "builtins.__dict__"}
            ):
                gaps.append(
                    f"indirect builtin code loader in {current.relative_to(root).as_posix()} line {node.lineno}"
                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pending.extend(_local_module_files(root, start.parent, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = current.parent
                    for _ in range(max(0, node.level - 1)):
                        base = base.parent
                    module = node.module or ""
                    alias_base = base
                    if module:
                        relative_target = _within_root(
                            root, base.joinpath(*module.split("."))
                        )
                        if relative_target is not None:
                            alias_base = relative_target
                            module_file = relative_target.with_suffix(".py")
                            package_file = relative_target / "__init__.py"
                            if module_file.is_file():
                                pending.append(module_file.resolve())
                            elif package_file.is_file():
                                pending.append(package_file.resolve())
                    for alias in node.names:
                        relative_alias = _within_root(root, alias_base / alias.name)
                        if relative_alias is not None:
                            alias_file = relative_alias.with_suffix(".py")
                            alias_package = relative_alias / "__init__.py"
                            if alias_file.is_file():
                                pending.append(alias_file.resolve())
                            elif alias_package.is_file():
                                pending.append(alias_package.resolve())
                elif node.module:
                    pending.extend(_local_module_files(root, start.parent, node.module))
                    for alias in node.names:
                        pending.extend(
                            _local_module_files(
                                root, start.parent, f"{node.module}.{alias.name}"
                            )
                        )
    return sorted(visited), list(dict.fromkeys(gaps))
