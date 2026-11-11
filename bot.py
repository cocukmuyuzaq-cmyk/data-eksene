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
# İKİ SUNUCU ID'Sİ BURADA
ALLOWED_GUILD_IDS = [1564299296097050855, 1563560298596536453]

# tfLink'ten aldığınız downloadLinkEncoded'ı Render Environment'a DATA_URL olarak ekleyin
DATA_URL = os.getenv("DATA_URL")

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
        # Sunucu kontrolü (Güncellendi: not in ALLOWED_GUILD_IDS)
        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        if not DATA_URL:
            await interaction.followup.send("❌ `DATA_URL` environment değişkeni ayarlanmamış.", ephemeral=True)
            return

        # tfLink'ten dosyayı çek (aiohttp kullanarak botun donmasını engelliyoruz)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(DATA_URL, timeout=120) as resp:
                    resp.raise_for_status()
                    content = await resp.text()
        except Exception as e:
            await interaction.followup.send(f"❌ Dosya indirilemedi: `{e}`", ephemeral=True)
            return

        # Satırları ayır ve boş olanları temizle
        all_lines = [satir.strip() for satir in content.splitlines() if satir.strip()]

        if not all_lines:
            await interaction.followup.send("❌ Dosyada veri bulunamadı.", ephemeral=True)
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
    # Sunucu kontrolü (Güncellendi: not in ALLOWED_GUILD_IDS)
    if ctx.guild is None or ctx.guild.id not in ALLOWED_GUILD_IDS:
        return

    embed = discord.Embed(
        title="🕵️‍♂️ Yenilgi Data Paneli",
        description="Aşağıdaki butona tıklayarak tfLink'teki veri dosyasındaki verileri kanala çekebilirsiniz.",
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
