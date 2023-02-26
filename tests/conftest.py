import pytest
from click.testing import CliRunner
from sqlite_utils import Database


@pytest.fixture
def cli_running() -> CliRunner:
    return CliRunner()


@pytest.fixture
def mock_db() -> Database:
    return Database(memory=True)
