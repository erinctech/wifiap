from winrt.windows.devices.wifidirect import WiFiDirectAdvertisementPublisher

print("=" * 70)
print("Wi-Fi Direct AP DEBUG")
print("=" * 70)

publisher = WiFiDirectAdvertisementPublisher()
advertisement = publisher.advertisement
legacy = advertisement.legacy_settings

advertisement.is_autonomous_group_owner_enabled = True
legacy.is_enabled = True

print("Autonomous Group Owner:", advertisement.is_autonomous_group_owner_enabled)
print("Legacy Settings:", legacy.is_enabled)

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
print("Publisher is running.")
print("Press ENTER to stop.")

input()

print()
print("Stopping...")

try:
    publisher.stop()
    print("Stopped.")
except Exception as e:
    print("STOP ERROR:", type(e).__name__, str(e))