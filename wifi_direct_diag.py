import subprocess
import json

print("=" * 70)
print("          Wi-Fi Direct / Virtual Wi-Fi Diagnostic")
print("=" * 70)

# ------------------------------------------------------------
# 1. Wi-Fi Direct virtual adapter
# ------------------------------------------------------------

print("\n[1] Wi-Fi Direct / Virtual adapters")
print("-" * 70)

commands = [
    """
    Get-NetAdapter |
    Select-Object Name, InterfaceDescription, Status,
    Virtual, HardwareInterface, MacAddress, LinkSpeed |
    Format-List
    """,

    """
    Get-NetAdapter |
    Where-Object {
        $_.InterfaceDescription -match
        'Wi-Fi Direct|Wireless|Virtual'
    } |
    Select-Object Name, InterfaceDescription, Status,
    Virtual, HardwareInterface |
    Format-Table -AutoSize
    """
]

for cmd in commands:

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            cmd
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    print(result.stdout)


# ------------------------------------------------------------
# 2. P2P related services
# ------------------------------------------------------------

print("\n[2] Wi-Fi Direct related services")
print("-" * 70)

result = subprocess.run(
    [
        "powershell",
        "-NoProfile",
        "-Command",
        """
        Get-Service |
        Where-Object {
            $_.Name -match 'Wlan|Wcmsvc|DeviceAssociation|P2P'
            -or
            $_.DisplayName -match 'Wi-Fi|Wireless|Device Association'
        } |
        Select-Object Name, DisplayName, Status, StartType |
        Format-Table -AutoSize
        """
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace"
)

print(result.stdout)


# ------------------------------------------------------------
# 3. PnP information for MT7921
# ------------------------------------------------------------

print("\n[3] MT7921 PnP capabilities")
print("-" * 70)

result = subprocess.run(
    [
        "powershell",
        "-NoProfile",
        "-Command",
        """
        Get-PnpDevice |
        Where-Object {
            $_.FriendlyName -like '*MT7921*'
        } |
        Select-Object Status, Class, FriendlyName,
        InstanceId |
        Format-List
        """
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace"
)

print(result.stdout)


# ------------------------------------------------------------
# 4. Wireless Hosted Network information
# ------------------------------------------------------------

print("\n[4] Hosted Network registry / driver hints")
print("-" * 70)

paths = [
    r"HKLM:\SYSTEM\CurrentControlSet\Services\WlanSvc",
    r"HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
]

for path in paths:

    print(f"\nRegistry path: {path}")

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            f"""
            Get-ItemProperty '{path}' -ErrorAction SilentlyContinue |
            Format-List *
            """
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    output = result.stdout

    # Don't dump everything if it gets huge
    if len(output) > 5000:
        output = output[:5000] + "\n...[truncated]..."

    print(output)


print("\n" + "=" * 70)
print("Diagnostic complete.")
print("=" * 70)