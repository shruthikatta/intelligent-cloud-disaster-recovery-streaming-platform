from __future__ import annotations

"""Publish admin-visible notifications (mock SNS or real)."""


from cloud_adapters.dependency_factory import get_notification_adapter


async def notify_admin(subject: str, body: str) -> str:
    adapter = get_notification_adapter()
    return await adapter.publish_alert(subject, body)
