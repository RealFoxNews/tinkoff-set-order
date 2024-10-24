from typing import List

from tinkoff.invest import OrderType, OrderDirection, Quotation

from src.containers.market import TraderDecision, MarketState, CreateOrder
from src.traders.base import BaseTrader


class EMATrader(BaseTrader):
    _trader_name = "ema"

    async def make_decisions(self) -> List[TraderDecision]:
        rr = CreateOrder()
        CreateOrder.order_type = OrderType(1)
        CreateOrder.order_direction = OrderDirection(2)
        CreateOrder.price = Quotation(units=self.trader_config.config['units'], nano=self.trader_config.config['nano'])
        CreateOrder.quantity = self.trader_config.config['quantity']
        return [rr]