"""The core elements of sqlfluff."""

# flake8: noqa: F401
import tblib.pickling_support  # type: ignore

# Config objects
from sqlfluff.core.config import FluffConfig

# Public classes
from sqlfluff.core.linter import Linter
from sqlfluff.core.parser import Lexer, Parser

# Dialect introspection
from sqlfluff.core.dialects import dialect_selector, dialect_readout

# All of the errors.
from sqlfluff.core.errors import (
    SQLBaseError,
    SQLTemplaterError,
    SQLLexError,
    SQLParseError,
    SQLLintError,
)

# Timing objects
from sqlfluff.core.timing import TimingSummary


# This is for "sqlfluff lint" and "sqlfluff fix" multiprocessing (--parallel)
# support. If an exception (i.e. runtime error) occurs in a worker process, we
# want to return the tracebook to the main process and report it there, as part
# of the normal output. However, anything returned from a multiprocessing.Pool
# worker must be serializable using "pickle". By default, Python traceback
# objects cannot be pickled. The tblib package addresses this limitation; we
# simply need to install it before creating the worker pool. See these links for
# additional context:
# * https://pypi.org/project/tblib/
# * https://stackoverflow.com/questions/6126007/python-getting-a-traceback-from-a-multiprocessing-process
tblib.pickling_support.install()
