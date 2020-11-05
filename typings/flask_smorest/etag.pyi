"""
This type stub file was generated by pyright.
"""

"""ETag feature"""
class EtagMixin:
    """Extend Blueprint to add ETag handling"""
    METHODS_CHECKING_NOT_MODIFIED = ...
    METHODS_NEEDING_CHECK_ETAG = ...
    METHODS_ALLOWING_SET_ETAG = ...
    ETAG_INCLUDE_HEADERS = ...
    def etag(self, etag_schema=...):
        """Decorator generating an endpoint response

        :param etag_schema: :class:`Schema <marshmallow.Schema>` class
            or instance. If not None, will be used to serialize etag data.

        Can be used as either a decorator or a decorator factory:

            Example: ::

                @blp.etag
                def view_func(...):
                    ...

                @blp.etag(EtagSchema)
                def view_func(...):
                    ...

        The ``etag`` decorator expects the decorated view function to return a
        ``Response`` object. It is the case if it is decorated with the
        ``response`` decorator.

        See :doc:`ETag <etag>`.
        """
        ...
    
    def check_etag(self, etag_data, etag_schema=...):
        """Compare If-Match header with computed ETag

        Raise 412 if If-Match header does not match.

        Must be called from resource code to check ETag.

        Unfortunately, there is no way to call it automatically. It is the
        developer's responsability to do it. However, a warning is logged at
        runtime if this function was not called.

        Logs a warning if called in a method other than one of
        PUT, PATCH, DELETE.
        """
        ...
    
    def set_etag(self, etag_data, etag_schema=...):
        """Set ETag for this response

        Raise 304 if ETag identical to If-None-Match header

        Must be called from resource code, unless the view function is
        decorated with the ``response`` decorator, in which case the ETag is
        computed by default from response data if ``set_etag`` is not called.

        Logs a warning if called in a method other than one of
        GET, HEAD, POST, PUT, PATCH.
        """
        ...
    


