from importlib.metadata import version

from librarian import cli


def test_cli(cli_runner):
    result = cli_runner.invoke(cli.cli, ["--version"])
    assert result.exit_code == 0
    assert result.output == f"cli, version {version('librarian')}\n"
