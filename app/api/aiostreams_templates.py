import base64
import ctypes
import json
import os
import re
import time
from ctypes import wintypes
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit

import requests


class TemplateUpdateError(RuntimeError):
    pass


class _DataBlob(ctypes.Structure):

    _fields_ = [
        ("size", wintypes.DWORD),
        ("data", ctypes.POINTER(ctypes.c_byte)),
    ]


class WindowsDataProtector:

    DESCRIPTION = "Orion AIOStreams session"
    UI_FORBIDDEN = 0x1

    @staticmethod
    def _blob(value):

        buffer = ctypes.create_string_buffer(value)

        return (
            _DataBlob(
                len(value),
                ctypes.cast(
                    buffer,
                    ctypes.POINTER(ctypes.c_byte),
                ),
            ),
            buffer,
        )

    def protect(self, value):

        if os.name != "nt":
            raise TemplateUpdateError(
                "Secure Windows credential storage is unavailable."
            )

        source, source_buffer = self._blob(value)
        output = _DataBlob()

        success = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(source),
            ctypes.c_wchar_p(self.DESCRIPTION),
            None,
            None,
            None,
            self.UI_FORBIDDEN,
            ctypes.byref(output),
        )

        del source_buffer

        if not success:
            raise ctypes.WinError()

        try:
            return ctypes.string_at(
                output.data,
                output.size,
            )
        finally:
            ctypes.windll.kernel32.LocalFree(
                output.data
            )

    def unprotect(self, value):

        if os.name != "nt":
            raise TemplateUpdateError(
                "Secure Windows credential storage is unavailable."
            )

        source, source_buffer = self._blob(value)
        output = _DataBlob()

        success = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(source),
            None,
            None,
            None,
            None,
            self.UI_FORBIDDEN,
            ctypes.byref(output),
        )

        del source_buffer

        if not success:
            raise ctypes.WinError()

        try:
            return ctypes.string_at(
                output.data,
                output.size,
            )
        finally:
            ctypes.windll.kernel32.LocalFree(
                output.data
            )


class AIOStreamsTemplateUpdates:

    TEMPLATE_ID = "tamtaro.complete"
    TEMPLATE_NAME = "Tamtaro Complete SEL Setup"
    TEMPLATE_URL = (
        "https://raw.githubusercontent.com/"
        "Tam-Taro/SEL-Filtering-and-Sorting/"
        "refs/heads/main/AIOStreams%20Templates/"
        "Tamtaro-complete-setup-template.json"
    )
    MAX_TEMPLATE_BYTES = 1024 * 1024
    CACHE_SECONDS = 60 * 60
    UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-"
        r"[0-9a-f]{4}-[0-9a-f]{4}-"
        r"[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    VERSION_PATTERN = re.compile(
        r"^(\d+)\.(\d+)\.(\d+)"
        r"(?:[-+][0-9A-Za-z.-]+)?$"
    )

    def __init__(
        self,
        state_path=None,
        protector=None,
        session_factory=None,
        clock=None,
    ):

        self.state_path = Path(
            state_path
            or Path("data")
            / "aiostreams_template_session.json"
        )
        self.protector = (
            protector
            or WindowsDataProtector()
        )
        self.session_factory = (
            session_factory
            or requests.Session
        )
        self.clock = clock or time.time
        self._remote_cache = None
        self._remote_cache_time = 0

    @staticmethod
    def _local_base_url(value):

        parsed = urlsplit(value)

        if (
            parsed.scheme != "http"
            or parsed.hostname
            not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username
            or parsed.password
        ):
            raise TemplateUpdateError(
                "AIOStreams must use a local HTTP address."
            )

        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                "",
                "",
                "",
            )
        ).rstrip("/")

    @classmethod
    def _version_tuple(cls, value):

        match = cls.VERSION_PATTERN.fullmatch(
            str(value or "")
        )

        if match is None:
            raise TemplateUpdateError(
                "The template reported an invalid version."
            )

        return tuple(
            int(part)
            for part in match.groups()
        )

    def _read_limited_json(self, response):

        response.raise_for_status()

        declared_size = response.headers.get(
            "Content-Length"
        )

        if declared_size:
            try:
                too_large = (
                    int(declared_size)
                    > self.MAX_TEMPLATE_BYTES
                )
            except ValueError as error:
                raise TemplateUpdateError(
                    "The template source returned an invalid size."
                ) from error

            if too_large:
                raise TemplateUpdateError(
                    "The template download was unexpectedly large."
                )

        chunks = []
        total = 0

        for chunk in response.iter_content(65536):
            total += len(chunk)

            if total > self.MAX_TEMPLATE_BYTES:
                raise TemplateUpdateError(
                    "The template download was unexpectedly large."
                )

            chunks.append(chunk)

        try:
            return json.loads(
                b"".join(chunks).decode("utf-8")
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise TemplateUpdateError(
                "The template download was not valid JSON."
            ) from error

    def remote_template(self, force=False):

        now = self.clock()

        if (
            not force
            and self._remote_cache is not None
            and now - self._remote_cache_time
            < self.CACHE_SECONDS
        ):
            return dict(self._remote_cache)

        session = self.session_factory()

        try:
            response = session.get(
                self.TEMPLATE_URL,
                timeout=15,
                stream=True,
                allow_redirects=True,
            )

            if (
                urlsplit(response.url).scheme
                != "https"
            ):
                raise TemplateUpdateError(
                    "The template source did not remain secure."
                )

            payload = self._read_limited_json(
                response
            )
        except TemplateUpdateError:
            raise
        except requests.RequestException as error:
            raise TemplateUpdateError(
                "Unable to reach the Tamtaro template source."
            ) from error
        finally:
            session.close()

        templates = (
            payload
            if isinstance(payload, list)
            else [payload]
        )

        selected = next(
            (
                item
                for item in templates
                if isinstance(item, dict)
                and isinstance(
                    item.get("metadata"),
                    dict,
                )
                and item["metadata"].get("id")
                == self.TEMPLATE_ID
            ),
            None,
        )

        if selected is None:
            raise TemplateUpdateError(
                "The expected Tamtaro template was not found."
            )

        metadata = selected["metadata"]
        version = str(metadata.get("version", ""))
        self._version_tuple(version)

        result = {
            "id": self.TEMPLATE_ID,
            "name": str(
                metadata.get("name")
                or self.TEMPLATE_NAME
            ),
            "version": version,
        }

        self._remote_cache = dict(result)
        self._remote_cache_time = now

        return result

    def _save_state(self, state):

        protected = self.protector.protect(
            state["session_token"].encode("utf-8")
        )

        payload = {
            "version": 1,
            "uuid": state["uuid"],
            "session_token": base64.b64encode(
                protected
            ).decode("ascii"),
            "expires_at": int(state["expires_at"]),
            "applied_version": state.get(
                "applied_version"
            ),
        }

        self.state_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = self.state_path.with_suffix(
            self.state_path.suffix + ".tmp"
        )

        temporary.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

        os.replace(
            temporary,
            self.state_path,
        )

    def _load_state(self):

        if not self.state_path.is_file():
            return None

        try:
            payload = json.loads(
                self.state_path.read_text(
                    encoding="utf-8"
                )
            )

            token = self.protector.unprotect(
                base64.b64decode(
                    payload["session_token"],
                    validate=True,
                )
            ).decode("utf-8")

            uuid = str(payload["uuid"])

            if not self.UUID_PATTERN.fullmatch(uuid):
                raise ValueError("invalid UUID")

            return {
                "uuid": uuid,
                "session_token": token,
                "expires_at": int(
                    payload["expires_at"]
                ),
                "applied_version": (
                    payload.get("applied_version")
                ),
            }
        except Exception as error:
            raise TemplateUpdateError(
                "The saved AIOStreams link could not be read."
            ) from error

    def unlink(self, base_url=None):

        state = None

        try:
            state = self._load_state()
        except TemplateUpdateError:
            pass

        if state and base_url:
            session = self.session_factory()

            try:
                session.delete(
                    f"{self._local_base_url(base_url)}"
                    "/api/v1/user/session",
                    cookies={
                        "aiostreams.config-session": (
                            state["session_token"]
                        )
                    },
                    timeout=10,
                )
            except (
                TemplateUpdateError,
                requests.RequestException,
            ):
                pass
            finally:
                session.close()

        if self.state_path.exists():
            self.state_path.unlink()

    @staticmethod
    def _applied_version(user_data):

        entries = user_data.get(
            "appliedTemplates",
            [],
        )

        return next(
            (
                str(entry.get("version"))
                for entry in entries
                if isinstance(entry, dict)
                and entry.get("id")
                == AIOStreamsTemplateUpdates.TEMPLATE_ID
                and entry.get("version")
            ),
            None,
        )

    @staticmethod
    def _response_user_data(response):

        response.raise_for_status()

        try:
            payload = response.json()
        except (ValueError, json.JSONDecodeError) as error:
            raise TemplateUpdateError(
                "AIOStreams returned an invalid response."
            ) from error

        if not isinstance(payload, dict):
            raise TemplateUpdateError(
                "AIOStreams returned an invalid response."
            )

        data = payload.get("data")

        if not isinstance(data, dict):
            raise TemplateUpdateError(
                "AIOStreams returned an invalid response."
            )

        user_data = data.get("userData")

        if not isinstance(user_data, dict):
            raise TemplateUpdateError(
                "AIOStreams did not return the saved configuration."
            )

        return user_data

    def link(self, base_url, uuid, password):

        base_url = self._local_base_url(base_url)
        uuid = str(uuid or "").strip()

        if not self.UUID_PATTERN.fullmatch(uuid):
            raise TemplateUpdateError(
                "Enter a valid AIOStreams configuration UUID."
            )

        if not password:
            raise TemplateUpdateError(
                "Enter the AIOStreams configuration password."
            )

        session = self.session_factory()

        try:
            auth = (uuid, password)
            config_response = session.get(
                f"{base_url}/api/v1/user",
                params={"uuid": uuid, "raw": "true"},
                auth=auth,
                timeout=15,
            )
            user_data = self._response_user_data(
                config_response
            )

            login_response = session.post(
                f"{base_url}/api/v1/user/session",
                params={"uuid": uuid},
                auth=auth,
                json={"remember": True},
                timeout=15,
            )
            login_response.raise_for_status()
            login_payload = login_response.json()

            if not isinstance(login_payload, dict):
                raise TemplateUpdateError(
                    "AIOStreams returned an invalid session."
                )

            login_data = login_payload.get("data")

            if not isinstance(login_data, dict):
                raise TemplateUpdateError(
                    "AIOStreams returned an invalid session."
                )

            token = session.cookies.get(
                "aiostreams.config-session"
            )

            expires_at = login_data.get(
                "expiresAt"
            )

            if not token or not expires_at:
                raise TemplateUpdateError(
                    "AIOStreams did not create a remembered session."
                )

            state = {
                "uuid": uuid,
                "session_token": token,
                "expires_at": int(expires_at),
                "applied_version": self._applied_version(
                    user_data
                ),
            }

            self._save_state(state)

            return state
        except TemplateUpdateError:
            raise
        except requests.HTTPError as error:
            status = error.response.status_code

            if status in {401, 403, 404}:
                message = (
                    "AIOStreams rejected the UUID or password."
                )
            else:
                message = (
                    "AIOStreams could not link the configuration."
                )

            raise TemplateUpdateError(
                message
            ) from error
        except (requests.RequestException, ValueError) as error:
            raise TemplateUpdateError(
                "AIOStreams could not link the configuration."
            ) from error
        finally:
            session.close()

    def _refresh_linked_config(
        self,
        base_url,
        state,
    ):

        session = self.session_factory()

        try:
            response = session.get(
                f"{base_url}/api/v1/user",
                params={
                    "uuid": state["uuid"],
                    "raw": "true",
                },
                cookies={
                    "aiostreams.config-session": (
                        state["session_token"]
                    )
                },
                timeout=15,
            )

            user_data = self._response_user_data(
                response
            )

            state["applied_version"] = (
                self._applied_version(user_data)
            )

            renewed = response.cookies.get(
                "aiostreams.config-session"
            )

            if renewed:
                state["session_token"] = renewed

            self._save_state(state)

            return state
        except requests.HTTPError as error:
            if error.response.status_code in {
                401,
                403,
            }:
                raise TemplateUpdateError(
                    "The AIOStreams link has expired. Link it again."
                ) from error

            raise TemplateUpdateError(
                "AIOStreams could not verify the linked configuration."
            ) from error
        except requests.RequestException as error:
            raise TemplateUpdateError(
                "AIOStreams could not verify the linked configuration."
            ) from error
        finally:
            session.close()

    def status(self, base_url, force=False):

        result = {
            "linked": False,
            "state": "unlinked",
            "name": self.TEMPLATE_NAME,
            "installed_version": None,
            "latest_version": None,
            "update_available": False,
            "message": (
                "Link your saved AIOStreams configuration once "
                "to check Tamtaro template updates."
            ),
        }

        try:
            remote = self.remote_template(
                force=force
            )
            result["name"] = remote["name"]
            result["latest_version"] = (
                remote["version"]
            )
        except TemplateUpdateError as error:
            result["state"] = "unavailable"
            result["message"] = str(error)

        try:
            state = self._load_state()
        except TemplateUpdateError as error:
            result["state"] = "relink"
            result["message"] = str(error)
            return result

        if state is None:
            return result

        result["linked"] = True

        try:
            base_url = self._local_base_url(
                base_url
            )

            if force or not state.get(
                "applied_version"
            ):
                state = self._refresh_linked_config(
                    base_url,
                    state,
                )
        except TemplateUpdateError as error:
            result["state"] = "relink"
            result["message"] = str(error)
            return result

        installed = state.get("applied_version")
        result["installed_version"] = installed

        if not installed:
            result["state"] = "unknown"
            result["message"] = (
                "This configuration does not record an applied "
                "Tamtaro Complete template version."
            )
            return result

        if result["latest_version"] is None:
            return result

        try:
            update_available = (
                self._version_tuple(
                    result["latest_version"]
                )
                > self._version_tuple(installed)
            )
        except TemplateUpdateError as error:
            result["state"] = "unavailable"
            result["message"] = str(error)
            return result

        result["update_available"] = (
            update_available
        )
        result["state"] = (
            "available"
            if update_available
            else "current"
        )
        result["message"] = (
            f"Tamtaro {result['latest_version']} is available."
            if update_available
            else "The Tamtaro template is up to date."
        )

        return result

    def update_launch(self, base_url, browser_host):

        base_url = self._local_base_url(base_url)
        status = self.status(
            base_url,
            force=True,
        )

        if status["update_available"] is not True:
            raise TemplateUpdateError(
                status["message"]
            )

        state = self._load_state()

        if state is None:
            raise TemplateUpdateError(
                "Link AIOStreams before opening the update."
            )

        parsed = urlsplit(base_url)
        host = str(browser_host or "").strip()

        if host not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            host = parsed.hostname

        if ":" in host and not host.startswith("["):
            host = f"[{host}]"

        netloc = host

        if parsed.port:
            netloc = f"{host}:{parsed.port}"

        query = urlencode(
            {
                "template": self.TEMPLATE_URL,
                "templateId": self.TEMPLATE_ID,
            }
        )

        target = urlunsplit(
            (
                "http",
                netloc,
                "/stremio/configure",
                query,
                "",
            )
        )

        return {
            "target": target,
            "session_token": state[
                "session_token"
            ],
            "expires_at": state["expires_at"],
        }
