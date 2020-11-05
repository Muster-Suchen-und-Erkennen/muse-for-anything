API Documentation of the Flask app
==================================

The interactive documentation of the REST api with `Redoc <https://github.com/Redocly/redoc>`_ can be found here: `Api documentation <api.html>`_

The OpenAPI specification can also be downloaded here: :download:`api.json <api.json>` 



Format of API Responses
-----------------------

The API is a REST API that should be navigatable by only using links.
The default (and only) response document format of the API is JSON.
To accommodate for the fact that JSON does not have a native link datatype a custom format is used for all API responses.

.. warning:: This format is currently a draft only and may change anytime!


Example of the custom format:

.. code-block:: json

    {
        "links": [
            {"href": "/api/v1/auth/", "rel": ["api", "authentication"], "resourceType": "api"},
            {"href": "/api/v1/auth/login/", "rel": ["login", "post"], "resourceType": "login"},
        ],
        "embedded": [
            {
                "links": [],
                "key": {"namespaceId": "nsExample"},
                "data": {
                    "self": {"href": "/api/v1/namespaces/nsExample/", "rel": ["namespace"], "resourceType": "namespace"}
                }
            }
        ],
        "keyedLinks": [
            {"href": "/api/v1/namespaces/{namespaceId}/", "rel": ["namespace"], "resourceType":"namespace", "key": ["namespaceId"]}
        ]
        "data": {
            "self": {"href": "/api/v1/", "rel": ["api", "root"], "resourceType": "api"},
        }
    }

Each API response always has the two fields ``links`` and ``data``.
An api response may have the field ``keyedLinks`` or teh field ``key``, or both.
Additionally a top level (not embedded) API response can have the ``embedded`` field.


``links``
    Contains all navigational links relevant for the current resource.
    The ``rel`` attribute of a link is a list of strings.
    This allows for a more fine grained tagging of the links than a single rel value could.
    The type of the resource found behind the link is also expressed as a rel value.
    For example ``"api"`` is a collection of REST resources that form an API.

    The client **should** use these links for navigating the Api.
    The client **should** only select the links based on their ``rel`` attributes and **must not** depend on a specific url in the ``href`` attribute!
``embedded``
    Contains API response objects that are related to the returned API response.
    These can be cached by the client to avoid subsequent api calls.

    The client **must** never depend on anything returned inside of the ``embedded`` attribute!
``keyedLinks``
    Contains shortcut links that contain a template url that can be used with a ``key`` to construct a valid url.
    The links in this list contain a ``key`` attribute that matches the template variables in the url and can be used to check if the ``key`` is compatible with this link.

    The client **should** only use these links when there is no alternative navigation possible using only normal links from the ``links`` attribute.
    This can be the case if the client stored the resource ``key`` in the url and has to reconstruct its state from its current url (or similar).
    The client **must** check if the ``key`` matches the ``key`` attribute of the keyed link before constructing the link.
``key``
    A minimal key for this resource that can be used with a keyed link.
    The key is a mapping from key variables to key values (both as strings).
    
    To construct a link from a keyed link all keys of the link's ``key`` attribute must have a value in the key.
    Then the key values can be safely used to fill in the the template variables that correspond to the key variables (the keys of the key mapping).

    If a key has more key variables than specified in the links ``key`` attribute it **must** still create a valid url to an existing resource.
    This resource may not be of the same type as the resource the key was from.

    If the key has exactly all key variables specified in the links ``key`` attribute the resource found behind the url must be the same resource the key was from.

    The meaning of key variables **should** be as stable as the meaning of a rel attribute (never change them without updating the api major version!).
``data``
    Contains a single data object.

    All data objects have a ``self`` attribute that contains their canonical url.
    This attribute should be used to discover the links for the specific object if it is part of a collection resource.

    If the resource is a collection ``data`` contains a an object of the form ``{"self": {...}, "items": []}``.
    The ``items`` attribute of the collection contains a list of links to the resources in the collection.
    The actual resources should always be provided in the ``embedded`` attribute of the API response.
    If a client does not use the ``embedded`` attribute to populate a client side cache it can replace the links in the ``items`` attribute with the corresponding embedded item by matching the href of the link and the items self link.

    A client that caches API responses **may** use the url in the ``self`` attribute of the data object as the cache key for this API response if the response contains exactly one object.

All links are represented by a json object with a ``href`` and a ``rel`` attribute.
The ``href`` attribute should contain a fully realized url without any variables.
The ``rel`` attribute should contain a rel for the type of the resource.
If the resource behind the url should be called with another http method the method should be included as a rel (in lowercase).
The ``resourceType`` attribute of the link is the type of resource the API will will deliver when calling this link.
The ``resourceType`` is also one of the entries in ``rel``.


Rationale Behind the Format
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The format is similar to (and inspired by) the existing json format standards, that standardise how links should be embedded into json documents.
It does however not follow any one specific format.
This is because the exisiting formats are often very verbose (json+LD) or otherwise have serious limitations in their expressiveness or ease of use.

The custom format should enable the following goals:

Navigate the API without constructing URLs
    To reach the highest level of maturity of a REST API (HATEOAS) it is neccessary to be able to navigate the API by only following the provided hyperlinks.
    The format should allow the specification of these links with enough detail to allow navigation and actions on resources (e.g. crud actions using http methods).
    This means that the link format must have a way to specify what http/crud methods are supported by this resource.
Specify how to navigate with templated links
    The format should allow to define shortcuts to resources with templated urls.
    This is necessery if the client does not want to encode the full self link of a resource into its state url.
    The format should allow clients to reliably and safely decide what state needs to be encoded into the clients state url and how this state can be used later with the templated urls.
Seperate metadata from the data
    The metadata (e.g. the links and embedded responses) should be easy to seperate from the data.
    The format should make it easy to work with the data without all the extra api information embedded into the data object.
Allow for caching and embedding responses
    The embedded objects should be cacheable as is with the chache api provided by modern browsers.
    The client should only need to reconstruct a response object with the embedded response as the response body based on the current response headers.
Usable without supporting library
    The format should be usable (and ideally provide additional benefits over plain json objects) without a full library that handles parsing and caching in the client.
    The navigational portion of the format (navigating the api via the provided links) should follow simple rules while still allowing clients to benefit from the additional metadata provided (like schema or type information).
    Caching should be made as simple as possible for the client.
Avoid special characters for attribute names
    Because most formats mix the data with their annotations they use special characters to differentiate their attributes from the data's attributes.
    This makes using the json objects more cumbersome as for example in javascript accessing these fields cannot be done with the dot notation.


The custom format is mostly inspired by the JSON+Hal specification.
The JSON+Hal format is very easy to use with only three special defined attributes (``_links``, ``_embedded`` and ``self`` (in the ``_links`` attribute)).
This makes it easy to learn.
In fact all three attributes can be found again in the custom format.

.. note:: Inspirations for the custom format:

    JSON+Hal
        Link: https://tools.ietf.org/html/draft-kelly-json-hal-06

        Inspired the naming of the ``links``, ``embedded`` and ``self`` attributes (but without the undescores).
    Ion
        Link: https://ionspec.org

        Inspired the rel attribute of links to be a list instead of a single string.
        Also inspired me to encode http methods into links.

        The ``data`` attribute is inspired by the ``value`` attribute of value objects.
    Collection+JSON
        Link: http://amundsen.com/media-types/collection/

        Inspired a single list of links rather than using the map style of JSON+Hal or from Ion.
    SIREN
        Link:

        Inspired a single list of links rather than using the map style of JSON+Hal or from Ion.
        Inspired encapsulating the object in a ``data`` attribute (SIREN uses ``properties``).

    Relevant articles and other links:
     *  https://sookocheff.com/post/api/on-choosing-a-hypermedia-format/
     *  https://brandur.org/elegant-apis#hyper-schema


The actual data object is encapsuled in the ``data`` attribute.
This was done specifically, to make it trivially easy to seperate the data from the metadata of the response like links and other embedded objects.
The only restriction this format poses on the data object is that it has a ``self`` attribute
JSON+Hal actually embeds everything into the actual data object with the special attributes.
This means that to work with a clean data object one must first remove the links and embedded objects (without removing the special self link).

The ``embedded`` field contains full API responses (only the json response body).
These can easily be used to fill a cache to prevent execcive requests to the backend.
Only single resources **should** be embedded.
A embedded API response **must** have an empty array for its ``embedded`` field!

The links are contained in a single uniform array.
This allows for easier parsing of all links.
For example JSON+Hal could have a list of links or a single link for each key.
The ``_links`` attribute of a JSON+Hal object is a map where the keys are the rel for the link(s) behind the keys.
This makes finding a link by a single rel easier, but also makes it impossible to specify multiple values for rel.
For example in a paginated resource the "next" link can not have the type of its resources in the rel as "next" is already set.
The same goes for the special rel "self".

The custom format adresses this shortcoming by having multiple rels inside the link object itself.
The type of the REST resource can also be specified with the special ``resourceType`` attribute of the link.
By having multiple rels we can also encode crud actions and http methods for the links.

Consider the following example:

.. code-block:: json

    [
        {"href": "/api/objects/", "rel": ["collection", "myobject"], "resourceType": "myobject"},
        {"href": "/api/objects/", "rel": ["create", "post", "myobject"], "resourceType": "myobject"}
    ]

Here we can see that by having multiple rel values we can encode, that the same url can be used to get the collection of all myobjects and to create a new myobject with the POST method.
By specifying a list of special rel values the client can utilise this information and know even before calling the link what type of resource is returned and if it is a collection of these resources.


Link relations
^^^^^^^^^^^^^^

The rel attribute of a link can hold many relations.
The relations should use ``kebap-case`` and must not contain special characters that are not url safe.

Common defined rel types can be found here https://www.iana.org/assignments/link-relations/link-relations.xhtml and here https://html.spec.whatwg.org/multipage/links.html.

Additionally this format specifies these rel types:

api
    A collection of API endpoints that are provided via the ``links`` attribute of the API response.

    The client may follow and cache all api rels to speed up discovery of subsequent links.
    The client must refresh the cache on page reload or after 24 hours.
get, put, post, delete
    These rels map to the corresponding http method.
    If none of them is specified then ``get`` is implied.
create, retreive, update, delete, crud-delete
    These rels map to the common crud operations.
    They do not imply the use of a specific http method.
    If only the crud operation delete but not the http method delete is meant one can use ``crud-delete`` instead.
page
    Should always be used together with the rel ``collection``.
    Indicates that the collection is paginated.
partial
    Indicates that a resource (that is not a collection!) is only a partial of the full resource.
    A partial resource should be cached seperately from the full resource.
    Partial resources can be useful to include into collections as often not the whole resource is needed to be displayed in a collection.
    A partial resource may be used as initial value to display if it is already cached (but the full resource should be fetched from the api).
    If a partial resource has an etag it must be the same etag as for the full resource.
    If the full resource is cached and the etag does not match teh partial resource the full resource should be evicted from the cache.
<resourceType>
    All resource types are also valid rels.
    They should not have a conflict with any existing rel defined above or defined in a common spec like the ones linked above.

Rationale behind ``keyedLinks`` and ``key``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Keyed links together with the resource keys provide another means to navigate the api.
Other formats also allow templated urls but have no specified and reliable method to fill out the templates automatically.
The client can only try to fill the template by providing values from the attributes of the object the templated link was from.
This use case can however be fully realised by the server always providing fully realized (non templated) urls.

A web client that provides a ui for a end user however has a problem that cannot be addressed by only having templated urls.
If a web ui client shows a page for a resource that is part of a collection resource most users expect the url of the web client to be a path to that resource.
For this the client needs to encode how to find the resource in the api into the url.
The client cannot use the api url as it cannot depend on the url having a specific format and a web client typically has requirements for the format of its own url that do not match the api url format.
The client cannot only use rels to build its url as the resource is part of a collection.
While the collection may be discoverable by only following rels the single resource in the collection is not.
So the client would need to store the entire canonical url of the resource in its own url.
But this would lead to very large and unreadable urls for the client which is not desireable.

To solve this a web ui client typically only encodes the resource id into its url (example: ``/orders/23ca6/``).
As most formats have no way to discover what is part of a resources id this is typically hardcoded into the client.
This is a deviation from the otherwise loose coupling that a REST API that allows HATEOAS should provide.

To allow the client to build its own urls while still beeing able to use templated urls from the api without hardcoding the identifying attribute names of resources the API response format must provide additional information to the client.
The custom format does this in form of the ``key`` attribute of the API response together with the matching ``key`` in the ``keyedLinks``.

The client can then build its urls from the provided key: ``/apiObject/?orderId=23ca6``.
With a more complex key the url could look something like this ``/apiObject/?documentId=23ca6&revision=14&chapter=2``.


Algorithm for building and parsing concise client urls to and from keys
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

The client could also use a more sphisticated url building algorithm without relying on query strings.
For this the client needs to store rels and the values of the key variables in the url.
To tell values apart from the rels the client could mark them with a special character like ``:``.
This could lead to a url like the following ``/apiObject/document/:23ca6/revision/:14/chaper/:2``.

He can decode this url back into a key given the following API Response.

.. code-block:: json

    {
        "links": [],
        "keyedLinks": [
            {"rel": ["document"], "resourceType": "document", "key": ["documentId"], "href": "/api/v1/documents/{documentId}/"},
            {"rel": ["revision", "document"], "resourceType": "revision", "key": ["documentId", "documentRevisionId"], "href": "/api/v1/documents/{documentId}/revisions/{documentRevisionId}/"},
            {"rel": ["chapter", "document"], "resourceType": "chapter", "key": ["documentId", "documentRevisionId", "chapterNr"], "href": "/api/v1/documents/{documentId}/revisions/{documentRevisionId}/chapters/{chapterNr}/"},
            {"rel": ["revision", "video"], "resourceType": "revision", "key": ["videoId", "videoRevisionId"], "href": "..."}
        ],
        "data": {}
    }

The client has to iteratively resolve the key.
For this he parses its url into a list of rel, key values pairs: 

.. code-block:: json

    [
        {"rel": "document", "keyValues": ["23ca6"]},
        {"rel": "revision", "keyValues": ["14"]},
        {"rel": "chaper", "keyValues": ["2"]},
    ]

Now the client matches this list iteratively to the keyed links by their ``resourceType`` attribute.
For the first rel ``document`` this leads to the key ``["documentId"]``.
The number of keyValues for the rel must match the key length.
If multiple values are to be matched some consistent sorting should be applied to the key to not rely on the order in the key as given from the api.

The client now has reconstructed a partial key:

.. code-block:: json

    {
        "documentId": "23ca6",
    }

To resolve the next rels the client must use this partial key.
The next rel ``revision`` matches two keyed links but only one of the keys matches the partial key.
The client must check that the number of unassigned key variables matches the number of values of this next rel.
For this the client considers all key variables as assigned if they are part of the partial key.
It can the update the partial key.

.. code-block:: json

    {
        "documentId": "23ca6",
        "documentRevisionId": "14",
    }

Eventually the client will have reconstructed the full key only from rels and key values.
This realies on the API to provide unambigous key variable names and unambiguos resourceTypes (at least on the first level).

Note that the client would resolve the url ``/apiObject/chapter/:23ca6/:14/:2`` to the same key if he uses the key order from the API response.
The url ``/apiObject/revision/:23ca6/:14`` would potentially resolve to two different keys.
This can only be solved by the API using unambiguos resourceTypes everywhere (in this case a ``document-revision`` and a ``video-revision``).


In a similar way the client can construct such an url from a key with the same keyed links.
Consider the following API response.

.. code-block:: json

    {
        "links": [],
        "key": {
            "documentId": "23ca6",
            "documentRevisionId": "14"
        },
        "data": {}
    }

The client first needs to find all keyed links matching the key.

.. code-block:: json

    [
        {"rel": ["document"], "resourceType": "document", "key": ["documentId"], "href": "/api/v1/documents/{documentId}/"},
        {"rel": ["revision", "document"], "resourceType": "revision", "key": ["documentId", "documentRevisionId"], "href": "/api/v1/documents/{documentId}/revisions/{documentRevisionId}/"},
    ]

Then the client orders them by the size of their key starting with the smallest key.
The first url entry is the ``resourceType`` of the keyed link with the smallest key followed by the values for that key (``/apiObject/document/:23ca6/``).
Then the rel for the next biggest key is added to the end with the missing key values that were not already used in the url (``/apiObject/document/:23ca6/revision/:14/``).
This is done until no more keyed link is left.

Note that the keyed links my not be provided in the API response that contained the key.
The client is expected to crawl all ``api`` rels to find all potential keyed links to consider for building urls.

