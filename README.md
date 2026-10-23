# Wi-Fi Direct WPA2 Access Point + Internet Sharing (Python WinRT)

A lightweight Python script that creates a legacy Wi-Fi Direct Access Point (WPA2) on Windows using the native **WinRT (Windows Runtime)** APIs, and automatically enables **Internet Connection Sharing (ICS)** so connected clients get an IP address, DNS and internet access.

It is useful when the built-in *Mobile Hotspot* page fails (for example with "We can't set up mobile hotspot") or when you want to choose exactly which adapter shares its internet connection.

---

## 📋 Features

* **Legacy Wi-Fi Direct SoftAP**: Standard Wi-Fi devices (smartphones, laptops, TVs, IoT devices) can scan and connect with normal WPA2 credentials.
* **Autonomous Group Owner Mode**: Runs as an autonomous Group Owner without a peer negotiation prompt.
* **Automatic ICS**: Enables Windows Internet Connection Sharing through the `HNetCfg.HNetShare` COM interface, so clients receive DHCP + DNS (`192.168.137.x`) and NAT.
* **Choose the internet source**: Pick the adapter that provides internet either by name (`PUBLIC_MATCH`) or from a numbered list at startup.
* **Real status reporting**: Waits for the publisher's `STARTED` status (and reports `ABORTED` with its error) instead of assuming `start()` succeeded.
* **Clean shutdown**: Disables sharing and stops the publisher when you press Enter.

---

## 🛠️ Requirements & Compatibility

* **OS**: Windows 10 (version 1803+) or Windows 11.
* **Python**: Recommended **Python 3.11** (tested on `3.11.9`).
* **Hardware**: Wi-Fi adapter whose driver supports **Wi-Fi Direct / SoftAP**.
* **Privileges**: Must be run as **Administrator** (required for enabling ICS).

---

## 📦 Installation

```bash
pip install winrt-Windows.Devices.WiFiDirect winrt-Windows.Security.Credentials winrt-Windows.Foundation winrt-Windows.Foundation.Collections pywin32
```

* `winrt-Windows.Foundation*` is required for the `status_changed` event handler.
* `pywin32` is required for the ICS (internet sharing) part.

> **Note:** If another `ModuleNotFoundError` appears, install the matching package, e.g. `winrt.windows.devices.enumeration` → `pip install winrt-Windows.Devices.Enumeration`.

---

## ⚙️ Configuration

Edit the settings at the top of `wifi_direct_ap.py`:

| Setting | Description |
| --- | --- |
| `SSID` | Name of the access point. |
| `PASSWORD` | WPA2 passphrase, **at least 8 characters**. |
| `PUBLIC_MATCH` | Text contained in the name or device name of the adapter that provides internet (e.g. `"Ethernet"`, `"Wi-Fi 2"`). Set to `None` (no quotes) to choose from a numbered list at startup. |
| `PRIVATE_MATCH` | Text identifying the AP-side virtual adapter. Default: `"Wi-Fi Direct Virtual"`. |
| `START_TIMEOUT` | Seconds to wait for the AP to reach `STARTED`. |

To see your adapter names, run `ncpa.cpl`, or set `PUBLIC_MATCH = None` and read the list the script prints.

---

## 🚀 Usage

1. Open **Command Prompt** or **PowerShell** as **Administrator**.
2. Run the script:

```bash
python wifi_direct_ap.py
```

3. If `PUBLIC_MATCH` is `None` (or no adapter matched), pick the adapter that provides internet from the list. Do **not** pick the *Microsoft Wi-Fi Direct Virtual Adapter*, that is the AP side.
4. Check the output:
   * `[status] ... STARTED` – the AP is broadcasting.
   * `Public (internet kaynağı)` should be your internet adapter and `Private (AP tarafı)` should be the Wi-Fi Direct virtual adapter.
5. Once you see `WPA2 AP ÇALIŞIYOR`, connect from a client using your `SSID` and `PASSWORD`.
6. Keep the terminal open. Press **Enter** to disable sharing and stop the AP.

### Sharing from the same Wi-Fi card

You can share the internet of the Wi-Fi network you are connected to (select that Wi-Fi connection as the source). This requires driver support for running a client connection and an AP at the same time. Note that:

* The AP is forced onto the same channel/band as the connected network.
* Throughput is roughly halved because both share one radio.
* If you have several Wi-Fi cards, Windows chooses which one hosts the AP.

---

## ⚠️ Troubleshooting & Common Issues

* **`START ERROR` / `ABORTED` on `publisher.start()`**:
  * Make sure Wi-Fi is turned **ON** and Airplane mode is off.
  * Check driver support with `netsh wlan show drivers` (look for Wi-Fi Direct / Wireless Display support).
  * Run as **Administrator**.
* **Password is rejected or clients can't connect**: WPA2 requires at least 8 characters.
* **`Wi-Fi Direct sanal bağdaştırıcısı bulunamadı`**: Adjust `PRIVATE_MATCH` to match the device name shown in the adapter list.
* **ICS fails to enable**:
  * Make sure the *Internet Connection Sharing (SharedAccess)* service can start: `sc.exe config SharedAccess start= demand`.
  * Disable any old manual sharing on other adapters (the script already tries to turn it off first).
* **Clients get an IP but no DNS / internet**:
  * Test with a manual DNS on the client (e.g. `1.1.1.1`). If that works, NAT is fine and only DNS distribution is the issue; confirm the correct `Public` adapter was selected.
* **`sc query` returns empty output**: In PowerShell `sc` is an alias for `Set-Content`; use `sc.exe` instead.

## ⚠️ Manual DNS Commands

```powershell
Set-DnsClientServerAddress -InterfaceIndex 6 -ServerAddresses ("x.x.x.x")
Get-DnsClientServerAddress -InterfaceIndex 6
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
