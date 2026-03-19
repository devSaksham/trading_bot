from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}

def validate_symbol(symbol):
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if not symbol.isalnum():
        raise ValueError(f"Symbol '{symbol}' must be alphanumeric (e.g. BTCUSDT).")
    return symbol

def validate_sides(symbol):
    symbol = symbol.strip().upper()
    if symbol not in VALID_SIDES:
        raise ValueError(f"Symbol '{symbol}' must be one of {VALID_SIDES}")

    return symbol

def validate_order_type(symbol):
    symbol = symbol.strip().upper()
    if symbol not in VALID_ORDER_TYPES:
        raise ValueError(f"Symbol '{symbol}' must be one of {VALID_ORDER_TYPES}")
    return symbol

def validate_quantity(quantity):
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity must be a number. Got: '{quantity}'")
    if quantity <= 0:
        raise ValueError("Quantity must be positive.")
    return quantity

def validate_price(price, order_type):

    if order_type  == "MARKET":
        return None

    if order_type in ["LIMIT", "STOP_MARKET"]:
        if price is None:
            raise ValueError(f"Price is required for {order_type} orders.")
        try:
            price = float(price)
        except (TypeError, ValueError):
            raise ValueError(f"Price must be a number. Got: '{price}'")
        if price <= 0:
            raise ValueError("Price must be positive.")
        return price

    return None

def validate_stop_price(stop_price, order_type):
    if order_type != "STOP_MARKET":
        return None
    if stop_price is None:
        raise ValueError("stopPrice is required for STOP_MARKET orders.")
    try:
        sp = float(stop_price)
    except (TypeError, ValueError):
        raise ValueError(f"stopPrice must be a number. Got: '{stop_price}'")
    if sp <= 0:
        raise ValueError(f"stopPrice must be greater than 0. Got: {sp}")
    return sp

def validate_parameters(
    symbol, side, order_type, quantity,
    price = None, stop_price = None):

    symbol = validate_symbol(symbol)
    side = validate_sides(side)
    order_type = validate_order_type(order_type)
    quantity = validate_quantity(quantity)
    price = validate_price(price, order_type)
    stop_price = validate_price(stop_price, order_type)

    parameters = {}
    parameters["symbol"] = symbol
    parameters["side"] = side
    parameters["order_type"] = order_type
    parameters["quantity"] = quantity
    parameters["price"] = price
    parameters["stop_price"] = stop_price
    return parameters


