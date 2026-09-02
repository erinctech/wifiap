import ctypes
from ctypes import wintypes
import uuid

wlanapi = ctypes.WinDLL("wlanapi.dll")


# ============================================================
# Structures
# ============================================================

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


# Microsoft:
#
# typedef struct _WLAN_INTERFACE_CAPABILITY {
#     WLAN_INTERFACE_TYPE interfaceType;
#     BOOL bDot11DSupported;
#     DWORD dwMaxDesiredSsidListSize;
#     DWORD dwMaxDesiredBssidListSize;
#     DWORD dwNumberOfSupportedPhys;
#     DOT11_PHY_TYPE dot11PhyTypes[WLAN_MAX_PHY_INDEX];
# } WLAN_INTERFACE_CAPABILITY;
#
# WLAN_MAX_PHY_INDEX = 64

class WLAN_INTERFACE_CAPABILITY(ctypes.Structure):
    _fields_ = [
        ("interfaceType", wintypes.DWORD),
        ("bDot11DSupported", wintypes.BOOL),
        ("dwMaxDesiredSsidListSize", wintypes.DWORD),
        ("dwMaxDesiredBssidListSize", wintypes.DWORD),
        ("dwNumberOfSupportedPhys", wintypes.DWORD),
        ("dot11PhyTypes", wintypes.DWORD * 64),
    ]


# ============================================================
# PHY names
# ============================================================

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


# ============================================================
# API
# ============================================================

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


# IMPORTANT:
#
# DWORD WlanGetInterfaceCapability(
#     HANDLE hClientHandle,
#     const GUID *pInterfaceGuid,
#     PVOID pReserved,
#     PWLAN_INTERFACE_CAPABILITY *ppCapability
# );

WlanGetInterfaceCapability = wlanapi.WlanGetInterfaceCapability
WlanGetInterfaceCapability.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(GUID),
    wintypes.LPVOID,
    ctypes.POINTER(ctypes.POINTER(WLAN_INTERFACE_CAPABILITY)),
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


# ============================================================
# Open
# ============================================================

handle = wintypes.HANDLE()
version = wintypes.DWORD()

status = WlanOpenHandle(
    2,
    None,
    ctypes.byref(version),
    ctypes.byref(handle),
)

print("WlanOpenHandle:", status)
print("Negotiated WLAN version:", version.value)

if status != 0:
    raise SystemExit


# ============================================================
# Enumerate
# ============================================================

interfaces = ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)()

status = WlanEnumInterfaces(
    handle,
    None,
    ctypes.byref(interfaces),
)

print("WlanEnumInterfaces:", status)

if status != 0:
    WlanCloseHandle(handle, None)
    raise SystemExit


count = interfaces.contents.dwNumberOfItems

print("Interfaces found:", count)
print()


# ============================================================
# Capability
# ============================================================

for i in range(count):

    info = interfaces.contents.InterfaceInfo[i]

    guid_bytes = (
        int(info.InterfaceGuid.Data1).to_bytes(4, "little") +
        int(info.InterfaceGuid.Data2).to_bytes(2, "little") +
        int(info.InterfaceGuid.Data3).to_bytes(2, "little") +
        bytes(info.InterfaceGuid.Data4)
    )

    guid = uuid.UUID(bytes_le=guid_bytes)

    print("=" * 70)
    print("Interface:", info.strInterfaceDescription)
    print("GUID:", guid)
    print("State:", info.isState)
    print()

    capability = ctypes.POINTER(
        WLAN_INTERFACE_CAPABILITY
    )()

    status = WlanGetInterfaceCapability(
        handle,
        ctypes.byref(info.InterfaceGuid),
        None,
        ctypes.byref(capability),
    )

    print("WlanGetInterfaceCapability:", status)
    print("Capability pointer:", hex(ctypes.addressof(capability.contents))
          if capability else "NULL")

    if status != 0:
        print("Capability query failed.")
        continue

    if not capability:
        print("ERROR: NULL capability pointer")
        continue

    cap = capability.contents

    print()
    print("interfaceType:", cap.interfaceType)
    print("802.11d supported:", bool(cap.bDot11DSupported))
    print("Max desired SSID list:",
          cap.dwMaxDesiredSsidListSize)
    print("Max desired BSSID list:",
          cap.dwMaxDesiredBssidListSize)

    print()
    print("Supported PHY count:",
          cap.dwNumberOfSupportedPhys)

    phy_count = min(
        cap.dwNumberOfSupportedPhys,
        64
    )

    for n in range(phy_count):
        phy = cap.dot11PhyTypes[n]

        print(
            f"  PHY {n}: {phy} "
            f"({PHY_TYPES.get(phy, 'UNKNOWN')})"
        )

    print()

    WlanFreeMemory(capability)


# ============================================================
# Cleanup
# ============================================================

WlanFreeMemory(interfaces)
WlanCloseHandle(handle, None)

print("=" * 70)
print("DONE")