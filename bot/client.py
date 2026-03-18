
from __future__ import annotations

import time
import  hmac
import hashlib

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bot.logging_config import setup_logger

logger = setup_logger()

BASE_URL = "https://testnet.binancefuture.com"

_RETRY_STRATEGY = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],

)

class BinanceAPIError(Exception):
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg
        super().__init__(f"Binance API Error {code}: {msg}")


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")
        self.api_key = api_key
        self.api_secret = api_secret

        self.sessions = requests.Sessions()
        adapter = HTTPAdapter(max_retries=_RETRY_STRATEGY)
        self._session.mount("https://", adapter)
        self._session.headers.update({"X-MBX-APIKEY": self.api_key})

        logger.debug("Binance Futures Testnet API client initialized.")

        def _timestamp():
            return int(time.time() * 1000)

        def _sign(self, query):
            return hmac.new(
                self.api_secret.encode('utf-8'),
                query.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

        def _build_signed_params(self, params):
            params["timestamp"] = self._timestamp()
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
            params["signature"] = self._sign(query_string)
            return params

        def _request(self, method, endpoint, params=None ):

            signed_params = self._build_signed_params(params)
            url =  BASE_URL + endpoint

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
                    msg = data.get("msg", "Unknown error")
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


    def get(self,url, params = None):
        return self._request("GET", url, params or {})

    def delete(self,url, params = None):
        return self._request("DELETE", url,params or {})

    def post(self, url, params = None):
        return self._request("POST", url, params or {})


    def ping(self):
        try:
            self._session.get(BASE_URL+"/fapi/v1/ping", timeout=10)
            logger.debug("<< PING OK")
            return True
        except requests.exceptions.RequestException:
            logger.warning("Request failed")
            return False

    def get_balance(self):
        return self.get("/fapi/v1/account/balance")

    def get_price(self, symbol):
        resp = self._session.get(BASE_URL + "/fapi/v1/ticker/price", params={"symbol": symbol}, timeout = 10)
        resp.raise_for_status()
        return resp.json()["price"]

