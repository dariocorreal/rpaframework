#!/usr/bin/env python3
"""
Robot Framework Libdoc Extended Edition
"""
import argparse
import json
import logging
import os
import re
import sys
import traceback
from contextlib import contextmanager
from pathlib import Path

from robot.errors import DataError
from robot.libdocpkg import LibraryDocumentation, htmlwriter
from robot.utils import normalize, unic

BLACKLIST = ("__pycache__",)
INIT_FILES = ("__init__.robot", "__init__.txt")
EXTENSIONS = (".robot", ".resource", ".txt")


class NullFormatter:
    def html(self, doc, *args, **kwargs):
        return doc


class LibdocExt:
    DOC_FORMATS = ("robot", "text", "html", "rest")

    def __init__(self, config=None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

    def convert_all(self, dir_in, dir_out, format_in, format_out):
        self.logger.info(
            "Searching for libraries in '%s'", ", ".join(str(d) for d in dir_in)
        )
        paths = self.find_keyword_files(dir_in)
        assert paths, "No keyword files found"

        errors = set()
        root = os.path.dirname(os.path.commonprefix(paths))
        for path_in in paths:
            try:
                self.convert_path(
                    path_in=path_in,
                    dir_out=dir_out,
                    format_in=format_in,
                    format_out=format_out,
                    root=root,
                )
            except Exception as err:
                if self.logger.isEnabledFor(logging.DEBUG):
                    traceback.print_exc()
                self.logger.error(str(err).split("\n")[0])
                errors.add(path_in)

        return list(errors)

    def find_keyword_files(self, root):
        paths, stack = set(), [Path(r) for r in root]

        while stack:
            path = stack.pop(0)
            if self.should_ignore(path):
                self.logger.debug("Ignoring file: %s", path)
                continue

            if path.is_dir():
                if self.is_module_library(path):
                    paths.add(path)
                    # Check for RF resources files in module
                    paths |= {
                        file
                        for file in path.glob("**/*")
                        if self.is_resource_file(path)
                    }
                else:
                    for child in path.iterdir():
                        stack.append(child)
            elif self.is_keyword_file(path):
                paths.add(path)

        return list(paths)

    def should_ignore(self, path):
        return path in self.config.get("ignore", []) or path.name in BLACKLIST

    def convert_path(self, path_in, dir_out, format_in, format_out, root=None):
        root = root if root is not None else Path.cwd()

        # Override default docstring format
        if path_in in self.config.get("override_docstring", {}):
            self.logger.debug(f"Overriding docstring format for '{path_in}'")
            format_in = self.config["override_docstring"][path_in]

        # Override default output format
        if path_in in self.config.get("override_format", {}):
            self.logger.debug(f"Overriding output format for '{path_in}'")
            format_out = self.config["override_format"][path_in]

        path_rel = path_in.with_suffix(".json").relative_to(root)
        if self.config.get("collapse", False):
            path_out = Path(dir_out) / Path(
                "_".join(part.lower() for part in path_rel.parts)
            )
        else:
            path_out = Path(dir_out) / path_rel

        path_out.parent.mkdir(parents=True, exist_ok=True)

        self.logger.debug("Converting '%s' to '%s'", path_in, path_out)
        libdoc = LibraryDocumentation(str(path_in), doc_format=format_in.upper())

        # Override name with user-given value
        if self.config.get("title"):
            libdoc.name = self.config["title"]
        # Create module path for library, e.g. RPA.Excel.Files
        elif path_rel.parent != Path("."):
            namespace = str(path_rel.parent).replace(os.sep, ".")
            if self.config.get("namespace"):
                namespace = self.config["namespace"] + "." + namespace
            libdoc.name = "{namespace}.{name}".format(
                namespace=namespace, name=libdoc.name,
            )

        # Convert library scope to RPA format
        if self.config.get("rpa", False):
            scope = normalize(unic(libdoc.scope), ignore="_")
            libdoc.scope = {
                "testcase": "Task",
                "testsuite": "Suite",
                "global": "Global",
            }.get(scope, "")

        # Write final JSON to file
        data = htmlwriter.JsonConverter(NullFormatter()).convert(libdoc)
        with open(path_out, "w") as fd:
            json.dump(data, fd, indent=4)

    @staticmethod
    def is_module_library(path):
        return (path / "__init__.py").is_file() and bool(
            LibraryDocumentation(str(path)).keywords
        )

    @staticmethod
    def is_keyword_file(file):
        return LibdocExt.is_library_file(file) or LibdocExt.is_resource_file(file)

    @staticmethod
    def is_library_file(file):
        return file.suffix == ".py" and file.name != "__init__.py"

    @staticmethod
    def is_resource_file(file):
        if file.name in INIT_FILES or file.suffix not in EXTENSIONS:
            return False

        def contains(data, pattern):
            return bool(re.search(pattern, data, re.MULTILINE | re.IGNORECASE))

        with open(file, "r", encoding="utf-8", errors="ignore") as fd:
            data = fd.read()
            has_keywords = contains(data, r"^\*+\s*((?:User )?Keywords?)")
            has_tasks = contains(data, r"^\*+\s*(Test Cases?|Tasks?)")
            return not has_tasks and has_keywords


class PathOverrideAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if self.nargs is None:
            values = [values]

        args = getattr(namespace, self.dest, {})
        args = args if args is not None else {}

        for value in values:
            try:
                key, val = value.split("=")
                args[Path(key)] = val
            except Exception as exc:
                raise argparse.ArgumentError(self, exc)
        setattr(namespace, self.dest, args)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("path", help="Input file path", type=Path, nargs="+")
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory",
        type=Path,
        default=Path("dist", "libdoc"),
    )
    parser.add_argument(
        "-d",
        "--docstring",
        help="Input docstring format",
        choices=LibdocExt.DOC_FORMATS,
        default="robot",
    )
    parser.add_argument(
        "-f", "--format", help="Output format", choices=CONVERTERS, default="json"
    )
    parser.add_argument(
        "--override-docstring",
        help="Override default docstring format for given files",
        action=PathOverrideAction,
        default={},
        dest="override_docstring",
        metavar="PATH=FORMAT",
    )
    parser.add_argument(
        "--override-format",
        help="Override default output format for given files",
        action=PathOverrideAction,
        default={},
        dest="override_format",
        metavar="PATH=FORMAT",
    )
    parser.add_argument(
        "-i",
        "--ignore",
        help="Ignore given path",
        action="append",
        default=[],
        type=Path,
    )
    parser.add_argument(
        "--ignore-errors", help="Ignore all conversion errors", action="store_true"
    )
    parser.add_argument("--namespace", help="Add custom namespace for library names")
    parser.add_argument(
        "--collapse",
        help="Convert subdirectories to path prefixes",
        action="store_true",
    )
    parser.add_argument("-t", "--title", help="Override title for generated files")
    parser.add_argument("--rpa", help="Use tasks instead of tests", action="store_true")
    parser.add_argument(
        "-v", "--verbose", help="Be more talkative", action="store_true"
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        stream=sys.stdout,
        level=log_level,
        format="%(asctime)s %(levelname)-8s %(message)s",
    )

    app = LibdocExt(
        config={
            "rpa": args.rpa,
            "title": args.title,
            "ignore": args.ignore,
            "override_docstring": args.override_docstring,
            "override_format": args.override_format,
            "namespace": args.namespace,
            "collapse": args.collapse,
        }
    )

    try:
        errors = app.convert_all(
            dir_in=args.path,
            dir_out=args.output,
            format_in=args.docstring,
            format_out=args.format,
        )
    except DataError as err:
        logging.error("Failed to parse library: %s", err)
        sys.exit(1)

    if errors and not args.ignore_errors:
        logging.error(
            "Failed to convert the following libraries:\n%s",
            "\n".join(f"{i}. {path}" for i, path in enumerate(sorted(errors), 1)),
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
