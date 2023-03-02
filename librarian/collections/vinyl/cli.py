import click

from ...integrations.discogs import DiscogsClient


@click.group()
def cli():
    """Inventory the library's vinyl record collection."""


@cli.command(name="add")
@click.option(
    "--release-id",
    prompt="Discogs release ID",
    prompt_required=True,
)
def add_vinyl(release_id: int):
    """Add a vinyl record to the library's collection."""
    client = DiscogsClient()
    release = client.get_release(release_id=release_id)
    artists = [
        client.get_artist(artist_id=artist.id) for artist in release.artists
    ]

    click.echo(release)
    for artist in artists:
        click.echo(artist)
