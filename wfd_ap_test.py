from winrt.windows.devices.wifidirect import (
    WiFiDirectAdvertisementPublisher,
    WiFiDirectAdvertisementPublisherStatus,
)

print("=" * 70)
print("MT7921 Wi-Fi Direct / Legacy AP TEST")
print("=" * 70)

publisher = WiFiDirectAdvertisementPublisher()

advertisement = publisher.advertisement

# Windows'u Autonomous Group Owner olmaya zorla
advertisement.is_autonomous_group_owner_enabled = True

# Normal Wi-Fi cihazlarının bağlanabilmesini sağla
legacy = advertisement.legacy_settings
legacy.is_enabled = True

print()
print("Configuration:")
print("  Autonomous Group Owner :", advertisement.is_autonomous_group_owner_enabled)
print("  Legacy Settings        :", legacy.is_enabled)

print()
print("Starting publisher...")

try:
    publisher.start()

    print("Publisher status:", publisher.status)

    status_names = {
        WiFiDirectAdvertisementPublisherStatus.CREATED: "Created",
        WiFiDirectAdvertisementPublisherStatus.STARTED: "Started",
        WiFiDirectAdvertisementPublisherStatus.STOPPED: "Stopped",
        WiFiDirectAdvertisementPublisherStatus.ABORTED: "Aborted",
    }

    print(
        "Status name:",
        status_names.get(
            publisher.status,
            f"Unknown ({publisher.status})"
        )
    )

except Exception as e:
    print()
    print("START FAILED")
    print("Exception:", type(e).__name__)
    print("Message:", e)

print()
print("=" * 70)