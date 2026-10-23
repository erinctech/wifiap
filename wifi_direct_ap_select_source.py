"""
Wi-Fi Direct AP (WPA2) + Internet Connection Sharing (ICS)
+ AP'yi yayınlayacak Wi-Fi kartı seçimi

Gereksinimler:
    pip install winrt-Windows.Devices.WiFiDirect winrt-Windows.Security.Credentials
    pip install winrt-Windows.Foundation winrt-Windows.Foundation.Collections pywin32

YÖNETİCİ olarak çalıştırın.

NOT: WinRT API'si AP'nin hangi kartta açılacağını seçmeye izin vermez.
Bu script seçilen kart dışındaki Wi-Fi kartlarını çalışırken GEÇİCİ olarak
devre dışı bırakır ve çıkışta geri açar.
"""
import atexit
import json
import subprocess
import sys
import time
import threading

import pythoncom
import win32com.client

from winrt.windows.devices.wifidirect import (
    WiFiDirectAdvertisementPublisher,
    WiFiDirectAdvertisementPublisherStatus,
)
from winrt.windows.security.credentials import PasswordCredential

# ------------------------------------------------------------------ AYARLAR
SSID = "SUPERONLINE_WiFi_1225"
PASSWORD = "12345678"            # WPA2 için en az 8 karakter

# İnternetin geldiği bağdaştırıcı: Ad veya cihaz adında geçen ifade.
# None yapılırsa açılışta listeden numara ile seçersiniz.
PUBLIC_MATCH = "E16Cap"

# AP'yi yayınlayacak Wi-Fi kartı: Ad veya açıklamasında geçen ifade.
# None yapılırsa birden fazla Wi-Fi kartı varsa listeden numara ile seçersiniz.
HOST_MATCH = None

# True: seçilen kart dışındaki Wi-Fi kartlarını geçici olarak devre dışı bırakır.
# False: kart seçimi yapılmaz, Windows kendisi seçer.
MANAGE_ADAPTERS = True

# AP tarafındaki sanal bağdaştırıcının cihaz adında geçen ifade
PRIVATE_MATCH = "Wi-Fi Direct Virtual"

START_TIMEOUT = 15               # saniye
# ---------------------------------------------------------------------------


# ------------------------------------------------------------------ PowerShell
def ps(command):
    full = "[Console]::OutputEncoding=[Text.Encoding]::UTF8; " + command
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", full],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def q(s):
    """PowerShell tek tırnaklı string için kaçış."""
    return "'" + s.replace("'", "''") + "'"


# ------------------------------------------------------------------ Wi-Fi kartları
def get_wifi_adapters():
    """Fiziksel Wi-Fi kartları (NdisPhysicalMedium 9 = Native 802.11)."""
    r = ps(
        "Get-NetAdapter -Physical | Where-Object { $_.NdisPhysicalMedium -eq 9 } | "
        "Select-Object Name,InterfaceDescription,Status | ConvertTo-Json -Compress"
    )
    out = r.stdout.strip()
    if not out:
        return []
    data = json.loads(out)
    if isinstance(data, dict):
        data = [data]
    return data


def choose_host(adapters):
    if not adapters:
        return None

    if HOST_MATCH:
        key = HOST_MATCH.lower()
        for a in adapters:
            if key in a["Name"].lower() or key in a["InterfaceDescription"].lower():
                return a
        print(f"'{HOST_MATCH}' ile eşleşen Wi-Fi kartı bulunamadı.")

    if len(adapters) == 1:
        return adapters[0]

    print("Wi-Fi kartları:")
    for i, a in enumerate(adapters):
        print(f"  [{i}] {a['Name']!r:20} | {a['InterfaceDescription']} | {a['Status']}")
    idx = int(input("AP'yi yayınlayacak kartın numarası: "))
    return adapters[idx]


_disabled = []


def disable_others(adapters, keep_names):
    for a in adapters:
        name = a["Name"]
        if name in keep_names or a["Status"] == "Disabled":
            continue
        r = ps(f"Disable-NetAdapter -Name {q(name)} -Confirm:$false")
        if r.returncode == 0:
            _disabled.append(name)
            print(f"Geçici olarak devre dışı: {name}")
        else:
            print(f"Devre dışı bırakılamadı ({name}): {r.stderr.strip()}")
    if _disabled:
        print("Script beklenmedik şekilde kapanırsa kartları elle açmak için:")
        for n in _disabled:
            print(f"  Enable-NetAdapter -Name {q(n)}")
        time.sleep(3)


def restore_adapters():
    while _disabled:
        name = _disabled.pop()
        r = ps(f"Enable-NetAdapter -Name {q(name)} -Confirm:$false")
        if r.returncode == 0:
            print(f"Yeniden etkinleştirildi: {name}")
        else:
            print(f"Etkinleştirilemedi ({name}): {r.stderr.strip()}")


atexit.register(restore_adapters)


# ------------------------------------------------------------------ ICS
def get_share():
    pythoncom.CoInitialize()
    return win32com.client.Dispatch("HNetCfg.HNetShare")


def all_connections():
    ns = get_share()
    result = []
    for c in ns.EnumEveryConnection:
        p = ns.NetConnectionProps(c)
        result.append((c, p.Name, p.DeviceName))
    return ns, result


def disable_all_sharing():
    ns, conns = all_connections()
    for c, name, _ in conns:
        try:
            cfg = ns.INetSharingConfigurationForINetConnection(c)
            if cfg.SharingEnabled:
                cfg.DisableSharing()
                print(f"Paylaşım kapatıldı: {name}")
        except Exception as e:
            print(f"Paylaşım kapatılamadı ({name}): {e}")


def choose_public():
    """İnternet kaynağının ADINI döndürür (AP başlamadan önce seçilir)."""
    _, conns = all_connections()
    conns = [x for x in conns if PRIVATE_MATCH.lower() not in x[2].lower()]

    if PUBLIC_MATCH:
        key = PUBLIC_MATCH.lower()
        for _, name, dev in conns:
            if key in name.lower() or key in dev.lower():
                return name
        print(f"'{PUBLIC_MATCH}' ile eşleşen bağdaştırıcı bulunamadı.")

    print("Bağdaştırıcılar:")
    for i, (_, name, dev) in enumerate(conns):
        print(f"  [{i}] {name!r:35} | {dev}")
    idx = int(input("İnternet veren bağdaştırıcının numarası: "))
    return conns[idx][1]


def enable_ics(public_name):
    disable_all_sharing()          # eski paylaşımlar çakışmasın
    time.sleep(1)

    ns, conns = all_connections()

    public = None
    private = private_name = None
    for c, name, dev in conns:
        if name == public_name:
            public = c
        if PRIVATE_MATCH.lower() in dev.lower():
            private, private_name = c, name   # birden fazlaysa sonuncusu

    if public is None:
        raise RuntimeError(f"İnternet kaynağı bulunamadı: {public_name}")
    if private is None:
        raise RuntimeError(
            "Wi-Fi Direct sanal bağdaştırıcısı bulunamadı. "
            "PRIVATE_MATCH değerini düzeltin."
        )

    print(f"Public  (internet kaynağı): {public_name}")
    print(f"Private (AP tarafı)       : {private_name}")

    ns.INetSharingConfigurationForINetConnection(public).EnableSharing(0)   # public
    ns.INetSharingConfigurationForINetConnection(private).EnableSharing(1)  # private
    print("ICS etkinleştirildi (DHCP + DNS + NAT).")


# ------------------------------------------------------------------ AP
def main():
    print("=" * 70)
    print("Wi-Fi Direct AP - WPA2 + ICS")
    print("=" * 70)

    # 1) İnternet kaynağını seç
    public_name = choose_public()
    print(f"İnternet kaynağı: {public_name}")

    # 2) AP kartını seç ve diğer Wi-Fi kartlarını geçici kapat
    if MANAGE_ADAPTERS:
        wifi = get_wifi_adapters()
        host = choose_host(wifi)
        if host is None:
            print("Fiziksel Wi-Fi kartı bulunamadı, kart seçimi atlanıyor.")
        else:
            print(f"AP kartı: {host['Name']} ({host['InterfaceDescription']})")
            wifi_names = {a["Name"] for a in wifi}
            if public_name in wifi_names and public_name != host["Name"]:
                print(
                    f"UYARI: İnternet kaynağı ({public_name}) başka bir Wi-Fi kartı. "
                    "Kapatılamaz; Windows AP için hangi kartı kullanacağını kendisi "
                    "seçebilir."
                )
            disable_others(wifi, keep_names={host["Name"], public_name})

    try:
        run_ap(public_name)
    finally:
        restore_adapters()


def run_ap(public_name):
    publisher = WiFiDirectAdvertisementPublisher()
    advertisement = publisher.advertisement
    legacy = advertisement.legacy_settings

    advertisement.is_autonomous_group_owner_enabled = True

    legacy.is_enabled = True
    legacy.ssid = SSID

    credential = PasswordCredential()
    credential.password = PASSWORD
    legacy.passphrase = credential

    print()
    print("SSID:", legacy.ssid)
    print("Password:", PASSWORD)
    print("Legacy Settings:", legacy.is_enabled)
    print("Autonomous Group Owner:", advertisement.is_autonomous_group_owner_enabled)

    started = threading.Event()
    failed = threading.Event()

    def on_status(sender, args):
        print(f"[status] {args.status} | error: {args.error}")
        if args.status == WiFiDirectAdvertisementPublisherStatus.STARTED:
            started.set()
        elif args.status == WiFiDirectAdvertisementPublisherStatus.ABORTED:
            failed.set()

    publisher.add_status_changed(on_status)

    print()
    print("Starting publisher...")
    try:
        publisher.start()
    except Exception as e:
        print("START ERROR:", type(e).__name__, str(e))
        raise

    deadline = time.time() + START_TIMEOUT
    while time.time() < deadline and not started.is_set() and not failed.is_set():
        time.sleep(0.2)

    if failed.is_set() or not started.is_set():
        print("AP başlatılamadı (ABORTED veya zaman aşımı).")
        try:
            publisher.stop()
        except Exception:
            pass
        sys.exit(1)

    time.sleep(2)  # sanal bağdaştırıcının hazır olması için

    try:
        enable_ics(public_name)
    except Exception as e:
        print("ICS ERROR:", type(e).__name__, str(e))
        print("AP açık kalıyor ama internet paylaşımı yapılamadı.")

    print()
    print("=" * 70)
    print("WPA2 AP ÇALIŞIYOR")
    print("=" * 70)
    print("SSID:", SSID)
    print("Password:", PASSWORD)
    print()
    print("Bu pencereyi açık tutun.")
    print("Durdurmak için ENTER'a basın.")

    try:
        input()
    except KeyboardInterrupt:
        pass

    print()
    print("Stopping...")
    try:
        disable_all_sharing()
    except Exception as e:
        print("ICS kapatma hatası:", e)
    publisher.stop()
    print("Stopped.")


if __name__ == "__main__":
    main()
