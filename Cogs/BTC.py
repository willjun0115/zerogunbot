import os

import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
import operator
from datetime import datetime
import time
import pyupbit
import numpy as np


def get_target_price(ticker, k=0.5):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price


def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time


def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15


def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0


def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]


def get_ror(k=0.5):
    df = pyupbit.get_ohlcv("KRW-BTC", count=7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'],
                         1)

    ror = df['ror'].cumprod()[-2]
    return ror


def find_best_k():
    best_k = 0.5
    best_ror = 0
    for k in np.arange(0.1, 1.0, 0.1):
        ror = get_ror(k)
        if best_ror < ror:
            best_ror = ror
            best_k = k
    return best_k


class BTC(commands.Cog, name="비트코인", description="비트코인 조회에 관련된 카테고리입니다."):

    def __init__(self, app):
        self.app = app

    @commands.command(
        name="비트코인", aliases=["BTC"],
        help="업비트 코인 정보를 조회합니다.",
        usage="* (str(*ticker*))"
    )
    async def bitcoin(self, ctx, ticker='KRW-BTC'):
        embed = discord.Embed(title="<업비트>", description=ticker + " 정보 조회")
        embed.add_field(name="현재가", value=f"{get_current_price(ticker)}", inline=False)
        embed.add_field(name="ma15", value=f"{get_ma15(ticker)}", inline=False)
        await ctx.send(embed=embed)


access = os.environ.get('ACCESS')
secret = os.environ.get('SECRET')
if access and secret:
    upbit = pyupbit.Upbit(access, secret)


def setup(app):
    app.add_cog(BTC(app))