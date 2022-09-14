from os import environ
from os import execvpe as replace_process
from os import urandom
from pathlib import Path
from re import match
from shlex import join
from typing import List

from dotenv import load_dotenv
from invoke import task
from invoke.runners import Result

load_dotenv(".flaskenv")
load_dotenv(".env")

MODULE_NAME = "muse_for_anything"


# a list of allowed licenses, dependencies with other licenses will trigger an error in the list-licenses command
ALLOWED_LICENSES = [
    "3-Clause BSD License",
    "Apache 2.0",
    "Apache License, Version 2.0",
    "Apache Software License",
    "BSD License",
    "BSD",
    "GNU Lesser General Public License v2 or later (LGPLv2+)",
    "GNU Library or Lesser General Public License (LGPL)",
    "GPLv3",
    "MIT License",
    "MIT",
    "Mozilla Public License 2.0 (MPL 2.0)",
    "new BSD",
    "Python Software Foundation License",
]


@task
def doc(c, format_="html", all_=False, color=True):
    """Build the documentation.

    Args:
        c (Context): task context
        format_ (str, optional): the format to build. Defaults to "html".
        all (bool, optional): build all files new. Defaults to False.
        color (bool, optional): color output. Defaults to True.
    """
    cmd = ["sphinx-build", "-b", format_]
    if all_:
        cmd.append("-a")
    if color:
        cmd.append("--color")
    else:
        cmd.append("--no-color")
    cmd += [".", "_build"]
    with c.cd(str(Path("./docs"))):
        c.run(join(cmd), echo=True)


@task
def browse_doc(c):
    """Open the documentation in the browser.

    Args:
        c (Context): task context
    """
    index_path = Path("./docs/_build/html/index.html")
    if not index_path.exists():
        doc(c)

    print(f"Open: file://{index_path.resolve()}")
    import webbrowser

    webbrowser.open_new_tab(str(index_path.resolve()))


@task
def doc_index(c, filter_=""):
    """Search the index of referencable sphinx targets in the documentation.

    Args:
        c (Context): task context
        filter_ (str, optional): an optional filter string. Defaults to "".
    """
    inv_path = Path("./docs/_build/html/objects.inv")
    if not inv_path.exists():
        doc(c)

    if filter_:
        filter_ = filter_.lower()

    with c.cd(str(Path("./docs"))):
        output: Result = c.run(
            join(["python", "-m", "sphinx.ext.intersphinx", "_build/html/objects.inv"]),
            echo=True,
            hide="stdout",
        )
        print(
            "".join(
                l
                for l in output.stdout.splitlines(True)
                if (l and not l[0].isspace()) or (not filter_) or (filter_ in l.lower())
            ),
        )


@task
def start_gunicorn(c, workers=1, log_level="info", docker=False):
    """Start the gunicorn server.

    This task is intended to be run in docker.
    The gunicorn server port defaults to 8080 but can be changed by setting
    the SERVER_PORT environment variable.

    Args:
        c (Context): task context
        workers (int, optional): The number of parallel workers (set this to around <nr_of_cores>*2 + 1). Defaults to 1.
        log_level (str, optional): the log level to output in console. Defaults to "info".
        docker (bool, optional): set this to True if running inside of docker. Defaults to false.
    """
    server_port: str = environ.get("SERVER_PORT", "8080")
    assert match(
        r"[1-9][0-9]*", server_port
    ), f"The given server port '{server_port}' does not have the right format! (must be a valid port number)"
    cmd = [
        "python",
        "-m",
        "gunicorn",
        "--pythonpath",
        ".",
        "--worker-tmp-dir",
        "/dev/shm" if docker else "/tmp",  # use in memory file system for heartbeats
        "-w",
        environ.get("GUNICORN_WORKERS", str(workers)),
        "-b",
        f"0.0.0.0:{server_port}",
        "--log-level",
        log_level.lower(),
        "--error-logfile=-",
        f"{MODULE_NAME}:create_app()",
    ]

    print(join(cmd))

    # replaces the current process with the subprocess!
    replace_process(cmd[0], cmd, environ)


@task
def await_db(c):
    """Docker specific task. Do not call."""
    c.run("/wait", echo=True, warn=False)


@task
def upgrade_db(c):
    """Upgrade the database to the newest migration."""
    c.run(join(["python", "-m", "flask", "db", "upgrade"]), echo=True, warn=True)


@task
def ensure_paths(c):
    """Docker specific task. Do not call."""
    Path("/app/instance").mkdir(parents=True, exist_ok=True)


@task(ensure_paths, await_db, upgrade_db)
def start_docker(c):
    """Docker entry point task. Do not call!"""
    if not environ.get("M4A_SECRET_KEY"):
        environ["M4A_SECRET_KEY"] = urandom(32).hex()

    log_level = environ.get("DEFAULT_LOG_LEVEL", "INFO")
    concurrency_env = environ.get("CONCURRENCY", "4")
    concurrency = int(concurrency_env) if concurrency_env.isdigit() else 1
    start_gunicorn(c, workers=concurrency, log_level=log_level, docker=True)


@task
def list_licenses(
    c,
    format_="json",
    include_installed=False,
    summary=False,
    short=False,
    echo=False,
):
    """List licenses of dependencies.

    By default only the direct (and transitive) dependencies of the project are included.

    Args:
        c (Context): task context
        format_ (str, optional): The output format (json, html, markdown, plain, plain-vertical, rst, confluence, json-license-finder, csv). Defaults to "json".
        include_installed (bool, optional): If true all currently installed packages are considered dependencies. Defaults to False.
        summary (bool, optional): If true output a summary of found licenses. Defaults to False.
        short (bool, optional): If true only name, version, license and authors of a apackage are printed. Defaults to False.
        echo (bool, optional): If true the command used to generate the license output is printed to console. Defaults to False.
    """
    packages: List[str] = []
    if not include_installed:
        packages_output: Result = c.run(
            join(["poetry", "export", "--dev", "--without-hashes"]),
            echo=False,
            hide="both",
        )
        packages = [p.split("=", 1)[0] for p in packages_output.stdout.splitlines() if p]
    cmd: List[str] = [
        "pip-licenses",
        "--format",
        format_,
        "--with-authors",
        "--allow-only",
        ";".join(ALLOWED_LICENSES),
    ]
    if not short:
        cmd += [
            "--with-urls",
            "--with-description",
            "--with-license-file",
            "--no-license-path",
            "--with-notice-file",
        ]
    if summary:
        cmd.append("--summary")
    if not include_installed:
        cmd += [
            "--packages",
            *packages,
        ]
    c.run(
        join(cmd),
        echo=echo,
        warn=True,
    )


@task
def update_licenses(c, include_installed=False):
    """Update the licenses template to include all licenses.

    By default only the direct (and transitive) dependencies of the project are included.

    Args:
        c (Context): task context
        include_installed (bool, optional): Include all currently installed libraries. Defaults to False.
    """
    packages: List[str] = []
    if not include_installed:
        packages_output: Result = c.run(
            join(["poetry", "export", "--dev", "--without-hashes"]),
            echo=False,
            hide="both",
        )
        packages = [p.split("=", 1)[0] for p in packages_output.stdout.splitlines() if p]
    cmd: List[str] = [
        "pip-licenses",
        "--format",
        "html",
        "--output-file",
        str((Path(".") / Path(MODULE_NAME) / Path("templates/licenses.html")).resolve()),
        "--with-authors",
        "--with-urls",
        "--with-description",
        "--with-license-file",
        "--no-license-path",
        "--with-notice-file",
        "--allow-only",
        ";".join(ALLOWED_LICENSES),
    ]
    if not include_installed:
        cmd += [
            "--packages",
            *packages,
        ]
    c.run(
        join(cmd),
        echo=True,
        hide="err",
        warn=True,
    )


@task(update_licenses)
def update_dependencies(c):
    """Update dependencies that are derived from the pyproject.toml dependencies (e.g. doc dependencies and licenses).

    Args:
        c (Context): task context
    """
    c.run(
        join(
            [
                "poetry",
                "export",
                "--dev",
                "--without-hashes",
                "--format",
                "requirements.txt",
                # "--without-hashes",  # with hashes fails because pip is to strict with transitive dependencies
                "--output",
                str(Path("./docs/requirements.txt")),
            ]
        ),
        echo=True,
        hide="err",
        warn=True,
    )
