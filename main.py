import discord
from discord.ext import commands
import os
import asyncio
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
# Eğer herkese açık olsun istiyorsan burayı silip veya None yapabilirsin.
# Şimdilik sadece senin sunucun için kilitli bıraktım (1564299296097050855).
ALLOWED_GUILD_ID = 1564299296097050855 

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
        # Sunucu kontrolü
        if interaction.guild is None or interaction.guild.id != ALLOWED_GUILD_ID:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # data.txt dosyasını kontrol et
        if not os.path.exists("data.txt"):
            await interaction.followup.send("❌ `data.txt` dosyası bulunamadı! Lütfen botun olduğu klasöre ekleyin.", ephemeral=True)
            return
            
        with open("data.txt", "r", encoding="utf-8") as f:
            satirlar = [satir.strip() for satir in f.readlines() if satir.strip()]

        if not satirlar:
            await interaction.followup.send("⚠️ `data.txt` dosyası boş.", ephemeral=True)
            return

        await interaction.followup.send(f"✅ Toplam {len(satirlar)} veri bulundu. 1'er saniye arayla kanala yazılıyor...", ephemeral=True)
        
        # Embed ile kanala yaz
        for satir in satirlar:
            embed = discord.Embed(
                title="📁 Yenilgi Data",
                description=f"```yaml\n{satir}\n```",
                color=0x5865F2
            )
            embed.set_image(url=IMAGE_URL)
            embed.set_footer(text=FOOTER_TEXT)
            
            # Mesajı butona basılan kanala gönder
            await interaction.channel.send(embed=embed)
            
            # 1 saniye bekle (Spam engellemek için)
            await asyncio.sleep(1) 

# ==================== KOMUT ====================
@bot.event
async def on_ready():
    print(f"✅ Data Botu hazır: {bot.user}")
    await bot.change_presence(activity=discord.Game(name=f"!menü | {FOOTER_TEXT}"))

@bot.command(name="menü", aliases=["menu"])
async def menu(ctx):
    # Sadece belirtilen sunucuda çalış
    if ctx.guild is None or ctx.guild.id != ALLOWED_GUILD_ID:
        return 

    embed = discord.Embed(
        title="🕵️‍♂️ Yenilgi Data Paneli",
        description="Aşağıdaki butona tıklayarak `data.txt` dosyasındaki verileri kanala çekebilirsiniz.",
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
