"""Thin HTTP client wrapping vnrobo-agent (or falling back to requests)."""

from typing import Any, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class VnRoboClient:
    def __init__(self, api_key: str, robot_id: str, endpoint: str):
        self._api_key = api_key
        self._robot_id = robot_id
        self._endpoint = endpoint
        self._session = self._make_session()

    def _make_session(self):
        try:
            import requests
            s = requests.Session()
            s.headers.update({
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            })
            return s
        except ImportError:
            return None

    def send(
        self,
        status: str = "online",
        battery: Optional[float] = None,
        location: Optional[Dict] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        from datetime import datetime, timezone
        payload: Dict[str, Any] = {
            "robotId": self._robot_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if battery is not None:
            payload["battery"] = battery
        if location is not None:
            payload["location"] = location
        if metadata is not None:
            payload["metadata"] = metadata

        if self._session is None:
            logger.error("requests not installed — pip install requests")
            return False

        try:
            resp = self._session.post(self._endpoint, data=json.dumps(payload), timeout=10)
            if resp.status_code < 300:
                return True
            logger.warning("VnRobo API %d: %s", resp.status_code, resp.text[:200])
            return False
        except Exception as exc:
            logger.warning("VnRobo send failed: %s", exc)
            return False
