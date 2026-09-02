# Wi-Fi Direct WPA2 Access Point (Python WinRT)

A lightweight Python script that creates a legacy Wi-Fi Direct Access Point (WPA2) on Windows using the native **WinRT (Windows Runtime)** APIs via `winsdk` / `winrt-Windows.Devices.WiFiDirect` and `winrt-Windows.Security.Credentials`.

---

## 📋 Features

* **Legacy Wi-Fi Direct SoftAP**: Allows standard Wi-Fi devices (smartphones, laptops, IoT devices) to scan and connect via standard WPA2 credentials.
* **Autonomous Group Owner Mode**: Runs as an autonomous Group Owner without requiring a peer negotiation prompt.
* **Pure Python & Native Windows API**: Interacts directly with Windows Runtime APIs without needing external C++ wrappers or legacy `netsh` hacks.

---

## 🛠️ Requirements & Compatibility

* **OS**: Windows 10 (version 1803+) or Windows 11.
* **Python**: Recommended **Python 3.11** (tested on `3.11.9`).
* **Hardware**: Wi-Fi adapter supporting **Wi-Fi Direct / SoftAP** mode.

---

## 📦 Installation

To run this script on **Python 3.11**, install the required `winrt` standard packages:

```bash
pip install winrt-Windows.Devices.WiFiDirect winrt-Windows.Security.Credentials
```

> **Note on `winsdk` / `winrt` libraries:**
> Depending on your environment or if you are using the modern PyWinRT toolchain, you can also install:
> ```bash
> pip install winsdk
> ```

---

## 🚀 Usage

1. Open a **Command Prompt** or **PowerShell** as **Administrator** (recommended for low-level network API calls).
2. Clone or download this repository.
3. Run the script:

```bash
python wfd_ap_ssid.py
```

4. Once you see `WPA2 AP SHOULD NOW BE RUNNING`, scan for Wi-Fi networks on your client device (phone, laptop, etc.):
   * **SSID**: `testap`
   * **Password**: `12345678`

5. Keep the terminal window open to keep the Access Point active. Press **Enter** in the console to stop the advertisement and shut down the AP.

---

## ⚠️ Troubleshooting & Common Issues

* **`START ERROR` / Exception on `publisher.start()`**:
  * Ensure Wi-Fi is turned **ON** in Windows settings.
  * Verify that your Wi-Fi card supports Wi-Fi Direct (`netsh wlan show drivers` -> check *Hosted network supported* or *Wi-Fi Direct* support).
  * Run the command prompt as **Administrator**.
* **Clients fail to obtain an IP address**:
  * Wi-Fi Direct legacy mode creates the connection layer. For automatic IP assignment (DHCP) and Internet connection sharing, ensure **ICS (Internet Connection Sharing)** or Windows Network Bridging is properly configured on your primary internet adapter.

## ⚠️ Manual DNS Commands

```
Set-DnsClientServerAddress -InterfaceIndex 6 -ServerAddresses ("x.x.x.x")
Get-DnsClientServerAddress -InterfaceIndex 6
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.