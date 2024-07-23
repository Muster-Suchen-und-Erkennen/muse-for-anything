from os import environ
from typing import Dict, List, Optional, Tuple, Union
from flask_babel import gettext
from werkzeug.exceptions import SecurityError
from werkzeug.security import (
    DEFAULT_PBKDF2_ITERATIONS,
    generate_password_hash,
    check_password_hash,
)
import hashlib
from flask import Flask, Blueprint
from flask.cli import with_appcontext
import click
from itertools import cycle, chain
from operator import mul


class FlaskPassword:
    """Class handling password hashing and checking.

    Settings can be changed in the app config.
    """

    _ALLOWED_PASSWORD_HASH_FUNCTIONS = (
        set(
            [
                "sha256",
                "sha384",
                "sha512",
                "blake2b",
                "sha3_256",
                "sha3_384",
                "sha3_512",
                "shake_128",
                "shake_256",
            ]
        )
        & hashlib.algorithms_available
    )

    _app: Optional[Flask] = None

    # either "untested" or a boolean
    settings_ok: Union[bool, str] = "untested"
    security_risk: bool = False

    # either "pbkdf2" or "bcrypt"
    _password_hash_algorithm: str = "pbkdf2"

    # pbkdf2 settings
    _pbkdf2_rounds: int = 1_000_000  # timings similar to 12 log rounds of bcrypt
    _pbkdf2_hash_function: str = "sha256"
    _pbkdf2_salt_length: int = 8  # default of werkzeug

    # imported bcrypt module
    _bcrypt = None

    # bcrypt settings
    _bcrypt_log_rounds: int = 12
    _bcrypt_prefix: str = "2b"
    _bcrypt_handle_long_passwords: bool = True
    _bcrypt_long_password_hash: str = "sha256"

    def __init__(self, app: Flask = None):
        self._password_hash_algorithm = "pbkdf2"
        try:
            # check if bcrypt is available
            import bcrypt

            self._bcrypt = bcrypt
            self._password_hash_algorithm = "bcrypt"
        except ImportError:
            pass
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initializes the FlaskPassword instance with the flask app settings."""
        self._app = app
        # set default password hash method
        default = "bcrypt" if self._bcrypt else "pbkdf2"
        self._password_hash_algorithm = app.config.get("PASSWORD_HASH_ALGORITHM", default)
        if self._password_hash_algorithm == "bcrypt" and self._bcrypt is None:
            raise ValueError(
                "Cannot use bcrypt as password hash algorithm. Install the bcrypt package!"
            )

        # init pbkdf2 settings
        self._pbkdf2_rounds = app.config.get("PBKDF2_ROUNDS", 1_000_000)
        self._pbkdf2_hash_function = app.config.get("PBKDF2_HASH_FUNCTION", "sha256")
        self._pbkdf2_salt_length = app.config.get("PBKDF2_SALT_LENGTH", 8)
        if self._pbkdf2_hash_function not in self._ALLOWED_PASSWORD_HASH_FUNCTIONS:
            raise ValueError(
                f"Cannot use unsupported hash algorithm '{self._pbkdf2_hash_function}' for PBKDF2!"
            )

        # init bcrypt settings
        self._bcrypt_log_rounds = app.config.get("BCRYPT_LOG_ROUNDS", 12)
        self._bcrypt_prefix = app.config.get("BCRYPT_HASH_PREFIX", "2b")
        self._bcrypt_handle_long_passwords = app.config.get(
            "BCRYPT_HANDLE_LONG_PASSWORDS", True
        )
        self._bcrypt_long_password_hash = app.config.get(
            "BCRYPT_LONG_PASSWORDS_HASH", "sha256"
        )
        if self._bcrypt_long_password_hash not in self._ALLOWED_PASSWORD_HASH_FUNCTIONS:
            raise ValueError(
                f"Cannot use unsupported hash algorithm '{self._bcrypt_long_password_hash}' for bcrypt!"
            )

        self._log_current_settings()

        # check settings for security issues
        env = app.config.get("ENV", "production")
        should_skip = environ.get("SKIP_PASSWORD_HASHING_CHECKS", "").lower() == "true"
        should_skip_all = (
            environ.get("SKIP_PASSWORD_HASHING_CHECKS", "").lower() == "force"
        )
        if not should_skip_all and (
            app.config.get("CHECK_PASSWORD_HASH_SETTINGS", False)
            or (env == "production" and not should_skip)
        ):
            self.settings_ok = self.check_current_settings()

    def _log_current_settings(self):
        """Log the current password settings to the app logger with info severity."""
        current_settings = [
            f"Password hash algorithm '{self._password_hash_algorithm}'",
        ]
        if self._password_hash_algorithm == "bcrypt":
            current_settings.extend(
                [
                    f"Nr. of log rounds '{self._bcrypt_log_rounds}'",
                    f"Handle long passwords '{self._bcrypt_handle_long_passwords}'",
                    f"Hash algorithm for handling long passwords '{self._bcrypt_long_password_hash}'",
                ]
            )
        elif self._password_hash_algorithm == "pbkdf2":
            current_settings.extend(
                [
                    f"Nr. of rounds '{self._pbkdf2_rounds}'",
                    f"Hash function used by pbkdf2 '{self._pbkdf2_hash_function}'",
                    f"Salt length '{self._pbkdf2_salt_length}' characters",
                ]
            )

        self._app.logger.info("Current Password Settings: " + ", ".join(current_settings))

    def _to_bytes(self, string: Union[str, bytes]) -> bytes:
        """Convert string to a bytes object if necessary."""
        if isinstance(string, str):
            return string.encode(encoding="utf-8")
        return string

    def _get_hash_function(self, hash_function: str):
        """Get hash function object by name."""
        if hash_function not in self._ALLOWED_PASSWORD_HASH_FUNCTIONS:
            raise ValueError(f"Cannot use unsupported hash algorithm '{hash_function}'!")
        if hash_function == "sha256":
            return hashlib.sha256()
        elif hash_function == "sha384":
            return hashlib.sha384()
        elif hash_function == "sha512":
            return hashlib.sha512()
        elif hash_function == "blake2b":
            return hashlib.blake2b()
        elif hash_function == "sha3_256":
            return hashlib.sha3_256()
        elif hash_function == "sha3_384":
            return hashlib.sha3_384()
        elif hash_function == "sha3_512":
            return hashlib.sha3_512()
        elif hash_function == "shake_128":
            return hashlib.shake_128()
        elif hash_function == "shake_256":
            return hashlib.shake_256()
        else:
            raise ValueError(f"Cannot use unsupported hash algorithm '{hash_function}'!")

    def _hash_long_password_for_bcrypt(
        self, password: bytes, hash_function_name: str
    ) -> bytes:
        """Hash a long password to be passed to bcrypt."""
        hash_function = self._get_hash_function(hash_function_name)
        hash_function.update(password)
        if hash_function_name in ("shake_128", "shake_256"):
            hex_hash = hash_function.hexdigest(64)
        else:
            hex_hash = hash_function.hexdigest()
        return self._to_bytes(hex_hash)

    def _check_for_known_security_risks(self):
        """Check if the security_risk flag is set for this instance and raise a security error if it is.

        Raises:
            SecurityError: if a security risk was detected previously by self.check_current_settings
        """
        if self.security_risk:
            raise SecurityError(
                gettext(
                    "Cannot hash password because the current password hashing settings pose a security risk!"
                )
            )

    def generate_bcrypt_password_hash(self, password: str, rounds_log: int = None) -> str:
        """Generate a bcrypt password hash.

        Args:
            password (str): the password to hash
            rounds_log (int, optional): the nr of log rounds for the bcrypt algorithm (usually 12 < rounds < 16). Defaults to current settings.

        Raises:
            ValueError: if password is empty or None
            SecurityError: if the current password settings pose a security risk and rounds_log is None
            KeyError: if bcrypt is not defined

        Returns:
            str: the password hash to be stored in the db
        """
        if self._bcrypt is None:
            raise KeyError("Bcrypt is not defined. Cannot generate bcrypt passwords!")
        if rounds_log == None:
            self._check_for_known_security_risks()
        if not password:
            raise ValueError("Password must be non-empty.")

        if rounds_log is None:
            rounds_log = self._bcrypt_log_rounds

        b_password = self._to_bytes(password)
        b_prefix = self._to_bytes(self._bcrypt_prefix)

        method_prefix = "bcrypt"

        if self._bcrypt_handle_long_passwords:
            hash_function = self._bcrypt_long_password_hash
            method_prefix += f":{hash_function}"
            b_password = self._hash_long_password_for_bcrypt(
                password=b_password, hash_function_name=hash_function
            )

        bcrypt_salt = self._bcrypt.gensalt(rounds=rounds_log, prefix=b_prefix)
        password_hash = self._bcrypt.hashpw(password=b_password, salt=bcrypt_salt)
        return method_prefix + password_hash.decode("utf-8")

    def generate_pbkdf2_password_hash(self, password: str, rounds: int = None) -> str:
        """Generate a PBKDF2 password hash.

        Args:
            password (str): the password to hash
            rounds (int, optional): The number of (linear!) rounds for the PBKDF2 algorithm. Defaults to current settings.

        Raises:
            ValueError: if password is empty or None
            SecurityError: if the current password settings pose a security risk and rounds is None

        Returns:
            str: the password hash to be stored in the db
        """
        if rounds is None:
            self._check_for_known_security_risks()
        if not password:
            raise ValueError("Password must be non-empty.")

        if rounds is None:
            rounds = self._pbkdf2_rounds

        hash_method = f"pbkdf2:{self._pbkdf2_hash_function}:{rounds}"
        password_hash = generate_password_hash(
            password=password, method=hash_method, salt_length=self._pbkdf2_salt_length
        )
        return password_hash

    def generate_password_hash(
        self, password: str, password_hash_algorithm: str = None
    ) -> str:
        """Generate a password hash with the current settings.

        Args:
            password (str): the password to hash
            password_hash_algorithm (str, optional): either "bcrypt" or "pbkdf2". Defaults to None.

        Raises:
            KeyError: if bcrypt is not defined

        Returns:
            str: the password hash that can be stored in the db
        """
        self._check_for_known_security_risks()
        if password_hash_algorithm is None:
            password_hash_algorithm = self._password_hash_algorithm
        if password_hash_algorithm == "bcrypt":
            return self.generate_bcrypt_password_hash(password)

        if password_hash_algorithm == "pbkdf2" or True:
            return self.generate_pbkdf2_password_hash(password)

    def check_bcrypt_password_hash(self, pw_hash: str, password: str) -> bool:
        """Check if a bcrypt password hash matches the given password.

        Args:
            pw_hash (str): the password hash generated by generate_password_hash
            password (str): the password to check

        Raises:
            KeyError: if bcrypt is not defined

        Returns:
            bool: True is the password matches, False in any other case
        """
        if self._bcrypt is None:
            raise KeyError("Bcrypt is not defined. Cannot generate bcrypt passwords!")
        if pw_hash is None or password is None:
            return False

        begin = pw_hash.index("$")
        prefix, pw_hash = pw_hash[:begin], pw_hash[begin:]

        b_password = self._to_bytes(password)
        b_pw_hash = self._to_bytes(pw_hash)

        if ":" in prefix:
            _, hash_function = prefix.split(":")
            try:
                b_password = self._hash_long_password_for_bcrypt(
                    b_password, hash_function_name=hash_function
                )
            except ValueError:
                return False

        return self._bcrypt.checkpw(password=b_password, hashed_password=b_pw_hash)

    def check_pbkdf2_password_hash(self, pw_hash: str, password: str) -> bool:
        """Check i a pbkdf2 password hash matches the given password.

        Args:
            pw_hash (str): the password hash generated by generate_password_hash
            password (str): the password to check

        Returns:
            bool: True is the password matches, False in any other case
        """
        if pw_hash is None or password is None:
            return False

        return check_password_hash(pwhash=pw_hash, password=password)

    def check_password_hash(self, pw_hash: str, password: str):
        """Check if a password hash matches the given password.

        Args:
            pw_hash (str): the password hash generated by generate_password_hash
            password (str): the password to check

        Raises:
            KeyError: if bcrypt is not defined and the password hash was generated with the bcrypt algorithm

        Returns:
            bool: True if the password matches, False in any other case
        """
        if pw_hash is None or password is None:
            return False

        if pw_hash.startswith("bcrypt"):
            return self.check_bcrypt_password_hash(pw_hash=pw_hash, password=password)

        if pw_hash.startswith("pbkdf2"):
            return self.check_pbkdf2_password_hash(pw_hash=pw_hash, password=password)

        return False

    def needs_rehash(
        self, pw_hash: str, ignore_password_hash_algorithm: bool = False
    ) -> bool:
        """Check if the password hash is outdated.

        Args:
            pw_hash (str): the password hash generated by generate_password_hash
            ignore_password_hash_algorithm (bool, optional): wether to ignore the password hashing algorithm ("bcrypt" or "pbkdf2"). Defaults to False.

        Returns:
            bool: True if the password hash was generated with different settings ('!=' not '<='!) than the current setting
        """
        if (
            not pw_hash.startswith(self._password_hash_algorithm)
            and not ignore_password_hash_algorithm
        ):
            return True

        if pw_hash.startswith("pbkdf2"):
            expected_prefix = f"pbkdf2:{self._pbkdf2_hash_function}:{self._pbkdf2_rounds}"
            prefix, _ = pw_hash.split("$", maxsplit=1)
            if prefix != expected_prefix:
                return True

        if pw_hash.startswith("bcrypt"):
            expected_prefix = (
                "bcrypt"
                + (
                    f":{self._bcrypt_long_password_hash}"
                    if self._bcrypt_handle_long_passwords
                    else ""
                )
                + f"${self._bcrypt_prefix}${self._bcrypt_log_rounds}"
            )
            *prefix_parts, _ = pw_hash.split("$", maxsplit=3)
            prefix = "$".join(prefix_parts)
            if prefix != expected_prefix:
                return True

        return False

    def check_current_settings(self) -> bool:
        """Check the current password hashing settings for problems.

        Hashes a calibration password 10 times with the current settings.
        If the fastest time is < 0.1 seconds or the slowest time is > 2 seconds
        the settings point to a severe security or usability problem. See the
        log output for more information.

        The method also sets 'settings_ok' to the output of this method and
        'security_risk' if the settings point to a security risk.

        Returns:
            bool: False if the current settings lead to a security or usability problem, True if the settings are ok
        """
        from time import perf_counter_ns as time_ns

        if self._app:
            rounds = (
                self._bcrypt_log_rounds
                if self._password_hash_algorithm
                else self._pbkdf2_rounds
            )
            self._app.logger.info(
                "Checking current password settings for possible security issues.\n"
                f"\tCurrent algorithm: '{self._password_hash_algorithm}' Current rounds: {rounds}"
            )

        self.security_risk = False  # reset security_risk flag
        calibration_password = "password"
        results = []

        for i in range(10):
            start = time_ns()
            self.generate_password_hash(password=calibration_password)
            end = time_ns()
            results.append(end - start)

        min_time = min(results) / (10**9)
        max_time = max(results) / (10**9)

        if min_time < 0.1:
            if self._app:
                self._app.logger.critical(
                    f"Password hashing took {min_time} seconds (less than 0.1s).\n"
                    "\tThis is a security risk!\n"
                    "\tConsider changing the rounds parameter of the password hashing algorithm."
                )
            self.settings_ok = False
            self.security_risk = True
            return False
        if min_time < 0.3:
            if self._app:
                self._app.logger.warning(
                    f"Password hashing took {min_time} seconds (less than 0.3s).\n"
                    "\tThis is may be a security risk!\n"
                    "\tConsider changing the rounds parameter of the password hashing algorithm."
                )
        if max_time > 0.8 and max_time < 2 and self._app:
            self._app.logger.warning(
                f"Password hashing took {min_time} seconds (more than 0.8s).\n"
                "\tThis is good for security but can be bad user experience."
            )
        if max_time > 2:
            if self._app:
                self._app.logger.error(
                    f"Password hashing took {min_time} seconds (more than 2s).\n"
                    "\tThis is very good for security but also bad user experience!"
                )
            self.settings_ok = False
            self.security_risk = False
            return False
        if self._app:
            self._app.logger.info(
                f"The current password settings are ok. Min time to hash: {min_time}s Max time to hash: {max_time}s"
            )
        self.settings_ok = True
        self.security_risk = False
        return True

    def calibrate(self, echo_results: bool = False) -> Dict[str, Dict[int, List[int]]]:
        """Generate calibration data for all supported password hashing algorithms (warning: slow!).

        Generate calibration data for the supported alforithm by hashing a
        calibration password 10 times with varying settings for the rounds
        parameter of the algorithms.

        The parameters for the algorithms should be chosen such that hashing a
        password takes > 0.1 (ideally > 0.3) seconds. The higher this value the
        slower a brute force attack will be.

        For usability the password hashing time should not exceed 0.8 seconds as
        this also influences how fast a password can be checked against an
        existing hash because the password needs to be hashed again. This will
        directly influence the time needed for a successful login!

        Args:
            echo_results (bool, optional): if True results are echoed to console immediately. Defaults to False.

        Returns:
            Dict[str, Dict[int, List[int]]]: a dict containing the raw results.
                    The outer dict is a mapping from 'algorithm' to 'results'.
                    The inner dict is a mapping from parameters to timings.
                    The timings are in ns (nanoseconds).
        """
        from time import perf_counter_ns as time_ns

        calibration_password = "password"

        results_bcrypt = {}

        if self._bcrypt:

            if echo_results:
                click.echo("\nResults Bcrypt:")

            for rounds in range(4, 100):
                timings = []
                for i in range(10):
                    start = time_ns()
                    self.generate_bcrypt_password_hash(
                        password=calibration_password, rounds_log=rounds
                    )
                    end = time_ns()
                    timings.append(end - start)
                results_bcrypt[rounds] = timings
                if echo_results:
                    min_time = min(timings) / (10**9)
                    max_time = max(timings) / (10**9)
                    click.echo(
                        f"Log Rounds {rounds: 4}: Min {min_time:<8.3} s  Max {max_time:<8.3} s"
                    )
                if max(timings) > 1 * (10**9):
                    break

        if echo_results:
            click.echo("\nResults PBKDF2:")

        results_pbkdf2 = {}
        rounds_iterator = chain(
            (DEFAULT_PBKDF2_ITERATIONS,),
            map(
                lambda x: mul(*x),
                zip(cycle([1, 2, 5]), [10 ** (i // 3) for i in range(5 * 3, 30 * 3)]),
            ),
        )

        for rounds in rounds_iterator:
            timings = []
            for i in range(10):
                start = time_ns()
                self.generate_pbkdf2_password_hash(
                    password=calibration_password, rounds=rounds
                )
                end = time_ns()
                timings.append(end - start)
            results_pbkdf2[rounds] = timings
            if echo_results:
                min_time = min(timings) / (10**9)
                max_time = max(timings) / (10**9)
                click.echo(
                    f"Rounds {rounds:13_}: Min {min_time:<6.3} s  Max {max_time:<6.3} s"
                )
            if max(timings) > 1 * (10**9):
                break

        results = {
            "pbkdf2": results_pbkdf2,
        }
        if results_bcrypt:
            results["bcrypt"] = results_bcrypt

        return results


FLASK_PASSWORD = FlaskPassword()


# blueprint to hold cli
PASSWORD_CLI_BLP = Blueprint("password_cli", __name__, cli_group="passwords")
PASSWORD_CLI = PASSWORD_CLI_BLP.cli  # expose as attribute for autodoc generation


@PASSWORD_CLI.command("check-settings")
@with_appcontext
def check_current_settings():
    """Check current password settings for security and usability problems."""
    click.echo("\nChecking current password settings:\n")
    settings_ok = FLASK_PASSWORD.check_current_settings()
    if settings_ok:
        click.echo("\nCurrent password settings are ok.\n")
    else:
        click.echo(
            "\nCurrent password settings are bad! See log output for more details.\n"
        )


@PASSWORD_CLI.command("calibrate")
def generate_calibration_data():
    """Generate calibration data to find good password settings."""
    click.echo("\nGenerating calibration data for password settings:\n")
    data = FLASK_PASSWORD.calibrate(True)
    click.echo("\nDetermining good settings from calibration results:\n")

    min_threshold_ns = 0.2 * (10**9)
    max_threshold_ns = 1.2 * (10**9)

    for key, name in (("bcrypt", "Bcrypt"), ("pbkdf2", "PBKDF2")):
        calibration_data = data.get(key)
        if not calibration_data:
            continue
        good_rounds_settings = []
        for rounds, timings in calibration_data.items():
            if min(timings) > min_threshold_ns and max(timings) < max_threshold_ns:
                good_rounds_settings.append(rounds)
        if good_rounds_settings:
            if len(good_rounds_settings) == 1:
                click.echo(
                    f"{name} should be set to around {good_rounds_settings[0]:_} rounds."
                )
            else:
                click.echo(
                    f"{name} should be set between {min(good_rounds_settings):_} and {max(good_rounds_settings):_} rounds."
                )
        else:
            click.echo("could not detemine good settings for {name}.")


@PASSWORD_CLI.command("list-settings")
@with_appcontext
def test_available_settings():
    """List all available password hashing settings (except round numbers)."""
    click.echo("\nListing all available pasword hashing settings:\n")
    algorithms: List[Tuple[str, str]] = [("pbkdf2", "PBKDF2")]
    if FLASK_PASSWORD._bcrypt is not None:
        algorithms.append(("bcrypt", "Bcrypt"))

    click.echo("Available algorithms:")

    for algorithm, name in algorithms:
        click.echo(f"\tAlgorithm {name} (PASSWORD_HASH_ALGORITHM='{algorithm}')")

    click.echo("Available hash functions:")
    for function in sorted(FLASK_PASSWORD._ALLOWED_PASSWORD_HASH_FUNCTIONS):
        setting_string = f"'{function}'"
        click.echo(
            f"\tHash function {function:<9} (PBKDF2_HASH_FUNCTION={setting_string:<11}  or  BCRYPT_LONG_PASSWORDS_HASH={setting_string:<11}  with  BCRYPT_HANDLE_LONG_PASSWORDS=True)"
        )


def register_password_helper(app: Flask):
    """Register FLASK_PASSWORD  with the current app to load the settings and register th cli."""
    FLASK_PASSWORD.init_app(app)
    app.register_blueprint(PASSWORD_CLI_BLP)
    app.logger.info("Registered Passwords CLI blueprint.")
