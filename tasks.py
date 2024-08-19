from os import environ
from os import execvpe as replace_process
from os import urandom
from pathlib import Path
from re import match
from shlex import join
from typing import List, cast
from platform import system

from dotenv import load_dotenv, set_key, unset_key
from invoke import task
from invoke.context import Context
from invoke.runners import Result

if system() == "Windows":
    from subprocess import list2cmdline as join
else:
    from shlex import join

load_dotenv(".flaskenv")
load_dotenv(".env")

MODULE_NAME = "muse_for_anything"
CELERY_WORKER = f"{MODULE_NAME}.celery_worker:CELERY"


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
def stop_broker(c):
    """Stop the previously started redis broker container with docker or podman.

    Discovers the container id from the environment variable REDIS_CONTAINER_ID.
    If the variable is not set ``--latest`` is used (this assumes that the latest
    created container is the broker!).

    To use podman instead of docker set the DOCKER_CMD environment variable to "podman".

    Args:
        c (Context): task context
    """
    c = cast(Context, c)
    docker_cmd = environ.get("DOCKER_CMD", "docker")
    container_id = environ.get("REDIS_CONTAINER_ID", "--latest")
    c.run(join([docker_cmd, "stop", container_id]))


@task(stop_broker)
def reset_broker(c):
    """Remove the current redis container and unset the REDIS_CONTAINER_ID variable.

    Discovers the container id from the environment variable REDIS_CONTAINER_ID.
    If the variable is not set this task does nothing.

    To use podman instead of docker set the DOCKER_CMD environment variable to "podman".

    Args:
        c (Context): task context
    """
    c = cast(Context, c)
    docker_cmd = environ.get("DOCKER_CMD", "docker")
    container_id = environ.get("REDIS_CONTAINER_ID")
    if not container_id:
        return
    c.run(join([docker_cmd, "rm", container_id]), echo=True)
    dot_env_path = Path(".env")
    unset_key(dot_env_path, "REDIS_CONTAINER_ID")


@task
def start_broker(c, port=None):
    """Start a redis broker container with docker or podman.

    Resuses an existing container if the environment variable REDIS_CONTAINER_ID is set.
    The reused container ignores the port option!
    Sets the environemnt variable in the .env file if a new container is created.

    Redis port is optionally read from REDIS_PORT environment variable. Use the
    ``reset-broker`` task to remove the old container to create a new container
    with a different port.

    To use podman instead of docker set the DOCKER_CMD environment variable to "podman".

    Args:
        c (Context): task context
        port (str, optional): outside port for connections to redis. Defaults to "6379".
    """
    c = cast(Context, c)
    docker_cmd = environ.get("DOCKER_CMD", "docker")
    container_id = environ.get("REDIS_CONTAINER_ID", None)

    if container_id:
        res: Result = c.run(join([docker_cmd, "restart", container_id]), echo=True)
        if res.failed:
            print(f"Failed to start container with id {container_id}.")
        return

    if not port:
        port = environ.get("REDIS_PORT", "6379")
    c.run(join([docker_cmd, "run", "-d", "-p", f"{port}:6379", "redis"]), echo=True)
    result: Result = c.run(join([docker_cmd, "ps", "-q", "--latest"]), hide=True)
    result_container_id = result.stdout.strip()
    dot_env_path = Path(".env")
    if not dot_env_path.exists():
        dot_env_path.touch()
    set_key(dot_env_path, "REDIS_CONTAINER_ID", result_container_id)


@task
def worker(
    c, pool="solo", concurrency=1, dev=False, log_level="INFO", beat=False, watch=False
):
    """Run the celery worker, optionally starting the redis broker.

    Args:
        c (Context): task context
        pool (str, optional): the executor pool to use for celery workers (defaults to "solo" for development on linux and windows)
        concurrency (int, optional): the number of concurrent workers (defaults to 1 for development)
        dev (bool, optional): If true the redis docker container will be started before the worker and stopped after the workers finished. Defaults to False.
        log_level (str, optional): The log level of the celery logger in the worker (DEBUG|INFO|WARNING|ERROR|CRITICAL|FATAL). Defaults to "INFO".
        beat (bool, optional): If True, a celery beat scheduler will be started alongside the worker. This is needed for periodic tasks. Should only be set to True for one worker otherwise the periodic tasks get executed too often (see readme file).
        watch (bool, optional): If True, watch for file changes and restart workers automatically. Defaults to False.
    """
    if dev:
        start_broker(c)
    c = cast(Context, c)
    cmd = [
        "celery",
        "--app",
        CELERY_WORKER,
        "worker",
        f"--pool={pool}",
        "--concurrency",
        str(concurrency),
        "--loglevel",
        log_level.upper(),
        "-E",
    ]

    if watch:
        cmd = [
            "watchmedo",
            "auto-restart",
            f"--directory=./{MODULE_NAME}",
            "--pattern=*.py",
            "--recursive",
            "--debounce-interval=3",
            "--kill-after=10",
            "--no-restart-on-command-exit",
            "--",
        ] + cmd

    if beat:
        cmd += ["-B"]

    if dev:
        c.run(join(cmd), echo=True)
        stop_broker(c)
    else:
        # if not in dev mode completely replace the current process with the started process
        print(join(cmd))
        replace_process(cmd[0], cmd, environ)


@task
def celery_status(c):
    """Show the status of celery workers.

    Args:
        c (Context): task context
    """
    c = cast(Context, c)
    c.run(
        join(["celery", "--app", CELERY_WORKER, "status"]),
        echo=True,
        hide="err",
        warn=True,
    )


@task
def celery_queues(c):
    """Show the queus of the celery instance.

    Args:
        c (Context): task context
    """
    c = cast(Context, c)
    c.run(
        join(["celery", "--app", CELERY_WORKER, "list", "bindings"]),
        echo=True,
        hide="err",
        warn=True,
    )


@task(celery_queues)
def celery_inspect(c):
    """Show a detailed status report of the running workers and queues.

    Args:
        c (Context): task context
    """
    c.run(
        join(["celery", "--app", CELERY_WORKER, "inspect", "report"]),
        echo=True,
        hide="err",
        warn=True,
    )
    c.run(
        join(["celery", "--app", CELERY_WORKER, "inspect", "stats"]),
        echo=True,
        hide="err",
        warn=True,
    )


@task
def celery_enabe_events(c):
    """Enable celery worker events events.

    Args:
        c (Context): task context
    """
    c.run(
        join(["celery", "--app", CELERY_WORKER, "control", "enable_events"]),
        echo=True,
        hide="err",
        warn=True,
    )


@task
def celery_disable_events(c):
    """Disable celery worker events events.

    Args:
        c (Context): task context
    """
    c.run(
        join(["celery", "--app", CELERY_WORKER, "control", "disable_events"]),
        echo=True,
        hide="err",
        warn=True,
    )


@task(pre=[celery_enabe_events], post=[celery_disable_events])
def celery_monitor(c):
    """Show current events.

    Args:
        c (Context): task context
    """
    c.run(
        join(["celery", "--app", CELERY_WORKER, "events"]),
        pty=True,
        hide="err",
        warn=True,
    )


@task
def purge_task_queues(c):
    """Purge all task queues. Deletes tasks forever!

    Args:
        c (Context): task context
    """
    answer = input(
        "This action cannot be undone. Type in 'purge' to purge all task queues:"
    )
    if answer != "purge":
        print("Not purging task queues.")
        return
    c.run(
        join(["celery", "--app", CELERY_WORKER, "purge"]),
        echo=True,
        hide="err",
        warn=True,
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
