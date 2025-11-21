import json
import logging
import threading
import urllib.parse

import requests

from config import VPN_API_URL, VPN_PASSWORD, VPN_USERNAME, SERVER_DOMAIN

SESSION_COOKIES = None
logger = logging.getLogger(__name__)


# Авторизация в 3X-UI
def vpn_login():
    global SESSION_COOKIES
    url = f"{VPN_API_URL}/login"
    data = {"username": VPN_USERNAME, "password": VPN_PASSWORD}
    try:
        resp = requests.post(url, json=data)
        resp.raise_for_status()
        SESSION_COOKIES = resp.cookies
        logger.info("Успешно залогинились в VPN-панель.")
    except Exception as e:
        logger.error(f"Не удалось залогиниться в VPN-панель: {e}")


def vless_key_generate(client_uuid: str, username: str) -> str:
    # --- Получаем параметры Reality из inbound ---
    inbounds_resp = requests.get(f"{VPN_API_URL}/panel/api/inbounds/list",
                                 cookies=SESSION_COOKIES)
    inbounds = inbounds_resp.json()

    items = inbounds.get("data") or inbounds.get("obj")

    if not items:
        raise Exception("API didn't return 'data' or 'obj'")

    inbound = next((i for i in items if i["id"] == 1), None)
    if not inbound:
        raise Exception("Inbound with id=1 not found")

    stream = json.loads(inbound["streamSettings"])
    reality = stream.get("realitySettings", {})

    # --- Reality параметры ---
    public_key = reality.get("settings", {}).get("publicKey")
    spider_x = reality.get("settings", {}).get("spiderX", "/")
    fp = reality.get("settings", {}).get("fingerprint", "chrome")
    target = reality.get("target") or (reality.get("serverNames") or [""])[0]
    sni = "google.com"
    pqv = reality.get("settings", {}).get("mldsa65Verify", "")

    spider_x_encoded = urllib.parse.quote(spider_x, safe='')

    short_ids = reality.get("shortIds", [])
    short_id = short_ids[0] if short_ids else ""

    SERVER_PORT = inbound["port"]

    # --- Формируем VLESS Reality ключ ---
    vless_key = (
        f"vless://{client_uuid}@{SERVER_DOMAIN}:{SERVER_PORT}"
        f"?type=tcp&encryption=none&security=reality"
        f"&pbk={public_key}"
        f"&fp={fp}"
        f"&sni={sni}"
        f"&sid={short_id}"
        f"&spx={spider_x_encoded}"
        f"&pqv={pqv}"
        f"&flow=xtls-rprx-vision"
        f"#KOSOLAPYYI-{username}"
    )

    return vless_key


def periodic_session_refresh(interval=60 * 355):
    """
    Обновляет сессию каждые interval секунд.
    """

    def refresh():
        vpn_login()
        logger.info("Сессия обновлена.")
        threading.Timer(interval, refresh).start()

    refresh()
