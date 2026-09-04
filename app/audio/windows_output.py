import ctypes
import sys
import uuid
from dataclasses import asdict, dataclass


class WindowsAudioOutputError(RuntimeError):
    pass


@dataclass(frozen=True)
class AudioEndpoint:

    name: str
    active: bool
    form_factor: str | None = None

    def as_dict(self):

        return asdict(self)


class _GUID(ctypes.Structure):

    _fields_ = [
        ("data1", ctypes.c_ulong),
        ("data2", ctypes.c_ushort),
        ("data3", ctypes.c_ushort),
        ("data4", ctypes.c_ubyte * 8),
    ]

    @classmethod
    def from_text(cls, value):

        guid = cls()
        raw = uuid.UUID(value).bytes_le
        ctypes.memmove(ctypes.byref(guid), raw, len(raw))
        return guid


class _PROPERTYKEY(ctypes.Structure):

    _fields_ = [
        ("fmtid", _GUID),
        ("pid", ctypes.c_ulong),
    ]


class _PROPVARIANT_VALUE(ctypes.Union):

    _fields_ = [
        ("signed_value", ctypes.c_long),
        ("unsigned_value", ctypes.c_ulong),
        ("wide_string", ctypes.c_wchar_p),
        ("pointer", ctypes.c_void_p),
    ]


class _PROPVARIANT(ctypes.Structure):

    _anonymous_ = ("value",)
    _fields_ = [
        ("variant_type", ctypes.c_ushort),
        ("reserved1", ctypes.c_ushort),
        ("reserved2", ctypes.c_ushort),
        ("reserved3", ctypes.c_ushort),
        ("value", _PROPVARIANT_VALUE),
    ]


class WindowsAudioOutput:

    CLSID_MMDEVICE_ENUMERATOR = _GUID.from_text(
        "bcde0395-e52f-467c-8e3d-c4579291692e"
    )
    IID_IMMDEVICE_ENUMERATOR = _GUID.from_text(
        "a95664d2-9614-4f35-a746-de8db63617e6"
    )
    FRIENDLY_NAME = _PROPERTYKEY(
        _GUID.from_text(
            "a45c254e-df1c-4efd-8020-67d146a850e0"
        ),
        14,
    )
    ENDPOINT_FORM_FACTOR = _PROPERTYKEY(
        _GUID.from_text(
            "1da5d803-d492-4edd-8c23-e0c0ffe7c245"
        ),
        0,
    )

    FORM_FACTORS = {
        0: "Remote network device",
        1: "Speakers",
        2: "Line output",
        3: "Headphones",
        4: "Microphone",
        5: "Headset",
        6: "Handset",
        7: "Digital passthrough",
        8: "S/PDIF",
        9: "HDMI/display audio",
    }

    DEVICE_STATE_ACTIVE = 0x00000001
    E_RENDER = 0
    E_MULTIMEDIA = 1
    CLSCTX_ALL = 23
    STGM_READ = 0
    VT_LPWSTR = 31
    VT_I4 = 3
    VT_UI4 = 19
    RPC_E_CHANGED_MODE = -2147417850

    def __init__(self, platform=None):

        self.platform = platform or sys.platform

    @staticmethod
    def _method(interface, index, result_type, *argument_types):

        table = ctypes.cast(
            interface,
            ctypes.POINTER(
                ctypes.POINTER(ctypes.c_void_p)
            ),
        ).contents
        address = table[index]
        prototype = ctypes.WINFUNCTYPE(
            result_type,
            ctypes.c_void_p,
            *argument_types,
        )
        return prototype(address)

    @staticmethod
    def _succeeded(result):

        return int(result) >= 0

    @classmethod
    def _require_success(cls, result):

        if not cls._succeeded(result):

            raise WindowsAudioOutputError(
                "Windows could not read the default audio output."
            )

    @classmethod
    def _release(cls, interface):

        if interface and interface.value:

            try:

                cls._method(
                    interface,
                    2,
                    ctypes.c_ulong,
                )(interface)

            except (OSError, ValueError, TypeError):

                pass

    @classmethod
    def _property(cls, ole32, store, key):

        value = _PROPVARIANT()
        get_value = cls._method(
            store,
            5,
            ctypes.c_long,
            ctypes.POINTER(_PROPERTYKEY),
            ctypes.POINTER(_PROPVARIANT),
        )
        cls._require_success(
            get_value(
                store,
                ctypes.byref(key),
                ctypes.byref(value),
            )
        )

        try:

            if value.variant_type == cls.VT_LPWSTR:

                return value.wide_string

            if value.variant_type in {
                cls.VT_I4,
                cls.VT_UI4,
            }:

                return int(
                    value.signed_value
                    if value.variant_type == cls.VT_I4
                    else value.unsigned_value
                )

            return None

        finally:

            ole32.PropVariantClear(
                ctypes.byref(value)
            )

    def default_endpoint(self):

        if self.platform != "win32":

            raise WindowsAudioOutputError(
                "Windows audio output is available only on Windows."
            )

        ole32 = ctypes.OleDLL("ole32")
        ole32.CoInitializeEx.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
        ]
        ole32.CoInitializeEx.restype = ctypes.c_long
        ole32.CoCreateInstance.argtypes = [
            ctypes.POINTER(_GUID),
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.POINTER(_GUID),
            ctypes.POINTER(ctypes.c_void_p),
        ]
        ole32.CoCreateInstance.restype = ctypes.c_long
        ole32.PropVariantClear.argtypes = [
            ctypes.POINTER(_PROPVARIANT)
        ]
        ole32.PropVariantClear.restype = ctypes.c_long

        initialised = ole32.CoInitializeEx(None, 2)

        if (
            not self._succeeded(initialised)
            and int(initialised) != self.RPC_E_CHANGED_MODE
        ):

            raise WindowsAudioOutputError(
                "Windows audio services are unavailable."
            )

        should_uninitialise = self._succeeded(initialised)
        enumerator = ctypes.c_void_p()
        device = ctypes.c_void_p()
        store = ctypes.c_void_p()

        try:

            self._require_success(
                ole32.CoCreateInstance(
                    ctypes.byref(
                        self.CLSID_MMDEVICE_ENUMERATOR
                    ),
                    None,
                    self.CLSCTX_ALL,
                    ctypes.byref(
                        self.IID_IMMDEVICE_ENUMERATOR
                    ),
                    ctypes.byref(enumerator),
                )
            )

            get_default = self._method(
                enumerator,
                4,
                ctypes.c_long,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_void_p),
            )
            self._require_success(
                get_default(
                    enumerator,
                    self.E_RENDER,
                    self.E_MULTIMEDIA,
                    ctypes.byref(device),
                )
            )

            get_state = self._method(
                device,
                6,
                ctypes.c_long,
                ctypes.POINTER(ctypes.c_ulong),
            )
            state = ctypes.c_ulong()
            self._require_success(
                get_state(device, ctypes.byref(state))
            )

            open_store = self._method(
                device,
                4,
                ctypes.c_long,
                ctypes.c_ulong,
                ctypes.POINTER(ctypes.c_void_p),
            )
            self._require_success(
                open_store(
                    device,
                    self.STGM_READ,
                    ctypes.byref(store),
                )
            )

            name = self._property(
                ole32,
                store,
                self.FRIENDLY_NAME,
            )
            form_factor_value = self._property(
                ole32,
                store,
                self.ENDPOINT_FORM_FACTOR,
            )

            if not name:

                raise WindowsAudioOutputError(
                    "Windows did not provide an audio output name."
                )

            return AudioEndpoint(
                name=str(name),
                active=bool(
                    state.value & self.DEVICE_STATE_ACTIVE
                ),
                form_factor=self.FORM_FACTORS.get(
                    form_factor_value,
                ),
            )

        except (OSError, ValueError, TypeError) as error:

            if isinstance(error, WindowsAudioOutputError):

                raise

            raise WindowsAudioOutputError(
                "Windows could not read the default audio output."
            ) from error

        finally:

            self._release(store)
            self._release(device)
            self._release(enumerator)

            if should_uninitialise:

                ole32.CoUninitialize()
