"""
Wi-Fi Direct AP (WPA2) + Internet Connection Sharing (ICS)

Gereksinimler:
    pip install winrt-Windows.Devices.WiFiDirect winrt-Windows.Security.Credentials pywin32
    (kullandığınız winrt paket kurulumu neyse onu kullanın)

YÖNETİCİ olarak çalıştırın.
"""
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
SSID = "SUPERONLINE_WiNN_1225"
PASSWORD = "12345678"            # WPA2 için en az 8 karakter

# İnternetin geldiği bağdaştırıcı: Ad veya cihaz adında geçen ifade.
# None yapılırsa açılışta listeden numara ile seçersiniz.
PUBLIC_MATCH = "Wi-Fi 2"
#PUBLIC_MATCH = None

# AP tarafındaki sanal bağdaştırıcının cihaz adında geçen ifade
PRIVATE_MATCH = "Wi-Fi Direct Virtual"

START_TIMEOUT = 15               # saniye
# ---------------------------------------------------------------------------


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


def list_connections():
    _, conns = all_connections()
    print("Bağdaştırıcılar:")
    for i, (_, name, dev) in enumerate(conns):
        print(f"  [{i}] {name!r:35} | {dev}")
    return conns


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


def pick_public(conns):
    if PUBLIC_MATCH:
        key = PUBLIC_MATCH.lower()
        for c, name, dev in conns:
            if PRIVATE_MATCH.lower() in dev.lower():
                continue
            if key in name.lower() or key in dev.lower():
                return c, name
        print(f"'{PUBLIC_MATCH}' ile eşleşen bağdaştırıcı bulunamadı.")

    idx = int(input("İnternet veren bağdaştırıcının numarası: "))
    c, name, _ = conns[idx]
    return c, name


def enable_ics():
    disable_all_sharing()          # eski paylaşımlar çakışmasın
    time.sleep(1)

    ns, conns = all_connections()
    print()
    list_connections()
    print()

    public, public_name = pick_public(conns)

    private = private_name = None
    for c, name, dev in conns:
        if PRIVATE_MATCH.lower() in dev.lower():
            private, private_name = c, name   # birden fazlaysa sonuncusu

    if private is None:
        raise RuntimeError(
            "Wi-Fi Direct sanal bağdaştırıcısı bulunamadı. "
            "PRIVATE_MATCH değerini listeye göre düzeltin."
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

    publisher = WiFiDirectAdvertisementPublisher()
    advertisement = publisher.advertisement
    legacy = advertisement.legacy_settings

    advertisement.is_autonomous_group_owner_enabled = True

    legacy.is_enabled = True
    legacy.ssid = SSID

    credential = PasswordCredential()
    credential.password = PASSWORD
    legacy.passphrase = credential

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
        enable_ics()
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
