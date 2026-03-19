"""
client.py
---------
Low-level Binance Futures Testnet API wrapper.

Responsibilities:
  - Build and sign every request (HMAC-SHA256)
  - Attach API key header
  - Send HTTP requests with timeout + retry
  - Raise clean exceptions for API/network errors
  - Log every request and response at DEBUG level

Nothing in this file knows about order logic or CLI — it only speaks HTTP.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bot.logging_config import setup_logger

logger = setup_logger()

BASE_URL = "https://testnet.binancefuture.com"

# Retry on transient network errors (not on 4xx API errors)
_RETRY_STRATEGY = Retry(
    total=3,
    backoff_factor=1,            # waits 1s, 2s, 4s between retries
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET", "POST", "DELETE"],
)


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-200 response."""
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg  = msg
        super().__init__(f"Binance API Error {code}: {msg}")


class BinanceClient:
    """
    Authenticated Binance Futures Testnet client.

    Usage:
        client = BinanceClient(api_key="...", api_secret="...")
        data   = client.post("/fapi/v1/order", {"symbol": "BTCUSDT", ...})
    """

    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")

        self._api_key    = api_key
        self._api_secret = api_secret

        # Persistent session with retry + connection pooling
        self._session = requests.Session()
        adapter = HTTPAdapter(max_retries=_RETRY_STRATEGY)
        self._session.mount("https://", adapter)
        self._session.headers.update({"X-MBX-APIKEY": self._api_key})

        logger.debug("BinanceClient initialised (testnet).")

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _timestamp() -> int:
        """Current UTC time in milliseconds."""
        return int(time.time() * 1000)

    def _sign(self, query_string: str) -> str:
        """HMAC-SHA256 signature required by Binance for private endpoints."""
        return hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _build_signed_params(self, params: dict) -> dict:
        """Add timestamp + signature to a params dict."""
        params["timestamp"] = self._timestamp()
        query_string        = "&".join(f"{k}={v}" for k, v in params.items())
        params["signature"] = self._sign(query_string)
        return params

    # ── Private request dispatcher ────────────────────────────────────────────

    def _request(self, method: str, endpoint: str, params: dict) -> Any:
        """
        Core method that signs, sends, and parses every request.
        Raises BinanceAPIError on API-level errors.
        Raises requests.exceptions.* on network-level errors.
        """
        signed_params = self._build_signed_params(params)
        url           = BASE_URL + endpoint

        logger.debug(">>> %s %s | params: %s", method.upper(), endpoint, signed_params)

        try:
            if method == "GET":
                response = self._session.get(url, params=signed_params, timeout=10)
            elif method == "POST":
                response = self._session.post(url, params=signed_params, timeout=10)
            elif method == "DELETE":
                response = self._session.delete(url, params=signed_params, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            data = response.json()

            logger.debug(
                "<<< %s %s | status: %d | body: %s",
                method.upper(), endpoint, response.status_code, data,
            )

            # Binance returns error details in JSON even on 4xx
            if not response.ok:
                code = data.get("code", response.status_code)
                msg  = data.get("msg",  "Unknown error")
                logger.error("API error %s: %s", code, msg)
                raise BinanceAPIError(code, msg)

            return data

        except requests.exceptions.Timeout:
            logger.error("Request timed out: %s %s", method, endpoint)
            raise
        except requests.exceptions.ConnectionError:
            logger.error("Connection error: %s %s", method, endpoint)
            raise
        except requests.exceptions.RequestException as exc:
            logger.error("Network error: %s", exc)
            raise

    # ── Public API methods ────────────────────────────────────────────────────

    def get(self, endpoint: str, params: dict | None = None) -> Any:
        return self._request("GET", endpoint, params or {})

    def post(self, endpoint: str, params: dict | None = None) -> Any:
        return self._request("POST", endpoint, params or {})

    def delete(self, endpoint: str, params: dict | None = None) -> Any:
        return self._request("DELETE", endpoint, params or {})

    # ── Convenience wrappers ──────────────────────────────────────────────────

    def ping(self) -> bool:
        """Returns True if the testnet server is reachable."""
        try:
            self._session.get(BASE_URL + "/fapi/v1/ping", timeout=5)
            logger.info("Testnet ping successful.")
            return True
        except requests.exceptions.RequestException:
            logger.warning("Testnet ping failed.")
            return False

    def get_balance(self) -> list[dict]:
        """Fetch USDT-M futures account balance."""
        return self.get("/fapi/v2/balance")

    def get_price(self, symbol: str) -> str:
        """Fetch latest mark price for a symbol (no auth needed)."""
        resp = self._session.get(
            BASE_URL + "/fapi/v1/ticker/price",
            params={"symbol": symbol},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()["price"]