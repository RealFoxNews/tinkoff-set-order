import os

INVEST_TOKEN = os.getenv("INVEST_TOKEN")
SANDBOX_TOKEN = os.getenv("SANDBOX_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
APP_NAME = os.getenv("APP_NAME")

FIGI = os.getenv("FIGI")

ORDER_DIRECTION = os.getenv("ORDER_DIRECTION")
ORDER_TICKER = os.getenv("ORDER_TICKER")
ORDER_PRICE = os.getenv("ORDER_PRICE")
ORDER_QUANTITY = os.getenv("ORDER_QUANTITY")

assert INVEST_TOKEN is not None
assert SANDBOX_TOKEN is not None
