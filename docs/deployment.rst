Deploying MUSE4Anything
=======================

This is a guide to deploying MUSE4Anything using the provided Dockerfile in the MUSE4Anything repository.

.. warning:: If you want to deploy MUSE4Anything in production then read this guide completely before deploying to not miss any security relevant setting!


Using the Dockerfile
---------------------


Building the Container Image
""""""""""""""""""""""""""""

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/Muster-Suchen-und-Erkennen/muse-for-anything.git
    
    cd muse-for-anything

    # optionally checkout a branch
    # git checkout branch-name

    docker build --tag muse4anything-image-tag .


Creating a Volume for Persistent Storage
""""""""""""""""""""""""""""""""""""""""

.. code-block:: bash

    # create a new volume
    docker volume create muse-volume-name

    # get information about the volume
    docker volume inspect muse-volume-name

The root folder of the volume is listed as ``Mountpoint`` in the output of ::command:`docker volume inspect`.


Starting the Container
""""""""""""""""""""""

.. code-block:: bash

    # start the container
    docker run -d --mount source=muse-volume-name,target=/app/instance -p 8080:8080 --name muse4anything-container-name muse4anything-image-tag

    # stop the container
    docker stop muse4anything-container-name

    # remove the container
    docker rm muse4anything-container-name


Configuration Options
---------------------

Configuration Options Using ENV Variables
"""""""""""""""""""""""""""""""""""""""""

To configure env variables with docker use the ``--env`` or ``--env-file`` options of the :command:`docker run` command (see https://docs.docker.com/engine/reference/commandline/run/#options).

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - ENV Var
     - Example
     - Description
   * - :envvar:`M4A_SECRET_KEY`
     - ``aTrulyRandomSecret``
     - The value is used as the server secret for checking JWT token validity.
   * - :envvar:`M4A_REVERSE_PROXY_COUNT`
     - ``1``
     - The number of reverse proxy headers flask should trust. Set this value to the number of reverse proxies you have configured for your MUSE4Anything instance.
   * - :envvar:`M4A_DEFAULT_LOG_SEVERITY`
     - ``20``
     - The minimal severity of log messages that should appear in the log. (10=DEBUG, 20=INFO, 30=WARNING; defaults to 30)
   * - :envvar:`FORWARDED_ALLOW_IPS`
     - ``127.0.0.1``
     - Allow forwarding headers from the IP in this ENV var to the flask app. (see also :external+gunicorn:ref:`forwarded-allow-ips`)


Configurations Using :file:`cinfig.py` or :file:`config.json`
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

.. hint:: Please set the SECRET_KEY setting via the environment variable :envvar:`M4A_SECRET_KEY` described above!

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Key
     - Example
     - Description
   * - REVERSE_PROXY_COUNT
     - ``1``
     - The number of reverse proxy headers flask should trust. Set this value to the number of reverse proxies you have configured for your MUSE4Anything instance.
   * - DEFAULT_LOG_SEVERITY
     - ``20``
     - The minimal severity of log messages that should appear in the log. (10=DEBUG, 20=INFO, 30=WARNING; defaults to 30)
   * - BCRYPT_LOG_ROUNDS
     - ``13``
     - The number of bcrypt hash rounds to use. (use the :ref:`calibrate` command for an indicator on what value to set for your server)
   * - SQLALCHEMY_DATABASE_URI
     - ``mysql://username:password@server/db``
     - The database connection string used by the SQLAchemy ORM. (Requires a database driver to be installed in the docker container! This is currently not the case...)

.. seealso:: Settings from other libraries:

    * Flask https://flask.palletsprojects.com/en/2.0.x/config/#builtin-configuration-values
    * Flask-SQLAlchemy https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/
    * Flask-JWT-Extended https://flask-jwt-extended.readthedocs.io/en/stable/options/


Deploying to Production
-----------------------

.. warning:: Always provide a sufficient random server secret via the environment variable :envvar:`M4A_SECRET_KEY` described above!
    This secret should stay the same on updates but can be exchanged if a security breach was detected to immediately invalidate all client sessions using JWT Tokens.

.. hint:: For https to work behind a reverse proxy make sure to set the ``REVERSE_PROXY_COUNT`` setting.
    Also check if the reverse proxy correctly sends one of the headers (see :external+gunicorn:ref:`secure-scheme-headers`) indicating that the request was sent via https.


