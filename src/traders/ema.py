from typing import List

from tinkoff.invest import OrderType, OrderDirection, Quotation

from src.containers.market import TraderDecision, MarketState, CreateOrder
from src.traders.base import BaseTrader


class EMATrader(BaseTrader):
    _trader_name = "ema"

    async def make_decisions(self) -> List[TraderDecision]:
        rr = CreateOrder()
        CreateOrder.order_type = OrderType(1)
        CreateOrder.order_direction = OrderDirection(2 if self.trader_config.config['direction'] == 'sell' else 1)
        CreateOrder.price = Quotation(units=int(self.trader_config.config['units']), nano=int(self.trader_config.config['nano']))
        print(int(self.trader_config.config['nano']))
        print(CreateOrder.price)
        CreateOrder.quantity = int(self.trader_config.config['quantity'])
        return [rr]