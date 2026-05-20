import hashlib
import hmac
import json
import logging
from datetime import datetime

from aiohttp import web

from src import config
from src.database import crud
from src.database.crud import GATEBOT_SYNC_ISO_FORMAT
from src.database.database import Session
from src.database.models import User


LOGGER = logging.getLogger(__name__)


def _is_enabled() -> bool:
    try:
        return bool(config.get("gatebot.sync_enabled"))
    except KeyError:
        return False


def _get_secret() -> str:
    try:
        return config.get("gatebot.sync_secret") or ""
    except KeyError:
        return ""


async def handle_gatebot_subscription_sync(request: web.Request) -> web.Response:
    if not _is_enabled():
        return web.Response(status=404)

    secret = _get_secret()
    if not secret:
        LOGGER.error("Gatebot sync: secret is not configured, rejecting request")
        return web.Response(status=503)

    raw_body = await request.read()
    signature_header = request.headers.get("X-Signature", "")
    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        LOGGER.warning("Gatebot sync: invalid signature")
        return web.Response(status=401)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
        user_id = int(payload["user_id"])
        end_date_str = str(payload["subscription_end_date"])
        incoming_utc = datetime.strptime(end_date_str, GATEBOT_SYNC_ISO_FORMAT)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        LOGGER.exception("Gatebot sync: malformed payload")
        return web.Response(status=400)

    with Session() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user is None:
            crud.upsert_pending_subscription(session, user_id, incoming_utc)
        else:
            crud.merge_subscription_for_existing_user(
                session, user_id, incoming_utc
            )

    return web.Response(status=200)
