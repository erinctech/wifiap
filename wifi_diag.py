import ctypes
import ctypes.wintypes as wt
import subprocess
import json
import os
import platform

print("=" * 70)
print("        MT7921 Wi-Fi / AP Capability Diagnostic")
print("=" * 70)

print(f"\nOS      : {platform.platform()}")
print(f"Python  : {platform.python_version()}")
print(f"Arch    : {platform.machine()}")

# ------------------------------------------------------------
# 1. Windows adapter information
# ------------------------------------------------------------

print("\n[1] Network adapters")
print("-" * 70)

try:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-NetAdapter | "
            "Select-Object Name, InterfaceDescription, Status, "
            "MacAddress, LinkSpeed, Virtual, HardwareInterface | "
            "ConvertTo-Json -Compress"
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode == 0 and result.stdout.strip():
        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        for adapter in data:
            print(json.dumps(adapter, indent=2, ensure_ascii=False))

    else:
        print("Adapter information could not be read.")
        print(result.stderr)

except Exception as e:
    print(f"ERROR: {e}")


# ------------------------------------------------------------
# 2. WLAN API
# ------------------------------------------------------------

print("\n[2] Native Windows WLAN API")
print("-" * 70)

wlanapi = ctypes.WinDLL("wlanapi.dll")

HANDLE = wt.HANDLE
DWORD = wt.DWORD
BOOL = wt.BOOL
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


# DWORD WlanOpenHandle(
#   DWORD dwClientVersion,
#   PVOID pReserved,
#   PDWORD pdwNegotiatedVersion,
#   PHANDLE phClientHandle
# );

wlanapi.WlanOpenHandle.argtypes = [
    DWORD,
    LPVOID,
    ctypes.POINTER(DWORD),
    ctypes.POINTER(HANDLE)
]

wlanapi.WlanOpenHandle.restype = DWORD


client_handle = HANDLE()
negotiated_version = DWORD()

status = wlanapi.WlanOpenHandle(
    2,
    None,
    ctypes.byref(negotiated_version),
    ctypes.byref(client_handle)
)

print(f"WlanOpenHandle status      : {status}")
print(f"Negotiated WLAN version    : {negotiated_version.value}")

if status != 0:
    print("Could not open native WLAN API.")
    raise SystemExit(1)


# ------------------------------------------------------------
# 3. Enumerate WLAN interfaces
# ------------------------------------------------------------

interface_list_ptr = ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)()

wlanapi.WlanEnumInterfaces.argtypes = [
    HANDLE,
    LPVOID,
    ctypes.POINTER(ctypes.POINTER(WLAN_INTERFACE_INFO_LIST))
]

wlanapi.WlanEnumInterfaces.restype = DWORD

status = wlanapi.WlanEnumInterfaces(
    client_handle,
    None,
    ctypes.byref(interface_list_ptr)
)

print(f"\nWlanEnumInterfaces status  : {status}")

if status == 0:
    interface_list = interface_list_ptr.contents

    print(f"Interfaces found            : {interface_list.dwNumberOfItems}")

    # The structure contains a variable-length array.
    base = ctypes.addressof(interface_list.InterfaceInfo)

    info_size = ctypes.sizeof(WLAN_INTERFACE_INFO)

    for i in range(interface_list.dwNumberOfItems):
        info = WLAN_INTERFACE_INFO.from_address(
            base + i * info_size
        )

        print(f"\nInterface #{i}")
        print(f"  Description : {info.strInterfaceDescription}")
        print(f"  State       : {info.isState}")

else:
    print("Could not enumerate WLAN interfaces.")


# ------------------------------------------------------------
# 4. Check Wi-Fi Direct service
# ------------------------------------------------------------

print("\n[3] Wi-Fi Direct")
print("-" * 70)

try:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-Service WlanSvc -ErrorAction SilentlyContinue | "
            "Select-Object Name, Status, StartType | ConvertTo-Json -Compress)"
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    print("WLAN AutoConfig service:")
    print(result.stdout.strip() or "Not available")

except Exception as e:
    print(f"ERROR: {e}")


# ------------------------------------------------------------
# 5. Driver information
# ------------------------------------------------------------

print("\n[4] MediaTek driver information")
print("-" * 70)

try:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            """
            Get-CimInstance Win32_PnPSignedDriver |
            Where-Object {
                $_.DeviceName -like '*MT7921*'
            } |
            Select-Object DeviceName,
                          DriverVersion,
                          DriverDate,
                          Manufacturer,
                          InfName |
            ConvertTo-Json -Compress
            """
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    print(result.stdout.strip() or "MT7921 driver information not found.")

except Exception as e:
    print(f"ERROR: {e}")


# ------------------------------------------------------------
# 6. Cleanup
# ------------------------------------------------------------

wlanapi.WlanCloseHandle.argtypes = [
    HANDLE,
    LPVOID
]

wlanapi.WlanCloseHandle.restype = DWORD

wlanapi.WlanCloseHandle(client_handle, None)

print("\n" + "=" * 70)
print("Diagnostic complete.")
print("=" * 70)