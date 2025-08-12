import asyncio
import datetime
import uuid
import sys
import time

import tinkoff.invest

from src import settings
from src.containers.config import TraderConfig
from src.containers.market import (
    AccountBalance,
    CancelOrder,
    CreateOrder,
    MarketData,
    MarketState,
)
from src.service.errors import DecisionExecutionError
from src.traders.base import BaseTrader


class TraderRunner:
    @classmethod
    async def start_trader_loop(cls, trader: BaseTrader) -> None:
        """Start the trade loop with the given trader."""
        print("The trader has been started")
        decisions = []
        order_sent = False
        while not order_sent:
            try:
                decisions = await trader.make_decisions()
                print(decisions)
                if decisions:
                    order_sent = await cls._execute_trader_decisions(decisions, trader.trader_config)
            except Exception:
                if len(decisions):
                    sys.exit(0)
            if not order_sent:
                await asyncio.sleep(trader.trader_config.config["decision_interval_s"])


    @classmethod
    async def _fetch_current_market_state(cls, trader_config: TraderConfig) -> MarketState:
        async with tinkoff.invest.AsyncClient(
                settings.INVEST_TOKEN, sandbox_token=settings.SANDBOX_TOKEN, app_name=settings.APP_NAME
        ) as services:
            # orders book
            order_book = await services.market_data.get_order_book(
                figi=trader_config.instrument_figi, depth=trader_config.config["order_book_depth"]
            )

            # candles for required period
            now = datetime.datetime.utcnow()
            candles = (
                await services.market_data.get_candles(
                    figi=trader_config.instrument_figi,
                    from_=now - trader_config.candle_timedelta,
                    to=now,
                    interval=trader_config.candle_interval,
                )
            ).candles

            # available balance for the account
            positions = await services.operations.get_positions(account_id=trader_config.account_id)

            # orders
            orders = (await services.orders.get_orders(account_id=trader_config.account_id)).orders

            return MarketState(
                account_balance=AccountBalance(
                    money=positions.money,
                    securities=positions.securities,
                ),
                market_data=MarketData(
                    bids=order_book.bids,
                    asks=order_book.asks,
                    candles=candles,
                ),
                opened_orders=orders,
            )

    @classmethod
    async def _execute_trader_decisions(cls, decisions, trader_config):
        success = False
        async with tinkoff.invest.AsyncClient(
                settings.INVEST_TOKEN, sandbox_token=settings.SANDBOX_TOKEN, app_name=settings.APP_NAME
        ) as services:
            tasks = [
                cls._execute_decision(services, trader_config, decision)
                for decision in decisions
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    print("error executing decision")
                elif result is not None:
                    success = True

        return success

    @classmethod
    async def _execute_decision(cls, client, trader_config, decision):
        if isinstance(decision, CreateOrder):
            try:
                start_time_ns = time.perf_counter_ns()
                response = await client.orders.post_order(
                    order_id=str(uuid.uuid4()),
                    figi=trader_config.instrument_figi,
                    account_id=trader_config.account_id,
                    # decision
                    order_type=decision.order_type,
                    direction=decision.order_direction,
                    price=decision.price,
                    quantity=decision.quantity,
                )
                elapsed_ms = (time.perf_counter_ns() - start_time_ns) / 1_000_000
                print(f"Order posted in {elapsed_ms:.2f} ms")
                return response
            except Exception as exc:
                print("unable to post the order", str(exc))
        elif isinstance(decision, CancelOrder):
            try:
                return await client.orders.cancel_order(account_id=trader_config.account_id, order_id=decision.order_id)
            except Exception as exc:
                print("unable to cancel the order", str(exc))
        else:
            print("Unsupported decision type", type(decision))

    @classmethod
    async def _log_algorithm_decision(cls, trader_config, decision, response):
        with open(f"logs/{trader_config.account_id}.log", "a") as f:
            f.write(str(decision) + str(response))
