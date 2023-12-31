# Librarian

Librarian is a set of tools to manage my books, vinyl records, and video 
games collections.

## Install

I haven't published this to PyPI yet, so you'll need to install it from GitHub
directly:

```console
foo@bar:~$ pip install -e git+https://github.com/myles/librarian.git#egg=librarian
```

## Setup and Configuration

Librarian uses a SQLite database to store all of its data. You can create a new
database by running:

```console
foo@bar:~$ librarian init
```

Librarian will need access to [Discogs][discogs] and [Genius][genius] to 
fetch data about your collections. You'll need to create an account on both
sites and generate an API key for each. Once you have your API keys, you can
configure Librarian by settings the following environment variables or a 
`.env` file:

```dotenv
LIBRARIAN_INTEGRATIONS_DISCOGS_PERSONAL_ACCESS_TOKEN=<your token>
LIBRARIAN_INTEGRATIONS_GENIUS_CLIENT_ACCESS_TOKEN=<your token>
```

## Develop

You'll need to have [Poetry][poetry], a Python packaging and dependency system,
installed. Once installed you can run:

```console
foo@bar:~$ make setup
```

[poetry]: https://python-poetry.org
