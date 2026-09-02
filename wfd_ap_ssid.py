from winrt.windows.devices.wifidirect import WiFiDirectAdvertisementPublisher
from winrt.windows.security.credentials import PasswordCredential

SSID = "TESTAP"
PASSWORD = "12345678"

print("=" * 70)
print("Wi-Fi Direct AP - WPA2 TEST")
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
print("Autonomous Group Owner:",
      advertisement.is_autonomous_group_owner_enabled)

print()
print("Starting publisher...")

try:
    publisher.start()

    print("Start returned successfully.")
    print("Publisher status:", publisher.status)

except Exception as e:
    print("START ERROR:", type(e).__name__, str(e))
    raise

print()
print("=" * 70)
print("WPA2 AP SHOULD NOW BE RUNNING")
print("=" * 70)
print("SSID:", SSID)
print("Password:", PASSWORD)
print()
print("Keep this window open.")
print("Press ENTER to stop.")

input()

print()
print("Stopping...")

publisher.stop()

print("Stopped.")