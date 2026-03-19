from __future__ import annotations

from typing import Any

from bot.client import BinanceClient
from bot.logging_config import setup_logger

logger = setup_logger()

ORDER_ENDPOINT = "/fapi/v1/order"


def parse_order_response(data):

    return {
        "orderId":     data.get("orderId"),
        "symbol":      data.get("symbol"),
        "status":      data.get("status"),
        "side":        data.get("side"),
        "type":        data.get("type"),
        "origQty":     data.get("origQty"),
        "executedQty": data.get("executedQty", "0"),
        "avgPrice":    data.get("avgPrice", "0"),
        "price":       data.get("price", "0"),
        "stopPrice":   data.get("stopPrice", "0"),
        "timeInForce": data.get("timeInForce", "—"),
        "updateTime":  data.get("updateTime"),
    }


def print_order_summary(parsed) -> None:
    """Print a clean, human-readable order result to stdout."""
    print("\n" + "═" * 45)
    print(" ORDER PLACED SUCCESSFULLY ")
    print("═" * 45)
    print(f"  Order ID     : {parsed['orderId']}")
    print(f"  Symbol       : {parsed['symbol']}")
    print(f"  Side         : {parsed['side']}")
    print(f"  Type         : {parsed['type']}")
    print(f"  Status       : {parsed['status']}")
    print(f"  Quantity     : {parsed['origQty']}")
    print(f"  Executed Qty : {parsed['executedQty']}")

    if float(parsed["avgPrice"] or 0) > 0:
        print(f"  Avg Price    : {parsed['avgPrice']}")
    if float(parsed["price"] or 0) > 0:
        print(f"  Limit Price  : {parsed['price']}")
    if float(parsed["stopPrice"] or 0) > 0:
        print(f"  Stop Price   : {parsed['stopPrice']}")

    print(f"  Time In Force: {parsed['timeInForce']}")
    print("═" * 45 + "\n")


def _base_params(symbol: str, side: str, quantity: float) -> dict:
    """Common params shared by all order types."""
    return {
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
    }


def place_market_order(
        client: BinanceClient,
        symbol: str,
        side: str,
        quantity: float,
) -> dict[str, Any]:

    params = _base_params(symbol, side, quantity)
    params["type"] = "MARKET"

    logger.info(
        "Placing MARKET %s order | symbol=%s | qty=%s",
        side, symbol, quantity,
    )
    logger.debug("Market order params: %s", params)

    raw = client.post(ORDER_ENDPOINT, params)
    parsed = parse_order_response(raw)

    logger.info(
        "MARKET order placed | orderId=%s | status=%s | executedQty=%s | avgPrice=%s",
        parsed["orderId"], parsed["status"], parsed["executedQty"], parsed["avgPrice"],
    )
    return parsed


def place_limit_order(
        client: BinanceClient,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
) -> dict[str, Any]:

    params = _base_params(symbol, side, quantity)
    params.update({
        "type": "LIMIT",
        "price": price,
        "timeInForce": time_in_force,
    })

    logger.info(
        "Placing LIMIT %s order | symbol=%s | qty=%s | price=%s | tif=%s",
        side, symbol, quantity, price, time_in_force,
    )
    logger.debug("Limit order params: %s", params)

    raw = client.post(ORDER_ENDPOINT, params)
    parsed = parse_order_response(raw)

    logger.info(
        "LIMIT order placed | orderId=%s | status=%s | price=%s",
        parsed["orderId"], parsed["status"], parsed["price"],
    )
    return parsed


def place_stop_market_order(
        client: BinanceClient,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
) -> dict[str, Any]:

    params = _base_params(symbol, side, quantity)
    params.update({
        "type": "STOP_MARKET",
        "stopPrice": stop_price,
    })

    logger.info(
        "Placing STOP_MARKET %s order | symbol=%s | qty=%s | stopPrice=%s",
        side, symbol, quantity, stop_price,
    )
    logger.debug("Stop-market order params: %s", params)

    raw = client.post(ORDER_ENDPOINT, params)
    parsed = parse_order_response(raw)

    logger.info(
        "STOP_MARKET order placed | orderId=%s | status=%s | stopPrice=%s",
        parsed["orderId"], parsed["status"], parsed["stopPrice"],
    )
    return parsed


# ── Master dispatcher ─────────────────────────────────────────────────────────

def place_order(
        client: BinanceClient,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        stop_price: float | None = None,
) -> dict[str, Any]:

    if order_type == "MARKET":
        return place_market_order(client, symbol, side, quantity)

    elif order_type == "LIMIT":
        return place_limit_order(client, symbol, side, quantity, price)

    elif order_type == "STOP_MARKET":
        return place_stop_market_order(client, symbol, side, quantity, stop_price)

    else:
        raise ValueError(f"Unsupported order type: {order_type}")

