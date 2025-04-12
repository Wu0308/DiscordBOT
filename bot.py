import discord
from discord.ext import commands
import openai
import requests
from bs4 import BeautifulSoup
import random
from duckduckgo_search import DDGS

#環境變數API Key
openai_api_key = os.environ["OPENAI_API_KEY"]
discord_token = os.environ["DISCORD_TOKEN"]

# 初始化 OpenAI 客戶端（新版本）
client = openai.OpenAI(api_key=openai_api_key)

# 建立 Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'🤖 Bot 已上線：{bot.user}')

# 基本對話指令
@bot.command()
async def hello(ctx):
    await ctx.send('你好我叫做余俊賢')

# 隨機罵人
@bot.command()
async def mom(ctx):
    replies = [
        "幹你娘 😡",
        "操你媽 😤",
        "去給狗幹 😢",
        "你媽死了🧎‍♂️",
        "跟你媽做愛‍♂️",
        "你娘老雞掰",
        "我愛你",
    ]
    await ctx.send(random.choice(replies))

@bot.command()
async def add(ctx, a: int, b: int):
    await ctx.send(f'{a} 加 {b} 等於 {a + b}')

# 問 ChatGPT 問題
@bot.command()
async def ask(ctx, *, question):
    await ctx.send("🧠 Thinking...")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個Discord 機器人助手，你的名字叫做余俊賢"},
                {"role": "user", "content": question}
            ]
        )
        answer = response.choices[0].message.content
        await ctx.send(answer)

    except Exception as e:
        await ctx.send(f"錯誤發生了：{e}")

# 搜尋圖片
@bot.command()
async def image(ctx, *, query: str):
    params = query.split()
    try:
        count = int(params[-1])
        keyword = " ".join(params[:-1])
    except ValueError:
        count = 1
        keyword = query

    await ctx.send(f"🔍 正在搜尋：{keyword} 的圖片，隨機顯示 {count} 張...")

    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(keyword, safesearch="off", region='tw-tzh', max_results=100))  # 先抓最多 100 張圖片
            if results:
                random.shuffle(results)  # 打亂順序
                selected = results[:count]  # 選取前 count 張
                for result in selected:
                    await ctx.send(result["image"])  # 發送圖片連結
            else:
                await ctx.send("找不到圖片 😢")
    except Exception as e:
        await ctx.send(f"⚠️ 發生錯誤：{e}")
        
# 搜尋影片
@bot.command()
async def video(ctx, *, query: str):
    params = query.split()
    try:
        count = int(params[-1])
        keyword = " ".join(params[:-1])
    except ValueError:
        count = 1
        keyword = query

    await ctx.send(f"🎬 正在搜尋：{keyword} 的影片，依順序顯示 {count} 部...")

    try:
        with DDGS() as ddgs:
            results = list(ddgs.videos(keyword, safesearch="off", region='tw-tzh', max_results=100))
            if results:
                selected = results[:count]
                for result in selected:
                    await ctx.send(result["content"])  # 發送影片連結
            else:
                await ctx.send("找不到影片 😢")
    except Exception as e:
        await ctx.send(f"⚠️ 發生錯誤：{e}")
        
# 搜尋關鍵字並回傳多筆結果
@bot.command()
async def search(ctx, *, query: str):
    params = query.split()
    try:
        count = int(params[-1])
        keyword = " ".join(params[:-1])
    except ValueError:
        count = 1
        keyword = query

    await ctx.send(f"🔍 正在搜尋：{keyword}，回傳前 {count} 筆結果...")

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(keyword, safesearch="off", region='tw-tzh', max_results=100))
            if results:
                for result in results[:count]:
                    title = result.get("title", "無標題")
                    href = result.get("href", "無連結")
                    await ctx.send(f"🔗 **{title}**\n{href}")
            else:
                await ctx.send("找不到搜尋結果 😢")
    except Exception as e:
        await ctx.send(f"⚠️ 發生錯誤：{e}")

import asyncio
from datetime import datetime

@bot.command()
async def remind(ctx, month_day: str, time_str: str, *, reminder: str):
    try:
        # 解析時間
        full_time_str = f"{month_day} {time_str}"
        remind_time = datetime.strptime(full_time_str, "%m/%d %H:%M")

        # 加上今年年份
        now = datetime.now()
        remind_time = remind_time.replace(year=now.year)

        # 如果時間已過，則提醒時間為明年
        if remind_time < now:
            remind_time = remind_time.replace(year=now.year + 1)

        # 計算等待秒數
        wait_seconds = (remind_time - now).total_seconds()

        await ctx.send(f"⏰ 好的！我會在 {remind_time.strftime('%m/%d %H:%M')} 提醒你：{reminder}")

        await asyncio.sleep(wait_seconds)
        await ctx.send(f"🔔 {ctx.author.mention} 提醒你：{reminder}")

    except ValueError:
        await ctx.send("⚠️ 時間格式錯誤，請使用 `!remind 月/日 時:分 內容`，例如：`!remind 4/13 21:30 看電影`")
    except Exception as e:
        await ctx.send(f"⚠️ 發生錯誤：{e}")



        
# help顯示指令提示
@bot.command()
async def help(ctx):
    help_text = """
📘 **指令說明列表：**

`!hello` - 和機器人打招呼  
`!mom` - 幹你媽  
`!add [數字1] [數字2]` - 加法計算
`!ask [問題]` - 問 ChatGPT 一個問題  
`!image [關鍵字] [數量]` - 搜尋圖片並隨機顯示結果
`!video [關鍵字] [數量]` - 搜尋影片並依順序顯示結果
`!search [關鍵字] [數量]` - 搜尋網頁並回傳指定筆數的結果
`!remind [月/日] [時:分] [提醒內容]` - 設定提醒功能 

👉 範例：
- `!image 狗`
- `!image 夜景 5`
- `!ask 寫一首詩給我`
- `!remind [4/13 17:00] [聚會]`

"""
    await ctx.send(help_text)




# 啟動機器人
bot.run(discord_token)
