"""
This type stub file was generated by pyright.
"""

class FlaskOso:
    """oso flask plugin

    This plugin must be initialized with a flask app, either using the
    ``app`` parameter in the constructor, or by calling :py:meth:`init_app` after
    construction.

    The plugin must be initialized with an :py:class:`oso.Oso` instance before
    use, either by passing one to the constructor or calling
    :py:meth:`set_oso`.

    **Authorization**

    - :py:meth:`FlaskOso.authorize`: Check whether an actor, action and resource is
      authorized. Integrates with flask to provide defaults for actor & action.

    **Configuration**

    - :py:meth:`require_authorization`: Require at least one
      :py:meth:`FlaskOso.authorize` call for every request.
    - :py:meth:`set_get_actor`: Override how oso determines the actor
      associated with a request if none is provided to :py:meth:`FlaskOso.authorize`.
    - :py:meth:`set_unauthorized_action`: Control how :py:meth:`FlaskOso.authorize`
      handles an unauthorized request.
    - :py:meth:`perform_route_authorization`:
      Call `authorize(resource=flask.request)` before every request.
    """
    def __init__(self, oso=..., app=...) -> None:
        ...
    
    def set_oso(self, oso):
        """Set the oso instance to use for authorization

        Must be called if ``oso`` is not provided to the constructor.
        """
        ...
    
    def init_app(self, app):
        """Initialize ``app`` for use with this instance of ``FlaskOso``.

        Must be called if ``app`` isn't provided to the constructor.
        """
        ...
    
    def set_get_actor(self, func):
        """Provide a function that oso will use to get the current actor.

        :param func: A function to call with no parameters to get the actor if
                     it is not provided to :py:meth:`FlaskOso.authorize`. The return value
                     is used as the actor.
        """
        ...
    
    def set_unauthorized_action(self, func):
        """Set a function that will be called to handle an authorization failure.

        The default behavior is to raise a Forbidden exception, returning a 403
        response.

        :param func: A function to call with no parameters when a request is
                     not authorized.
        """
        ...
    
    def require_authorization(self, app=...):
        """Enforce authorization on every request to ``app``.

        :param app: The app to require authorization for. Can be omitted if
                    the ``app`` parameter was used in the ``FlaskOso``
                    constructor.

        If :py:meth:`FlaskOso.authorize` is not called during the request processing,
        raises an :py:class:`oso.OsoError`.

        Call :py:meth:`FlaskOso.skip_authorization` to skip this check for a particular
        request.
        """
        ...
    
    def perform_route_authorization(self, app=...):
        """Perform route authorization before every request.

        Route authorization will call :py:meth:`oso.Oso.is_allowed` with the
        current request (from ``flask.request``) as the resource and the method
        (from ``flask.request.method``) as the action.

        :param app: The app to require authorization for. Can be omitted if
                    the ``app`` parameter was used in the ``FlaskOso``
                    constructor.
        """
        ...
    
    def skip_authorization(self, reason=...):
        """Opt-out of authorization for the current request.

        Will prevent ``require_authorization`` from causing an error.

        See also: :py:func:`flask_oso.skip_authorization` for a route decorator version.
        """
        ...
    
    def authorize(self, resource, *, actor=..., action=...):
        """Check whether the current request should be allowed.

        Calls :py:meth:`oso.Oso.is_allowed` to check authorization. If a request
        is unauthorized, raises a ``werkzeug.exceptions.Forbidden``
        exception.  This behavior can be controlled with
        :py:meth:`set_unauthorized_action`.

        :param actor: The actor to authorize. Defaults to ``flask.g.current_user``.
                      Use :py:meth:`set_get_actor` to override.
        :param action: The action to authorize. Defaults to
                       ``flask.request.method``.
        :param resource: The resource to authorize.  The flask request object
                         (``flask.request``) can be passed to authorize a
                         request based on route path or other request properties.

        See also: :py:func:`flask_oso.authorize` for a route decorator version.
        """
        ...
    
    @property
    def app(self):
        ...
    
    @property
    def oso(self):
        ...
    
    @property
    def current_actor(self):
        ...
    
    def teardown(self, exception):
        ...
    


