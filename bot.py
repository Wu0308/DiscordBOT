import discord
from discord.ext import commands
import openai
import requests
from bs4 import BeautifulSoup
import random
from duckduckgo_search import DDGS
import os
from keep_alive import keep_alive
import asyncio
from datetime import datetime
import yt_dlp
from discord import FFmpegPCMAudio

keep_alive()  # 在 bot 啟動前呼叫，這樣就會開一個 web port 給 Render 看

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

# 使用 yt_dlp 搜尋並取得音訊 URL
def search_youtube(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0'  # 防止 IPv6 問題
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            video = info['entries'][0] if 'entries' in info else info
            return {'source': video['url'], 'title': video['title']}
        except Exception as e:
            print(f"❗搜尋錯誤: {e}")
            return None

async def play_next(ctx):
    global now_playing
    if song_queue:
        song = song_queue.pop(0)
        now_playing = song
        vc = ctx.voice_client

        vc.play(
            discord.FFmpegPCMAudio(song['source'], before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"),
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        )
        await ctx.send(f"🎵 現在播放：{song['title']}")
    else:
        now_playing = None
        await ctx.send("📭 歌單已清空。")

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

@bot.command(name="music")
async def music(ctx, *, search: str):
    if not ctx.author.voice:
        await ctx.send("❗請先加入語音頻道")
        return

    voice_channel = ctx.author.voice.channel
    if not ctx.voice_client:
        await voice_channel.connect()

    song = search_youtube(search)
    if song:
        song_queue.append(song)
        await ctx.send(f"✅ 已加入：{song['title']}")

        if not ctx.voice_client.is_playing() and not is_paused:
            await play_next(ctx)
    else:
        await ctx.send("❗找不到這首歌")

@bot.command(name="skip")
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ 已跳過歌曲")
    else:
        await ctx.send("❗沒有正在播放的歌曲")

@bot.command(name="pause")
async def pause(ctx):
    global is_paused
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        is_paused = True
        await ctx.send("⏸️ 已暫停音樂")
    else:
        await ctx.send("❗沒有正在播放的歌曲")

@bot.command(name="play")
async def resume(ctx):
    global is_paused
    if ctx.voice_client and is_paused:
        ctx.voice_client.resume()
        is_paused = False
        await ctx.send("▶️ 繼續播放")
    else:
        await ctx.send("❗目前沒有暫停的音樂")

@bot.command(name="show")
async def show(ctx):
    if now_playing:
        msg = f"🎶 現正播放：{now_playing['title']}\n"
    else:
        msg = "🎶 現在沒有播放的音樂\n"

    if song_queue:
        msg += "\n📜 歌單：\n" + "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(song_queue)])
    else:
        msg += "\n📭 歌單是空的"

    await ctx.send(msg)

@bot.command(name="leave")
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        song_queue.clear()
        await ctx.send("👋 已離開語音頻道")

        
# help顯示指令提示
@bot.command()
async def help(ctx):
    help_text = """
📘 **指令說明列表：**
`[]`表示必填 `{}`表示選填

`!hello` - 和機器人打招呼  
`!mom` - 幹你媽  
`!add [數字1] [數字2]` - 加法計算
`!ask [問題]` - 問 ChatGPT 一個問題  
`!image [關鍵字] {數量}` - 搜尋圖片並隨機顯示結果
`!video [關鍵字] {數量}` - 搜尋影片並依順序顯示結果
`!search [關鍵字] {數量}` - 搜尋網頁並回傳指定筆數的結果
`!remind [月/日] [時:分] [提醒內容]` - 設定提醒功能
`!music [音樂]` - 加入音樂到撥放清單
`!show` - 顯示音樂播放清單
`!pause` - 暫停撥放
`!play` - 繼續撥放
`!skip` - 跳過這首歌 

👉 範例：
- `!image 狗 3`
- `!video 夜景 5`
- `!ask 寫一首詩給我`
- `!remind 4/13 17:00 聚會`
- `!music 周杰倫`

"""
    await ctx.send(help_text)




# 啟動機器人
bot.run(discord_token)
