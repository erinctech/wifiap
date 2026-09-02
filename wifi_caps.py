import ctypes
import ctypes.wintypes as wt
import uuid

wlanapi = ctypes.WinDLL("wlanapi.dll")

DWORD = wt.DWORD
HANDLE = wt.HANDLE
LPVOID = wt.LPVOID


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class WLAN_INTERFACE_INFO(ctypes.Structure):
    _fields_ = [
        ("InterfaceGuid", GUID),
        ("strInterfaceDescription", wt.WCHAR * 256),
        ("isState", DWORD),
    ]


class WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
    _fields_ = [
        ("dwNumberOfItems", DWORD),
        ("dwIndex", DWORD),
        ("InterfaceInfo", WLAN_INTERFACE_INFO * 1),
    ]


class DOT11_SSID(ctypes.Structure):
    _fields_ = [
        ("uSSIDLength", DWORD),
        ("ucSSID", ctypes.c_ubyte * 32),
    ]


class WLAN_RADIO_STATE(ctypes.Structure):
    _fields_ = [
        ("dwNumberOfPhys", DWORD),
    ]


class WLAN_INTERFACE_CAPABILITY(ctypes.Structure):
    _fields_ = [
        ("interfaceType", DWORD),
        ("strProfileName", wt.WCHAR * 256),
        ("dot11BssType", DWORD),
        ("dwMaxDesiredSsidListSize", DWORD),
        ("dwMaxDesiredBssidListSize", DWORD),
        ("dwNumberOfSupportedPhys", DWORD),
        ("dwNumberOfSupportedAuthCipherPairs", DWORD),
    ]


# ------------------------------------------------------------
# WlanOpenHandle
# ------------------------------------------------------------

wlanapi.WlanOpenHandle.argtypes = [
    DWORD,
    LPVOID,
    ctypes.POINTER(DWORD),
    ctypes.POINTER(HANDLE),
]

wlanapi.WlanOpenHandle.restype = DWORD

handle = HANDLE()
version = DWORD()

result = wlanapi.WlanOpenHandle(
    2,
    None,
    ctypes.byref(version),
    ctypes.byref(handle),
)

print("=" * 70)
print("           Native WLAN Capability Test")
print("=" * 70)

print(f"\nWlanOpenHandle : {result}")
print(f"WLAN version   : {version.value}")

if result != 0:
    raise RuntimeError(f"WlanOpenHandle failed: {result}")


# ------------------------------------------------------------
# Enumerate interfaces
# ------------------------------------------------------------

wlanapi.WlanEnumInterfaces.argtypes = [
    HANDLE,
    LPVOID,
    ctypes.POINTER(ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)),
]

wlanapi.WlanEnumInterfaces.restype = DWORD

interface_list_ptr = ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)()

result = wlanapi.WlanEnumInterfaces(
    handle,
    None,
    ctypes.byref(interface_list_ptr),
)

print(f"WlanEnumInterfaces : {result}")

if result != 0:
    raise RuntimeError(f"WlanEnumInterfaces failed: {result}")

interface_list = interface_list_ptr.contents

print(f"Interfaces found   : {interface_list.dwNumberOfItems}")


# ------------------------------------------------------------
# WlanQueryInterface
# ------------------------------------------------------------

wlanapi.WlanQueryInterface.argtypes = [
    HANDLE,
    ctypes.POINTER(GUID),
    DWORD,
    LPVOID,
    ctypes.POINTER(DWORD),
    ctypes.POINTER(LPVOID),
    ctypes.POINTER(DWORD),
]

wlanapi.WlanQueryInterface.restype = DWORD


# WLAN_INTF_OPCODE values
wlan_intf_opcode_current_connection = 7
wlan_intf_opcode_radio_state = 5
wlan_intf_opcode_interface_capability = 17


def guid_to_string(g):
    data4 = bytes(g.Data4)

    return (
        f"{g.Data1:08x}-"
        f"{g.Data2:04x}-"
        f"{g.Data3:04x}-"
        f"{data4[0]:02x}{data4[1]:02x}-"
        f"{data4[2]:02x}{data4[3]:02x}"
        f"{data4[4]:02x}{data4[5]:02x}"
        f"{data4[6]:02x}{data4[7]:02x}"
    )


def query_interface(guid, opcode):

    data_size = DWORD()
    data_ptr = LPVOID()
    value_type = DWORD()

    result = wlanapi.WlanQueryInterface(
        handle,
        ctypes.byref(guid),
        opcode,
        None,
        ctypes.byref(data_size),
        ctypes.byref(data_ptr),
        ctypes.byref(value_type),
    )

    return result, data_size.value, data_ptr


# ------------------------------------------------------------
# Inspect interface
# ------------------------------------------------------------

info_size = ctypes.sizeof(WLAN_INTERFACE_INFO)

for i in range(interface_list.dwNumberOfItems):

    base = ctypes.addressof(interface_list.InterfaceInfo)

    info = WLAN_INTERFACE_INFO.from_address(
        base + i * info_size
    )

    print("\n" + "-" * 70)
    print(f"INTERFACE #{i}")
    print("-" * 70)

    print("Description:")
    print(info.strInterfaceDescription)

    print("\nGUID:")
    print(guid_to_string(info.InterfaceGuid))

    print("\nState:")
    print(info.isState)

    # --------------------------------------------------------
    # Radio state
    # --------------------------------------------------------

    print("\n[Radio State]")

    result, size, ptr = query_interface(
        info.InterfaceGuid,
        wlan_intf_opcode_radio_state,
    )

    print("Result:", result)
    print("Size  :", size)

    if result == 0 and ptr:

        raw = ctypes.string_at(ptr, size)

        if len(raw) >= 4:
            number_phys = int.from_bytes(raw[:4], "little")
            print("Number of physical radios:", number_phys)

    # --------------------------------------------------------
    # Interface capability
    # --------------------------------------------------------

    print("\n[Interface Capability]")

    result, size, ptr = query_interface(
        info.InterfaceGuid,
        wlan_intf_opcode_interface_capability,
    )

    print("Result:", result)
    print("Size  :", size)

    if result == 0 and ptr:

        print("Capability structure returned.")

        raw = ctypes.string_at(ptr, size)

        print("\nRaw capability data:")
        print(raw.hex(" "))

        if size >= ctypes.sizeof(WLAN_INTERFACE_CAPABILITY):

            cap = WLAN_INTERFACE_CAPABILITY.from_buffer_copy(
                raw[:ctypes.sizeof(WLAN_INTERFACE_CAPABILITY)]
            )

            print("\nParsed:")
            print("  Interface type              :", cap.interfaceType)
            print("  Profile name                :", cap.strProfileName)
            print("  BSS type                    :", cap.dot11BssType)
            print("  Max desired SSIDs           :", cap.dwMaxDesiredSsidListSize)
            print("  Max desired BSSIDs          :", cap.dwMaxDesiredBssidListSize)
            print("  Supported physical radios  :", cap.dwNumberOfSupportedPhys)
            print("  Auth/Cipher pairs           :", cap.dwNumberOfSupportedAuthCipherPairs)

    else:
        print("Capability query failed.")

# ------------------------------------------------------------
# Close
# ------------------------------------------------------------

wlanapi.WlanCloseHandle.argtypes = [
    HANDLE,
    LPVOID,
]

wlanapi.WlanCloseHandle.restype = DWORD

wlanapi.WlanCloseHandle(handle, None)

print("\n" + "=" * 70)
print("Test complete.")
print("=" * 70)