import discord
import asyncio
import random
from discord.ext import commands
from discord.utils import get
import openpyxl

def setup(app):
    app.add_cog(Account(app))