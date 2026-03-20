

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceAPIError, BinanceClient
from bot.logging_config import setup_logger
from bot.orders import place_order, print_order_summary
from bot.validators import validate_order_inputs

load_dotenv()
logger = setup_logger()


def print_banner() -> None:
    print("""
============================================
    Binance Futures Testnet  Trading Bot             
============================================
""")


def print_request_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None,
    stop_price: float | None,
) -> None:
    print("\n── Order Request -------------------------\n")
    print(f"  Symbol     : {symbol}")
    print(f"  Side       : {side}")
    print(f"  Type       : {order_type}")
    print(f"  Quantity   : {quantity}")
    if price:
        print(f"  Price      : {price}")
    if stop_price:
        print(f"  Stop Price : {stop_price}")
    print("-------------------------------------------\n")


# Interactive mode

def prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value  = input(f"  {label}{suffix}: ").strip()
    return value if value else (default or "")


def run_interactive() -> dict:

    print("\n  Fill in the order details (press Enter to accept [default]):\n")

    while True:
        symbol = prompt("Symbol (e.g. BTCUSDT)").upper()
        if symbol:
            break
        print("Symbol cannot be empty.\n")

    while True:
        side = prompt("Side (BUY / SELL)").upper()
        if side in ("BUY", "SELL"):
            break
        print("Please enter BUY or SELL.\n")

    while True:
        order_type = prompt("Order type (MARKET / LIMIT / STOP_MARKET)").upper()
        if order_type in ("MARKET", "LIMIT", "STOP_MARKET"):
            break
        print("Please enter MARKET, LIMIT, or STOP_MARKET.\n")

    while True:
        try:
            quantity = float(prompt("Quantity (e.g. 0.01)"))
            if quantity > 0:
                break
            print("Quantity must be greater than 0.\n")
        except ValueError:
            print("Please enter a valid number.\n")

    price = None
    if order_type in ("LIMIT",):
        while True:
            try:
                price = float(prompt("Limit price"))
                if price > 0:
                    break
                print("  ⚠  Price must be greater than 0.\n")
            except ValueError:
                print("  ⚠  Please enter a valid number.\n")

    stop_price = None
    if order_type == "STOP_MARKET":
        while True:
            try:
                stop_price = float(prompt("Stop price"))
                if stop_price > 0:
                    break
                print("  ⚠  Stop price must be greater than 0.\n")
            except ValueError:
                print("  ⚠  Please enter a valid number.\n")

    return {
        "symbol":     symbol,
        "side":       side,
        "order_type": order_type,
        "quantity":   quantity,
        "price":      price,
        "stop_price": stop_price,
    }


# Argument parser

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=""
    )

    parser.add_argument("--symbol",     type=str,   help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side",       type=str,   help="BUY or SELL")
    parser.add_argument("--type",       type=str,   dest="order_type", help="MARKET | LIMIT | STOP_MARKET")
    parser.add_argument("--quantity",   type=float, help="Order quantity")
    parser.add_argument("--price",      type=float, help="Limit price (required for LIMIT orders)")
    parser.add_argument("--stop-price", type=float, dest="stop_price", help="Stop trigger price (for STOP_MARKET)")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive / guided mode")
    parser.add_argument("--balance",    action="store_true", help="Show account balance and exit")
    parser.add_argument("--price-check", type=str,  dest="price_check", metavar="SYMBOL",
                        help="Show current mark price for SYMBOL and exit")

    return parser


# Main

def main() -> None:
    print_banner()

    # Load credentials
    api_key    = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")

    if not api_key or not api_secret:
        print("API_KEY and API_SECRET must be set in your .env file.")
        logger.error("Missing API credentials. Check your .env file.")
        sys.exit(1)

    # Build client
    client = BinanceClient(api_key, api_secret)

    parser = build_parser()
    args   = parser.parse_args()

    # Utility commands

    if args.balance:
        try:
            balances = client.get_balance()
            print("\n-- Account Balance ------------------------")
            for b in balances:
                if float(b.get("balance", 0)) > 0:
                    print(f"  {b['asset']:10} | Balance: {b['balance']:>18} | Available: {b['availableBalance']}")
            print()
        except Exception as exc:
            print(f"Failed to fetch balance: {exc}")
        return

    if args.price_check:
        try:
            price = client.get_price(args.price_check.upper())
            print(f"\n  {args.price_check.upper()} current price: {price}\n")
        except Exception as exc:
            print(f"Failed to fetch price: {exc}")
        return

    #Gather inputs

    if args.interactive:
        inputs = run_interactive()
    else:
        # All order fields required in non-interactive mode
        missing = [f for f in ("symbol", "side", "order_type", "quantity")
                   if not getattr(args, f.replace("order_type", "order_type"), None)]
        # re-check properly
        missing = []
        if not args.symbol:     missing.append("--symbol")
        if not args.side:       missing.append("--side")
        if not args.order_type: missing.append("--type")
        if not args.quantity:   missing.append("--quantity")

        if missing:
            print(f"Missing required arguments: {', '.join(missing)}")
            print("   Run with --interactive for guided mode, or --help for usage.\n")
            sys.exit(1)

        inputs = {
            "symbol":     args.symbol,
            "side":       args.side,
            "order_type": args.order_type,
            "quantity":   args.quantity,
            "price":      args.price,
            "stop_price": args.stop_price,
        }

    # Validate 

    try:
        validated = validate_order_inputs(**inputs)
    except ValueError as exc:
        print(f"\nValidation error: {exc}\n")
        logger.warning("Validation failed: %s | inputs=%s", exc, inputs)
        sys.exit(1)

    #  Show request summary

    print_request_summary(
        symbol     = validated["symbol"],
        side       = validated["side"],
        order_type = validated["order_type"],
        quantity   = validated["quantity"],
        price      = validated["price"],
        stop_price = validated["stop_price"],
    )

    confirm = input("Confirm order? (yes/no) [yes]: ").strip().lower()
    if confirm in ("no", "n"):
        print("\n  Order cancelled.\n")
        logger.info("Order cancelled by user.")
        sys.exit(0)

    #Place orde

    try:
        result = place_order(
            client     = client,
            symbol     = validated["symbol"],
            side       = validated["side"],
            order_type = validated["order_type"],
            quantity   = validated["quantity"],
            price      = validated["price"],
            stop_price = validated["stop_price"],
        )
        print_order_summary(result)

    except BinanceAPIError as exc:
        print(f"\nBinance API Error [{exc.code}]: {exc.msg}\n")
        logger.error("Order failed — BinanceAPIError %s: %s", exc.code, exc.msg)
        sys.exit(1)

    except Exception as exc:
        print(f"\nUnexpected error: {exc}\n")
        logger.exception("Unexpected error during order placement.")
        sys.exit(1)


if __name__ == "__main__":
    main()
