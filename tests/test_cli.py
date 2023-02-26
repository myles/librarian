from importlib.metadata import version

from librarian import cli


def test_cli(cli_running):
    result = cli_running.invoke(cli.cli, ["--version"])
    assert result.exit_code == 0
    assert result.output == f"cli, version {version('librarian')}\n"
