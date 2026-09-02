import ctypes
from ctypes import wintypes
import uuid

wlanapi = ctypes.WinDLL("wlanapi.dll")

# ------------------------------------------------------------
# Constants
# ------------------------------------------------------------

WLAN_MAX_PHY_TYPE_NUMBER = 8
WLAN_MAX_NAME_LENGTH = 256

# WLAN_INTERFACE_CAPABILITY
WLAN_INTERFACE_CAPABILITY_FLAG_REQUIRES_MANUAL_RESTART = 0x00000001
WLAN_INTERFACE_CAPABILITY_FLAG_HARDWARE_RADIO_STATE_CHANGE = 0x00000002
WLAN_INTERFACE_CAPABILITY_FLAG_MEDIA_STREAMING = 0x00000004
WLAN_INTERFACE_CAPABILITY_FLAG_SAFE_AUTO_CONFIG = 0x00000008
WLAN_INTERFACE_CAPABILITY_FLAG_HOTSPOT = 0x00000010
WLAN_INTERFACE_CAPABILITY_FLAG_POWER_MANAGEMENT = 0x00000020
WLAN_INTERFACE_CAPABILITY_FLAG_AIRPLANE_MODE = 0x00000040
WLAN_INTERFACE_CAPABILITY_FLAG_ANNOTATED = 0x00000080

# DOT11_PHY_TYPE values
PHY_TYPES = {
    0: "unknown",
    1: "FHSS",
    2: "DSSS",
    3: "IRBaseband",
    4: "OFDM",
    5: "HRDSSS",
    6: "ERP",
    7: "HT",
    8: "VHT",
    9: "DMG",
    10: "HE",
}

# ------------------------------------------------------------
# Structures
# ------------------------------------------------------------

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
        ("strInterfaceDescription", wintypes.WCHAR * WLAN_MAX_NAME_LENGTH),
        ("isState", wintypes.DWORD),
    ]


class WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
    _fields_ = [
        ("dwNumberOfItems", wintypes.DWORD),
        ("dwIndex", wintypes.DWORD),
        ("InterfaceInfo", WLAN_INTERFACE_INFO * 1),
    ]


class WLAN_INTERFACE_CAPABILITY(ctypes.Structure):
    _fields_ = [
        ("interfaceType", wintypes.DWORD),
        ("strProfileName", wintypes.WCHAR * WLAN_MAX_NAME_LENGTH),
        ("dwMaxDesiredSsidListSize", wintypes.DWORD),
        ("dwMaxDesiredBssidListSize", wintypes.DWORD),
        ("dwNumberOfSupportedPhys", wintypes.DWORD),
        ("dot11PhyTypes", wintypes.DWORD * WLAN_MAX_PHY_TYPE_NUMBER),
        ("dwNumberOfSupportedBands", wintypes.DWORD),
        ("dwMaxNumberOfProbeRequests", wintypes.DWORD),
        ("dwNumberOfSupportedReceiveAntenna", wintypes.DWORD),
        ("dwNumberOfSupportedTransmitAntenna", wintypes.DWORD),
        ("dwSupportedFeatureFlags", wintypes.DWORD),
    ]


# ------------------------------------------------------------
# API definitions
# ------------------------------------------------------------

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


WlanGetInterfaceCapability = wlanapi.WlanGetInterfaceCapability
WlanGetInterfaceCapability.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(GUID),
    wintypes.LPVOID,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.LPVOID),
    wintypes.LPVOID,
]
WlanGetInterfaceCapability.restype = wintypes.DWORD


WlanFreeMemory = wlanapi.WlanFreeMemory
WlanFreeMemory.argtypes = [wintypes.LPVOID]
WlanFreeMemory.restype = None


WlanCloseHandle = wlanapi.WlanCloseHandle
WlanCloseHandle.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
]
WlanCloseHandle.restype = wintypes.DWORD


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def guid_to_uuid(g):
    data = (
        int(g.Data1).to_bytes(4, "little") +
        int(g.Data2).to_bytes(2, "little") +
        int(g.Data3).to_bytes(2, "little") +
        bytes(g.Data4)
    )
    return str(uuid.UUID(bytes_le=data))


def feature_flags(value):
    flags = []

    known = {
        0x00000001: "REQUIRES_MANUAL_RESTART",
        0x00000002: "HARDWARE_RADIO_STATE_CHANGE",
        0x00000004: "MEDIA_STREAMING",
        0x00000008: "SAFE_AUTO_CONFIG",
        0x00000010: "HOTSPOT",
        0x00000020: "POWER_MANAGEMENT",
        0x00000040: "AIRPLANE_MODE",
        0x00000080: "ANNOTATED",
    }

    for bit, name in known.items():
        if value & bit:
            flags.append(name)

    return flags


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

handle = wintypes.HANDLE()
negotiated = wintypes.DWORD()

status = WlanOpenHandle(
    2,
    None,
    ctypes.byref(negotiated),
    ctypes.byref(handle),
)

print("WlanOpenHandle:", status)
print("Negotiated WLAN version:", negotiated.value)

if status != 0:
    raise SystemExit("WlanOpenHandle failed")

interfaces = ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)()

status = WlanEnumInterfaces(
    handle,
    None,
    ctypes.byref(interfaces),
)

print("WlanEnumInterfaces:", status)

if status != 0:
    WlanCloseHandle(handle, None)
    raise SystemExit("WlanEnumInterfaces failed")

count = interfaces.contents.dwNumberOfItems

print("Interfaces found:", count)
print()

for i in range(count):

    info = interfaces.contents.InterfaceInfo[i]

    guid = guid_to_uuid(info.InterfaceGuid)

    print("=" * 70)
    print("Interface:", info.strInterfaceDescription)
    print("GUID:", guid)
    print("State:", info.isState)
    print()

    capability_ptr = wintypes.LPVOID()
    data_size = wintypes.DWORD()

    status = WlanGetInterfaceCapability(
        handle,
        ctypes.byref(info.InterfaceGuid),
        None,
        ctypes.byref(data_size),
        ctypes.byref(capability_ptr),
        None,
    )

    print("WlanGetInterfaceCapability:", status)
    print("Capability data size:", data_size.value)

    if status != 0:
        print("Capability query failed.")
        continue

    cap = ctypes.cast(
        capability_ptr,
        ctypes.POINTER(WLAN_INTERFACE_CAPABILITY)
    ).contents

    print()
    print("Interface Type:", cap.interfaceType)
    print("Profile Name:", repr(cap.strProfileName))
    print("Max desired SSID list:", cap.dwMaxDesiredSsidListSize)
    print("Max desired BSSID list:", cap.dwMaxDesiredBssidListSize)

    print()
    print("Supported PHY count:", cap.dwNumberOfSupportedPhys)

    phy_count = min(
        cap.dwNumberOfSupportedPhys,
        WLAN_MAX_PHY_TYPE_NUMBER
    )

    for n in range(phy_count):
        phy = cap.dot11PhyTypes[n]
        print(
            f"  PHY {n}: {phy} -> {PHY_TYPES.get(phy, 'UNKNOWN')}"
        )

    print()
    print("Supported bands:", cap.dwNumberOfSupportedBands)
    print("Max probe requests:", cap.dwMaxNumberOfProbeRequests)
    print("Receive antennas:", cap.dwNumberOfSupportedReceiveAntenna)
    print("Transmit antennas:", cap.dwNumberOfSupportedTransmitAntenna)

    print()
    print(
        "Supported feature flags:",
        hex(cap.dwSupportedFeatureFlags)
    )

    names = feature_flags(cap.dwSupportedFeatureFlags)

    if names:
        for name in names:
            print("  +", name)
    else:
        print("  (none reported)")

    # IMPORTANT
    if cap.dwSupportedFeatureFlags & WLAN_INTERFACE_CAPABILITY_FLAG_HOTSPOT:
        print()
        print(">>> HOTSPOT CAPABILITY FLAG = YES <<<")
    else:
        print()
        print(">>> HOTSPOT CAPABILITY FLAG = NO <<<")

    WlanFreeMemory(capability_ptr)


WlanFreeMemory(interfaces)
WlanCloseHandle(handle, None)

print()
print("=" * 70)
print("DONE")