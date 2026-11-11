import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
from flask import Flask
from threading import Thread

# ==================== RENDER İÇİN SAHTE WEB SUNUCUSU ====================
app = Flask('')

@app.route('/')
def home():
    return "Data Botu Aktif!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

# ==================== BOT AYARLARI ====================
TOKEN = os.getenv("TOKEN")
ALLOWED_GUILD_IDS = [1564299296097050855, 1563560298596536453]

# 5 ADET VERİ LİNKİ (Render Environment'a DATA_URL_1, DATA_URL_2, DATA_URL_3, DATA_URL_4, DATA_URL_5 olarak ekle)
DATA_URL_1 = os.getenv("DATA_URL_1")
DATA_URL_2 = os.getenv("DATA_URL_2")
DATA_URL_3 = os.getenv("DATA_URL_3")
DATA_URL_4 = os.getenv("DATA_URL_4")
DATA_URL_5 = os.getenv("DATA_URL_5")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# RESİM VE REKLAM
IMAGE_URL = "https://cdn.discordapp.com/attachments/1566040841150140477/1568589689072517201/image0.jpg?ex=6af05e7c&is=6aef0cfc&hm=2ba98ebe9a1b762f154d732a13a478165a8d0fae0929392899608834df3d033c&"
FOOTER_TEXT = "discord.gg/yenilgi"

# ==================== BUTON SİSTEMİ ====================
class DataView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Discord Data Çek", style=discord.ButtonStyle.green, emoji="📁")
    async def data_cek(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Sadece dolu olan linkleri toparla
        urls = [url for url in [DATA_URL_1, DATA_URL_2, DATA_URL_3, DATA_URL_4, DATA_URL_5] if url]

        if not urls:
            await interaction.followup.send("❌ Hiçbir veri linki (`DATA_URL_X`) ayarlanmamış.", ephemeral=True)
            return

        await interaction.followup.send(f"⏳ {len(urls)} adet dosya indiriliyor, lütfen bekleyin...", ephemeral=True)

        all_lines = []

        try:
            async with aiohttp.ClientSession() as session:
                for i, url in enumerate(urls, 1):
                    try:
                        async with session.get(url, timeout=120) as resp:
                            resp.raise_for_status()
                            content = await resp.text()
                            lines = [satir.strip() for satir in content.splitlines() if satir.strip()]
                            all_lines.extend(lines)
                    except Exception as e:
                        await interaction.followup.send(f"⚠️ {i}. link indirilemedi, atlanıyor: `{e}`", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ İndirme işlemi sırasında kritik hata: `{e}`", ephemeral=True)
            return

        if not all_lines:
            await interaction.followup.send("❌ İndirilen dosyalarda veri bulunamadı.", ephemeral=True)
            return

        await interaction.followup.send(f"🚀 Toplam {len(all_lines)} veri bulundu. Kanala yazılıyor (1 sn aralıklarla)...", ephemeral=True)

        # Kanala sırayla yaz
        for line in all_lines:
            embed = discord.Embed(
                title="📁 Yenilgi Data",
                description=f"```yaml\n{line}\n```",
                color=0x5865F2
            )
            embed.set_image(url=IMAGE_URL)
            embed.set_footer(text=FOOTER_TEXT)

            try:
                await interaction.channel.send(embed=embed)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Mesaj gönderme hatası: {e}")
                await asyncio.sleep(2)

# ==================== KOMUT ====================
@bot.event
async def on_ready():
    print(f"✅ Data Botu hazır: {bot.user}")
    await bot.change_presence(activity=discord.Game(name=f"!menü | {FOOTER_TEXT}"))

@bot.command(name="menü", aliases=["menu"])
async def menu(ctx):
    if ctx.guild is None or ctx.guild.id not in ALLOWED_GUILD_IDS:
        return

    embed = discord.Embed(
        title="🕵️‍♂️ Yenilgi Data Paneli",
        description="Aşağıdaki butona tıklayarak veri dosyalarındaki verileri kanala çekebilirsiniz.",
        color=0x5865F2
    )
    embed.set_image(url=IMAGE_URL)
    embed.set_footer(text=FOOTER_TEXT)

    await ctx.send(embed=embed, view=DataView())

# ==================== ÇALIŞTIR ====================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ HATA: TOKEN bulunamadı! Render'da TOKEN değişkenini kontrol et.")
    else:
        keep_alive()
        bot.run(TOKEN)
