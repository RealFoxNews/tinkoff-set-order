from typing import Optional

import tinkoff.invest
from tinkoff.invest import AccessLevel, AccountStatus, InstrumentIdType
from tinkoff.invest.async_services import AsyncServices

from src import settings
from src.containers.config import TraderConfig
from src.service.errors import ConfigError


async def prepare_trader_config(config: dict) -> TraderConfig:
    config['quantity'] = settings.ORDER_QUANTITY
    config['ticker'] = settings.ORDER_TICKER
    config['units'] = settings.ORDER_UNITS
    config['nano'] = settings.ORDER_NANO
    config['direction'] = settings.ORDER_DIRECTION
    config["decision_interval_s"] = float(settings.INTERVAL_SECONDS)

    ticker = config["ticker"]
    class_code = config["class_code"]

    async with tinkoff.invest.AsyncClient(
        settings.INVEST_TOKEN, sandbox_token=settings.SANDBOX_TOKEN, app_name=settings.APP_NAME
    ) as services:
        # get id of the user account
        account_id = await _fetch_user_account_id(services, target_account_id=settings.ACCOUNT_ID)

        # info = (await services.instruments.shares())
        # TODO: check schedule, buy, sell and api trade flags (MarketDataService.GetTradingStatus first)
        # check that the instrument is currently available for trading
        instrument_data = (
            await services.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER, id=ticker, class_code='TQCB'
            )
        ).instrument
        # schedule = await services.instruments.trading_schedules(
        #     from_=datetime.datetime.utcnow(),
        #     to=datetime.datetime.utcnow() + datetime.timedelta(days=5),
        #     exchange=instrument_data.exchange,
        # )

        instrument_figi = instrument_data.figi

    return TraderConfig(account_id=account_id, instrument_figi=instrument_figi, config=config)


async def _fetch_user_account_id(services: AsyncServices, *, target_account_id: Optional[str]) -> str:
    accounts = (await services.users.get_accounts()).accounts
    if target_account_id is not None:
        try:
            account = next(acc for acc in accounts if acc.id == target_account_id)
        except StopIteration:
            raise ConfigError("Specified account id is not found for the given token")
    else:
        if len(accounts) > 1:
            raise ConfigError(
                "Multiple accounts found for the token. "
                "Please, specify the concrete one with the ACCOUNT_ID env variable."
            )
        account = accounts[0]

    # verify rights on the account
    if account.access_level != AccessLevel.ACCOUNT_ACCESS_LEVEL_FULL_ACCESS:
        raise ConfigError("The access token does not have full access to the account")
    if account.status != AccountStatus.ACCOUNT_STATUS_OPEN:
        raise ConfigError("Can not operate on the account with incorrect status")

    return account.id
