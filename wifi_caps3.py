import ctypes
from ctypes import wintypes
import uuid

wlanapi = ctypes.WinDLL("wlanapi.dll")

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]

class WLAN_INTERFACE_INFO(ctypes.Structure):
    _fields_ = [
        ("InterfaceGuid", GUID),
        ("strInterfaceDescription", wintypes.WCHAR * 256),
        ("isState", wintypes.DWORD),
    ]

class WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
    _fields_ = [
        ("dwNumberOfItems", wintypes.DWORD),
        ("dwIndex", wintypes.DWORD),
        ("InterfaceInfo", WLAN_INTERFACE_INFO * 1),
    ]


# ---------------------------------------------------------
# API definitions
# ---------------------------------------------------------

WlanOpenHandle = wlanapi.WlanOpenHandle
WlanOpenHandle.argtypes = [
    wintypes.DWORD,
    wintypes.LPVOID,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.HANDLE),
]
WlanOpenHandle.restype = wintypes.DWORD


WlanEnumInterfaces = wlanapi.WlanEnumInterfaces
WlanEnumInterfaces.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
    ctypes.POINTER(ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)),
]
WlanEnumInterfaces.restype = wintypes.DWORD


# KRITIK:
# ppData = PVOID*
WlanGetInterfaceCapability = wlanapi.WlanGetInterfaceCapability
WlanGetInterfaceCapability.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(GUID),
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(ctypes.c_void_p),
]
WlanGetInterfaceCapability.restype = wintypes.DWORD


WlanFreeMemory = wlanapi.WlanFreeMemory
WlanFreeMemory.argtypes = [ctypes.c_void_p]
WlanFreeMemory.restype = None


WlanCloseHandle = wlanapi.WlanCloseHandle
WlanCloseHandle.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
]
WlanCloseHandle.restype = wintypes.DWORD


# ---------------------------------------------------------
# Open WLAN
# ---------------------------------------------------------

handle = wintypes.HANDLE()
version = wintypes.DWORD()

status = WlanOpenHandle(
    2,
    None,
    ctypes.byref(version),
    ctypes.byref(handle)
)

print("WlanOpenHandle:", status)
print("Negotiated WLAN version:", version.value)

if status != 0:
    raise SystemExit


# ---------------------------------------------------------
# Enumerate
# ---------------------------------------------------------

interfaces = ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)()

status = WlanEnumInterfaces(
    handle,
    None,
    ctypes.byref(interfaces)
)

print("WlanEnumInterfaces:", status)

if status != 0:
    WlanCloseHandle(handle, 0)
    raise SystemExit


count = interfaces.contents.dwNumberOfItems

print("Interfaces found:", count)
print()


# ---------------------------------------------------------
# Capability
# ---------------------------------------------------------

for i in range(count):

    info = interfaces.contents.InterfaceInfo[i]

    print("=" * 70)
    print("Interface:", info.strInterfaceDescription)
    print("State:", info.isState)

    data_size = wintypes.DWORD(0)
    data_ptr = ctypes.c_void_p(None)

    status = WlanGetInterfaceCapability(
        handle,
        ctypes.byref(info.InterfaceGuid),
        0,
        ctypes.byref(data_size),
        ctypes.byref(data_ptr)
    )

    print("WlanGetInterfaceCapability:", status)
    print("Data size:", data_size.value)
    print("Data pointer:", hex(data_ptr.value or 0))

    if status != 0:
        continue

    if not data_ptr.value:
        print("ERROR: API returned NULL pointer")
        continue

    if data_size.value < 4 or data_size.value > 1024 * 1024:
        print("ERROR: suspicious buffer size")
        continue

    raw = ctypes.string_at(
        data_ptr.value,
        data_size.value
    )

    print()
    print("First 256 bytes:")

    for offset in range(0, min(len(raw), 256), 16):
        chunk = raw[offset:offset + 16]

        hex_part = " ".join(
            f"{b:02X}" for b in chunk
        )

        ascii_part = "".join(
            chr(b) if 32 <= b < 127 else "."
            for b in chunk
        )

        print(
            f"{offset:04X}  "
            f"{hex_part:<47}  "
            f"{ascii_part}"
        )

    WlanFreeMemory(data_ptr)


WlanFreeMemory(interfaces)
WlanCloseHandle(handle, 0)

print()
print("=" * 70)
print("DONE")