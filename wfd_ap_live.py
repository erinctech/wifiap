from winrt.windows.devices.wifidirect import (
    WiFiDirectAdvertisementPublisher,
)

print("=" * 70)
print("MT7921 Wi-Fi Direct LIVE TEST")
print("=" * 70)

publisher = WiFiDirectAdvertisementPublisher()
advertisement = publisher.advertisement

advertisement.is_autonomous_group_owner_enabled = True
advertisement.legacy_settings.is_enabled = True

print("Autonomous Group Owner :", advertisement.is_autonomous_group_owner_enabled)
print("Legacy Settings        :", advertisement.legacy_settings.is_enabled)

print()
print("Starting...")

publisher.start()

print("Status:", publisher.status)
print()
print("Publisher is now alive.")
print("Press ENTER to stop.")
print()

input()

print("Stopping...")
publisher.stop()

print("Stopped.")