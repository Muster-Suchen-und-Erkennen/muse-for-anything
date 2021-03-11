# MUSE for Anything

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub license](https://img.shields.io/github/license/Muster-Suchen-und-Erkennen/muse-for-anything)](https://github.com/Muster-Suchen-und-Erkennen/muse-for-anything/blob/main/LICENSE)
![Python: >= 3.7](https://img.shields.io/badge/python-^3.7-blue)
[![Documentation Status](https://readthedocs.org/projects/muse4anything/badge/?version=latest)](https://muse4anything.readthedocs.io/en/latest/?badge=latest)

The current developer documentation can be found here: <https://muse4anything.readthedocs.io/>.

This package uses Poetry ([documentation](https://python-poetry.org/docs/)).

This package builds on the flask template https://github.com/buehlefs/flask-template

## VSCode

For vscode install the python extension and add the poetry venv path to the folders the python extension searches vor venvs.

On linux:

```json
{
    "python.venvFolders": [
        "~/.cache/pypoetry/virtualenvs"
    ]
}
```

## Development

Run `poetry install` to install dependencies.

Add `.env` file with the following content into the repository root.

```bash
FLASK_APP=muse_for_anything
FLASK_ENV=development # set to production of in production!
```

Run the development server with

```bash
poetry run flask run
```

To compile the frontend run the following commands in the `muse-for-anything-ui` folder.

```bash
npm install # update/install dependencies

# watching build
npm run watch
# normal build
npm run build
```

## Libraries and special files/folders

This package uses the following libraries to build a rest app with a database on top of flask.

 *  Flask ([documentation](https://flask.palletsprojects.com/en/1.1.x/))
 *  Flask-Cors ([documentation](https://flask-cors.readthedocs.io/en/latest/))\
    Used to provide cors headers.\
    Can be configured or removed in `muse_for_anything/__init__.py`.
 *  flask-babel ([documentation](https://flask-babel.tkte.ch), [babel documentation](http://babel.pocoo.org/en/latest/))\
    Used to provide translations.\
    Can be configured in `muse_for_anything/babel.py` and `babel.cfg`.\
    Translation files and Folders: `translations` (and `messages.pot` currently in .gitignore)
 *  Flask-SQLAlchemy ([documentation](https://flask-sqlalchemy.palletsprojects.com/en/2.x/), [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/13/))\
    ORM Mapper for many SQL databases.\
    Models: `muse_for_anything/db/models`\
    Config: `muse_for_anything/util/config/sqlalchemy_config.py` and `muse_for_anything/db/db.py`
 *  Flask-Migrate ([documentation](https://flask-migrate.readthedocs.io/en/latest/), [Alembic documentation](https://alembic.sqlalchemy.org/en/latest/index.html))\
    Provides automatic migration support based on alembic.\
    Migrations: `migrations`
 *  flask-smorest ([documentation](https://flask-smorest.readthedocs.io/en/latest/), [marshmallow documentation](https://marshmallow.readthedocs.io/en/stable/), [apispec documentation](https://apispec.readthedocs.io/en/latest/), [OpenAPI spec](http://spec.openapis.org/oas/v3.0.2))\
    Provides the API code and generates documentation in form of a OpenAPI specification.\
    API: `muse_for_anything/api`\
    API Models: `muse_for_anything/api/v1_api/models`\
    Config: `muse_for_anything/util/config/smorest_config.py` and `muse_for_anything/api/__init__.py`
 *  Flask-JWT-Extended ([documentation](https://flask-jwt-extended.readthedocs.io/en/stable/))\
    Provides authentication with JWT tokens.\
    Config: `muse_for_anything/util/config/smorest_config.py` and `muse_for_anything/api/jwt.py`
 *  Sphinx ([documentation](https://www.sphinx-doc.org/en/master/index.html))\
    The documentation generator.\
    Config: `pyproject.toml` and `docs/conf.py` (toml config input is manually configured in `conf.py`)
 *  sphinxcontrib-redoc ([documantation](https://sphinxcontrib-redoc.readthedocs.io/en/stable/))
    Renders the OpenAPI spec with redoc in sphinx html output.
    Config: `docs/conf.py` (API title is read from spec)
 *  flask-static-digest ([documentation](https://github.com/nickjj/flask-static-digest))\
    For serving the resources of a javascript SPA

Additional files and folders:

 *  `muse-for-anything-ui`\
    Aurelia frontend for the API.
 *  `default.nix` and `shell.nix`\
    For use with the [nix](https://nixos.org) ecosystem.
 *  `pyproject.toml`\
    Poetry package config and config for the [black](https://github.com/psf/black) formatter.
 *  `.flake8`\
    Config for the [flake8](https://flake8.pycqa.org/en/latest/) linter
 *  `.editorconfig`
 *  `tests`\
    Reserved for unit tests, this template has no unit tests.
 *  `instance` (in .gitignore)
 *  `muse_for_anything/templates` and `muse_for_anything/static` (currently empty)\
    Templates and static files of the flask app
 *  `docs`\
    Folder containing a sphinx documentation
 *  `typings`\
    Python typing stubs for libraries that have no type information.
    Mostly generated with the pylance extension of vscode.


Library alternatives or recommendations:

 *  For scripting tasks: invoke ([documentation](http://www.pyinvoke.org)) (is already in `pyproject.toml`)
 *  For hashing passwords: flask-bcrypt ([documentation](https://flask-bcrypt.readthedocs.io/en/latest/))
 

## Babel

```bash
# initial
poetry run pybabel extract -F babel.cfg -o messages.pot .
# create language
poetry run pybabel init -i messages.pot -d translations -l en
# compile translations to be used
poetry run pybabel compile -d translations
# extract updated strings
poetry run pybabel update -i messages.pot -d translations
```

## SQLAlchemy

```bash
# create dev db (this will NOT run migrations!)
poetry run flask create-db
# drop dev db
poetry run flask drop-db
```

This tool uses `select IN` eager loading which is incompatible with SQL Server and SQLite `< 3.15`.

## Migrations

```bash
# create a new migration after changes in the db
poetry run flask db migrate -m "Initial migration."
# upgrade db to the newest migration
poetry run flask db upgrade
# help
poetry run flask db --help
```
