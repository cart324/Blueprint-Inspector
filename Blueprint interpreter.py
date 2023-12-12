import discord
from discord.ext import commands
import asyncio
import os
import sys
import shutil
import stat
import traceback
import time

client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

with open('token.txt', 'r') as f:
    token = f.read()

client.load_extension("cogs.Inspector")


def on_rm_error(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


paths_list = [["Blueprint-Inspector/cogs", "cogs"], ["Blueprint-Inspector/data", "data"]]  # [옮길 파일 위치, 옮겨질 위치]


@client.command()
async def restart(ctx):
    try:
        await ctx.send('봇이 재시작됩니다.')
        now = str(time.strftime('%Y.%m.%d %H:%M:%S - '))
        print(now + "Received restart command, user = " + ctx.author.name)
        if os.path.exists("Blueprint-Inspector"):
            shutil.rmtree("Blueprint-Inspector", onerror=on_rm_error)
        os.system("git clone https://github.com/cart324/Blueprint-Inspector")
        for paths in paths_list:
            for (path, dirs, files) in os.walk(paths[0]):
                for file_name in files:
                    if os.path.exists(paths[1] + "/" + file_name):
                        os.remove(paths[1] + "/" + file_name)
                    shutil.move(paths[0] + "/" + file_name, paths[1] + "/" + file_name)
        shutil.rmtree("Blueprint-Inspector", onerror=on_rm_error)
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception:
        error_log = traceback.format_exc(limit=None, chain=True)
        cart = client.get_user(344384179552780289)
        await cart.send("```" + "\n" "사용자 = " + ctx.author.name + "\n" + str(error_log) + "```")

client.run(token)
