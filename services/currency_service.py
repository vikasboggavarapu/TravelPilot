"""
TravelPilot — Currency Service
Handles currency scaling, symbol formatting, and exchange rate estimations.
"""

CURRENCY_SYMBOLS: dict[str, str] = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "AUD": "A$",
    "CAD": "C$",
    "CHF": "CHF",
    "SGD": "S$",
    "AED": "AED",
}

# Approximate conversion scale relative to 1 USD benchmark
CURRENCY_SCALES_TO_USD: dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.78,
    "INR": 88.0,
    "JPY": 150.0,
    "AUD": 1.55,
    "CAD": 1.38,
    "CHF": 0.88,
    "SGD": 1.35,
    "AED": 3.67,
}


def get_currency_symbol(currency: str) -> str:
    """Returns the visual symbol for a currency code (e.g. ₹ for INR)."""
    return CURRENCY_SYMBOLS.get((currency or "").upper(), currency or "₹")


def get_currency_scale(currency: str) -> float:
    """Returns scale factor relative to USD benchmark (e.g. 88.0 for INR)."""
    return CURRENCY_SCALES_TO_USD.get((currency or "").upper(), 1.0)


def scale_amount(base_usd_amount: float, currency: str) -> float:
    """Scale a benchmark USD amount into target currency units."""
    scale = get_currency_scale(currency)
    return round(base_usd_amount * scale, 2)


def format_money(amount: float, currency: str) -> str:
    """Format money cleanly with appropriate symbol or code."""
    sym = get_currency_symbol(currency)
    if sym != currency:
        return f"{sym}{amount:,.0f}"
    return f"{currency} {amount:,.0f}"
