from discord.ext import commands
from typing import Union, Callable, Any


class InsufficientTokensError(commands.CheckFailure):
    """유료 명령어 실행 시 보유 토큰이 부족할 때 발생하는 예외."""
    def __init__(self, cost: int, current: int):
        self.cost = cost
        self.current = current
        super().__init__(f"토큰이 부족합니다. (필요: {cost} :coin: / 보유: {current} :coin:)")


class UserNotRegisteredError(commands.CheckFailure):
    """유료 명령어 실행 시 사용자가 DB에 등록되지 않았을 때 발생하는 예외."""
    def __init__(self):
        super().__init__("등록되지 않은 사용자입니다. `%등록` 명령어로 먼저 등록해주세요.")


class NotInVoiceChannelError(commands.CheckFailure):
    """음성 채널에 입장하지 않은 상태에서 음성 명령어를 실행할 때 발생하는 예외."""
    def __init__(self):
        super().__init__("먼저 음성 채널에 입장해 주세요.")


def require_voice():
    """사용자가 음성 채널에 연결되어 있는지 사전에 확인하는 커스텀 체크 데코레이터."""
    async def predicate(ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise NotInVoiceChannelError()
        return True
    return commands.check(predicate)


def token_cost(cost: int):
    """
    명령어 실행 시 토큰을 소모하도록 지정하는 데코레이터.
    - @commands.command 위 또는 아래 어디에 두어도 동작합니다.
    - 실행 전 유저의 잔여 토큰(cost 이상)을 사전 검증하여 부족 시 InsufficientTokensError를 발생시킵니다.
    - 인자 파싱 및 쿨타임, 권한 검사가 정상 통과된 후, 실제 함수 호출 직전(before_invoke)에
      원자적(atomic SQL UPDATE)으로 토큰을 차감합니다.
    - 동시 요청(Race Condition)으로 인한 잔액 초과 소모를 원천 차단합니다.
    - 도움말 시스템(%도움말)에서 감지할 수 있도록 command 및 callback에 token_cost 속성을 저장합니다.
    """
    async def predicate(*args):
        ctx = args[-1]
        db = getattr(ctx.bot, 'db', None)
        if db is None:
            return True
        coins = await db.get_coins(ctx.author.id)
        if coins is None:
            raise UserNotRegisteredError()
        if coins < cost:
            raise InsufficientTokensError(cost, coins)
        return True

    async def charge_fee(*args):
        ctx = args[-1]
        db = getattr(ctx.bot, 'db', None)
        if db is not None:
            success, balance = await db.consume_coins(ctx.author.id, cost)
            if not success:
                if balance is None:
                    raise UserNotRegisteredError()
                else:
                    raise InsufficientTokensError(cost, balance)

    def decorator(func_or_cmd):
        func_or_cmd.token_cost = cost
        if isinstance(func_or_cmd, commands.Command):
            func_or_cmd.add_check(predicate)
            func_or_cmd.before_invoke(charge_fee)
            func_or_cmd.callback.token_cost = cost
        else:
            if not hasattr(func_or_cmd, '__commands_checks__'):
                func_or_cmd.__commands_checks__ = []
            func_or_cmd.__commands_checks__.append(predicate)
            func_or_cmd.__before_invoke__ = charge_fee
        return func_or_cmd

    return decorator


# 하위 호환 및 가독성을 위한 별칭
paid_command = token_cost

