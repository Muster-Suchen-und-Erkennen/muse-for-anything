from pathlib import Path
import re
from secrets import token_urlsafe
from typing import Any, List
from flask import Flask, render_template, redirect, Blueprint, g
from flask.globals import current_app
from flask.views import MethodView
from flask_static_digest import FlaskStaticDigest
from werkzeug.utils import cached_property
from warnings import warn

ROOT_BLP = Blueprint("Root Routes", __name__)


@ROOT_BLP.route("/<string:file>")
def static_resources(file):
    if "." in file:
        return redirect(g.static_digest.static_url_for("static", filename=file))
    return render_template("index.html", title="muse4anything")


@ROOT_BLP.route("/assets/<string:file>")
def asset(file):
    if "." in file:
        return redirect(
            g.static_digest.static_url_for("static", filename="assets/" + file)
        )
    return render_template("index.html", title="muse4anything")


class SPA(MethodView):

    _BODY_REGEX = re.compile(
        r".*<body[^>]*>(?P<body>.*)</body>.*", flags=re.MULTILINE | re.DOTALL
    )
    _SKRIPT_REGEX = re.compile(
        r'<script[^>]*src="/static/(?P<source>[^"]*)"[^>]*>\s*</script>'
    )

    def _get_skripts(self) -> List[str]:
        static_folder = current_app.static_folder
        if static_folder is None:
            warn("No static folder found. Did you forget to compile the UI?")
            return []
        static = Path(static_folder)
        index = static / Path("index.html")
        if index.exists():
            with index.open() as _file:
                html = "".join(_file.readlines())
                matches = self._BODY_REGEX.match(html)
                body = matches.group("body") if matches else ""
                skripts = self._SKRIPT_REGEX.findall(body)
                print(html)
                return skripts
        else:
            # when in watch mode webpack does not compile the index.html...
            skripts = [s.name for s in static.glob("*.bundle.js")]
            skripts += [s.name for s in static.glob("*.chunk.js")]
            # emulate webpack sort order
            skripts.sort(key=lambda name: 1 if name.startswith("app") else 0)
            return skripts
        return []

    @cached_property
    def skripts(self) -> List[str]:
        return self._get_skripts()

    def get(self, path: str):
        if current_app.config.get("DEBUG", False):
            # circumvent cached property in debug mode...
            vars(self)["skripts"] = self._get_skripts()
            print("HEEEEELOOOOO")
        return render_template("index.html", title="muse4anything", skripts=self.skripts)


SPA_VIEW: Any = SPA().as_view("SPA")

ROOT_BLP.add_url_rule(
    "/",
    defaults={"path": ""},
    view_func=SPA_VIEW,
    methods=[
        "GET",
    ],
)
ROOT_BLP.add_url_rule(
    "/<path:path>",
    view_func=SPA_VIEW,
    methods=[
        "GET",
    ],
)


def register_root_routes(app: Flask, static_digest: FlaskStaticDigest):
    """Register the root routes blueprint."""

    def set_static_digest() -> None:
        g.static_digest = static_digest

    ROOT_BLP.before_request(set_static_digest)

    if app.config.get("DEBUG", False):
        # add cache busting for debugging as only production uses correctlly hashed files by default
        @app.template_filter("bustcache")
        def cache_busting_filter(s: str) -> str:
            """Cache bust filter that adds a random hash to the url to circumvent browser cache."""
            return s + "?chache-bust={}".format(token_urlsafe(16))

    else:
        # noop cache busting for production
        @app.template_filter("bustcache")
        def cache_busting_filter(s: str) -> str:
            """Noop cache bust filter for production."""
            return s

    app.register_blueprint(ROOT_BLP)
