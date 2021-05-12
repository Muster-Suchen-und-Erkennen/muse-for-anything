from pathlib import Path
import re
from secrets import token_urlsafe
from typing import Any, List
from flask import Flask, render_template, redirect, Blueprint, g, abort, request
from flask.globals import current_app
from flask.views import MethodView
from flask_static_digest import FlaskStaticDigest
from werkzeug.utils import cached_property
from warnings import warn
from http import HTTPStatus

from .db.models.users import User, DB, UserRole

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

    def _is_first_run(self) -> bool:
        """Return true if no user exists in the database."""
        return not User.exists()

    @property
    def is_first_run(self) -> bool:
        first_run = self._is_first_run()
        if not first_run:
            # only cache False as this is the more likely case and will never change
            self.__dict__["is_first_run"] = False
        return first_run

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
        if path and path.startswith("api/"):
            abort(404)
        if self.is_first_run:
            return redirect("/first-run/", code=HTTPStatus.SEE_OTHER)
        extra_script_sources = ""
        if current_app.config.get("DEBUG", False):
            extra_script_sources = "'unsafe-eval' 'self'"
            # circumvent cached property in debug mode...
            vars(self)["skripts"] = self._get_skripts()
        return render_template(
            "index.html",
            title="muse4anything",
            skripts=self.skripts,
            nonce=token_urlsafe(16),
            extra_script_sources=extra_script_sources,
        )


class FirstRunView(MethodView):
    @property
    def is_first_run(self) -> bool:
        """Return true if no user exists in the database."""
        return not User.exists()

    def get(self):
        if not self.is_first_run:
            abort(404)

        return render_template(
            "first-run.html",
            title="muse4anything",
            nonce=token_urlsafe(16),
        )

    def post(self):
        if not self.is_first_run:
            abort(404)
        username: str = request.form.get("username", "")
        password: str = request.form.get("password", "")
        password_retype: str = request.form.get("password-retype", "")

        if not username or not password or not password_retype:
            abort(HTTPStatus.BAD_REQUEST)

        if len(username) < 3:
            abort(HTTPStatus.BAD_REQUEST)

        if len(password) < 3:
            abort(HTTPStatus.BAD_REQUEST)

        if password != password_retype:
            abort(HTTPStatus.BAD_REQUEST)

        user = User(username=username, password=password)
        user_role = UserRole(user=user, role="admin")
        DB.session.add(user)
        DB.session.add(user_role)
        DB.session.commit()
        return redirect("/", code=HTTPStatus.MOVED_PERMANENTLY)


FIRST_RUN_VIEW: Any = FirstRunView().as_view("FirstRunView")

ROOT_BLP.add_url_rule(
    "/first-run/",
    view_func=FIRST_RUN_VIEW,
    methods=[
        "GET",
        "POST",
    ],
)


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
