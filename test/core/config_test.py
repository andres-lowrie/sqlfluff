"""Tests for the configuration routines."""

import os

from sqlfluff.core.config import ConfigLoader, nested_combine, dict_diff
from sqlfluff.core import Linter, FluffConfig

from pathlib import Path
from unittest.mock import patch, call
import appdirs
import pytest


config_a = {
    "core": {"testing_val": "foobar", "testing_int": 4},
    "bar": {"foo": "barbar"},
}


@pytest.fixture
def mock_xdg_home(monkeypatch):
    """Sets the XDG_CONFIG_HOME variable."""
    monkeypatch.setenv("XDG_CONFIG_HOME", "~/.config/my/special/path")


def test__config__nested_combine():
    """Test combination of two config dicts."""
    a = {"a": {"b": {"c": 123, "d": 456}}}
    b = {"b": {"b": {"c": 123, "d": 456}}}
    c = {"a": {"b": {"c": 234, "e": 456}}}
    r = nested_combine(a, b, c)
    assert r == {
        "a": {"b": {"c": 234, "e": 456, "d": 456}},
        "b": {"b": {"c": 123, "d": 456}},
    }


def test__config__dict_diff():
    """Test diffs between two config dicts."""
    a = {"a": {"b": {"c": 123, "d": 456, "f": 6}}}
    b = {"b": {"b": {"c": 123, "d": 456}}}
    c = {"a": {"b": {"c": 234, "e": 456, "f": 6}}}
    assert dict_diff(a, b) == a
    assert dict_diff(a, c) == {"a": {"b": {"c": 123, "d": 456}}}
    assert dict_diff(c, a) == {"a": {"b": {"c": 234, "e": 456}}}


def test__config__load_file_dir():
    """Test loading config from a directory path."""
    c = ConfigLoader()
    cfg = c.load_config_at_path(
        os.path.join("test", "fixtures", "config", "inheritance_a")
    )
    assert cfg == config_a


def test__config__load_file_f():
    """Test loading config from a file path."""
    c = ConfigLoader()
    cfg = c.load_config_at_path(
        os.path.join("test", "fixtures", "config", "inheritance_a", "testing.sql")
    )
    assert cfg == config_a


def test__config__load_nested():
    """Test nested overwrite and order of precedence of config files in the same directory."""
    c = ConfigLoader()
    cfg = c.load_config_up_to_path(
        os.path.join(
            "test", "fixtures", "config", "inheritance_a", "nested", "blah.sql"
        )
    )
    assert cfg == {
        "core": {"testing_val": "foobar", "testing_int": 1, "testing_bar": 7.698},
        "bar": {"foo": "foobar"},
        "fnarr": {"fnarr": {"foo": "foobar"}},
    }


def test__config__load_toml():
    """Test loading config from a pyproject.toml file."""
    c = ConfigLoader()
    cfg = c.load_default_config_file(
        os.path.join("test", "fixtures", "config", "toml"),
        "pyproject.toml",
    )
    assert cfg == {
        "core": {
            "testing_int": 5,
            "testing_bar": 7.698,
            "testing_bool": False,
            "testing_arr": ["a", "b", "c"],
            "testing_inline_table": {"x": 1},
        },
        "bar": {"foo": "foobar"},
        "fnarr": {"fnarr": {"foo": "foobar"}},
    }


def test__config__iter_config_paths_right_order():
    """Test that config paths are fetched ordered by priority."""
    c = ConfigLoader()
    cfg_paths = c.iter_config_locations_up_to_path(
        os.path.join(
            "test", "fixtures", "config", "inheritance_a", "nested", "blah.sql"
        ),
        working_path="test/fixtures",
    )
    assert list(cfg_paths) == [
        str(Path(p).resolve())
        for p in [
            "test/fixtures",
            "test/fixtures/config",
            "test/fixtures/config/inheritance_a",
            "test/fixtures/config/inheritance_a/nested",
        ]
    ]


def test__config__find_sqlfluffignore_in_same_directory():
    """Test find ignore file in the same directory as sql file."""
    ignore_files = ConfigLoader.find_ignore_config_files(
        path="test/fixtures/linter/sqlfluffignore/path_b/query_b.sql",
        working_path="test/fixtures/linter/sqlfluffignore/",
    )
    assert ignore_files == {
        os.path.abspath("test/fixtures/linter/sqlfluffignore/path_b/.sqlfluffignore"),
        os.path.abspath("test/fixtures/linter/sqlfluffignore/.sqlfluffignore"),
    }


def test__config__nested_config_tests():
    """Test linting with overriden config in nested paths.

    This looks like a linter test but it's actually a config
    test.
    """
    lntr = Linter(config=FluffConfig(overrides=dict(exclude_rules="L002")))
    lnt = lntr.lint_path("test/fixtures/config/inheritance_b")
    violations = lnt.check_tuples(by_path=True)
    for k in violations:
        if k.endswith("nested\\example.sql"):
            assert ("L003", 1, 4) in violations[k]
            assert ("L009", 1, 12) in violations[k]
            assert "L002" not in [c[0] for c in violations[k]]
        elif k.endswith("inheritance_b\\example.sql"):
            assert ("L003", 1, 4) in violations[k]
            assert "L002" not in [c[0] for c in violations[k]]
            assert "L009" not in [c[0] for c in violations[k]]


@patch("os.path.exists")
@patch("os.listdir")
def test__config__load_user_appdir_config(
    mock_listdir, mock_path_exists, mock_xdg_home
):
    """Test loading config from user appdir."""
    xdg_config_path = os.environ.get("XDG_CONFIG_HOME") + "/sqlfluff"

    def path_exists(x):
        if x == os.path.expanduser("~/.config/sqlfluff"):
            return False
        if x == xdg_config_path:
            return False
        else:
            return True

    mock_path_exists.side_effect = path_exists

    c = ConfigLoader()

    with patch.object(appdirs, attribute="system", new="darwin"):
        resolved_path = c._get_user_config_dir_path()
        c.load_user_appdir_config()
    assert resolved_path == os.path.expanduser("~/Library/Application Support/sqlfluff")

    mock_path_exists.assert_has_calls(
        [
            call(xdg_config_path),
            call(os.path.expanduser("~/Library/Application Support/sqlfluff")),
        ]
    )
