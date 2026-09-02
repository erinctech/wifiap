from winrt.windows.devices.wifidirect import (
    WiFiDirectAdvertisementPublisher,
    WiFiDirectAdvertisementPublisherStatus,
)


print("=" * 70)
print("Wi-Fi Direct WinRT test")
print("=" * 70)

try:
    publisher = WiFiDirectAdvertisementPublisher()

    print("Publisher created:       YES")
    print("Initial status:", publisher.status)

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

    advertisement = publisher.advertisement

    print()
    print("Advertisement object:    OK")

    print(
        "Autonomous Group Owner:",
        advertisement.is_autonomous_group_owner_enabled
    )

    print()
    print("SUCCESS: WinRT Wi-Fi Direct API is accessible.")

except Exception as e:

    print()
    print("FAILED")
    print("Exception type:", type(e).__name__)
    print("Exception:", e)

print("=" * 70)