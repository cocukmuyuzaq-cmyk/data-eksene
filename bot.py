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
    return "Bot Aktif!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

# ==================== BOT AYARLARI ====================
TOKEN = os.getenv("TOKEN")
ALLOWED_GUILD_IDS = [1564299296097050855, 1563560298596536453]

# Sorgu API'leri
API_BASE_1 = "https://wazely.vercel.app/api"
API_BASE_2 = "https://wazelyapi.vercel.app/api"
ID_API = "https://prox0959.netlify.app/api/search?id="

# Data Linkleri (Environment'tan okunur)
DATA_URL_1 = os.getenv("DATA_URL_1")
DATA_URL_2 = os.getenv("DATA_URL_2")
DATA_URL_3 = os.getenv("DATA_URL_3")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# RESİM VE REKLAM
IMAGE_URL = "https://cdn.discordapp.com/attachments/1566040841150140477/1568589689072517201/image0.jpg?ex=6af05e7c&is=6aef0cfc&hm=2ba98ebe9a1b762f154d732a13a478165a8d0fae0929392899608834df3d033c&"
FOOTER_TEXT = "discord.gg/yenilgi"

# ==================== FİLTRE ====================
def temizle(data):
    if isinstance(data, dict):
        return {k: temizle(v) for k, v in data.items() if k.lower() not in ['dev', 'author', 'provider', 'credit']}
    elif isinstance(data, list):
        return [temizle(i) for i in data]
    return data

# ==================== SORGU MODALLARI ====================
class SorguModal(discord.ui.Modal):
    def __init__(self, title, placeholder, api_url):
        super().__init__(title=title)
        self.api_url = api_url
        self.sorgu = discord.ui.TextInput(
            label="Sorgu Değeri",
            placeholder=placeholder,
            required=True,
            max_length=100
        )
        self.add_item(self.sorgu)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        deger = self.sorgu.value
        target_url = f"{self.api_url}{deger}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(target_url, timeout=20) as resp:
                    if resp.status != 200:
                        await interaction.followup.send(f"❌ Sorgu Hatası: HTTP {resp.status}", ephemeral=True)
                        return
                    try:
                        data = await resp.json()
                    except:
                        data = await resp.text()

            if not data:
                await interaction.followup.send("⚠️ Sonuç bulunamadı.", ephemeral=True)
                return

            temiz_data = temizle(data)
            sonuc_str = json.dumps(temiz_data, indent=2, ensure_ascii=False) if isinstance(temiz_data, dict) else str(temiz_data)

            if len(sonuc_str) > 1900:
                dosya = discord.File(io.BytesIO(sonuc_str.encode('utf-8')), filename=f"{self.title.replace(' ', '_').lower()}_log.txt")
                embed = discord.Embed(title=f"✅ Sorgu Sonucu: {self.title}", description="Log çok büyük olduğu için dosya olarak gönderildi.", color=0x00E676)
                embed.set_image(url=IMAGE_URL)
                embed.set_footer(text=FOOTER_TEXT)
                await interaction.user.send(embed=embed, file=dosya)
                await interaction.followup.send("✅ Sonuç dosya olarak DM'nize gönderildi!", ephemeral=True)
                return

            embed = discord.Embed(title=f"✅ Sorgu Sonucu: {self.title}", description=f"```json\n{sonuc_str}\n```", color=0x00E676)
            embed.set_image(url=IMAGE_URL)
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.user.send(embed=embed)
            await interaction.followup.send("✅ Sonuç özel mesaj (DM) olarak gönderildi!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Beklenmeyen Hata: {str(e)}", ephemeral=True)

class BosSorguModal(discord.ui.Modal):
    def __init__(self, title, api_url):
        super().__init__(title=title)
        self.api_url = api_url

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, timeout=20) as resp:
                    if resp.status != 200:
                        await interaction.followup.send(f"❌ Sorgu Hatası: HTTP {resp.status}", ephemeral=True)
                        return
                    try:
                        data = await resp.json()
                    except:
                        data = await resp.text()
            if not data:
                await interaction.followup.send("⚠️ Sonuç bulunamadı.", ephemeral=True)
                return
            temiz_data = temizle(data)
            sonuc_str = json.dumps(temiz_data, indent=2, ensure_ascii=False) if isinstance(temiz_data, dict) else str(temiz_data)
            if len(sonuc_str) > 1900:
                dosya = discord.File(io.BytesIO(sonuc_str.encode('utf-8')), filename=f"{self.title.replace(' ', '_').lower()}_log.txt")
                embed = discord.Embed(title=f"✅ Sorgu Sonucu: {self.title}", description="Log çok büyük olduğu için dosya olarak gönderildi.", color=0x00E676)
                embed.set_image(url=IMAGE_URL)
                embed.set_footer(text=FOOTER_TEXT)
                await interaction.user.send(embed=embed, file=dosya)
                await interaction.followup.send("✅ Sonuç dosya olarak DM'nize gönderildi!", ephemeral=True)
                return
            embed = discord.Embed(title=f"✅ Sorgu Sonucu: {self.title}", description=f"```json\n{sonuc_str}\n```", color=0x00E676)
            embed.set_image(url=IMAGE_URL)
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.user.send(embed=embed)
            await interaction.followup.send("✅ Sonuç özel mesaj (DM) olarak gönderildi!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Beklenmeyen Hata: {str(e)}", ephemeral=True)

# ==================== SEÇİM MENÜSÜ ====================
class SorguSecim(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="ID Sorgu (Mail/Veri)", description="Discord ID üzerinden veri sızdırır", value="idsorgu"),
            discord.SelectOption(label="Log Çekme", description="Site loglarını çeker", value="log"),
            discord.SelectOption(label="Eczane Sorgu", description="Eczane adından bilgi çeker", value="eczane"),
            discord.SelectOption(label="IP Bilgi", description="IP adresinin konumunu bulur", value="ipinfo"),
            discord.SelectOption(label="DNS Sorgu", description="Domain DNS kayıtlarını çeker", value="dns"),
            discord.SelectOption(label="Bahis Sorgu", description="İsim soyisim ile bahis kaydı arar", value="bahis"),
            discord.SelectOption(label="Plaka Sorgu", description="Plaka üzerinden araç bilgisi bulur", value="plaka"),
            discord.SelectOption(label="MC Bedrock", description="Minecraft Bedrock sunucu durumu", value="bedrock"),
            discord.SelectOption(label="Nitro Üret", description="Rastgele Nitro kodları üretir", value="nitro"),
            discord.SelectOption(label="Exxen Hesap", description="Rastgele Exxen hesabı üretir", value="exxen"),
            discord.SelectOption(label="Predunyam Hesap", description="Rastgele Predunyam hesabı üretir", value="predunyam"),
            discord.SelectOption(label="User Agent", description="Rastgele User-Agent üretir", value="ua"),
            discord.SelectOption(label="CC Gen", description="Rastgele kredi kartı üretir", value="ccgen"),
            discord.SelectOption(label="CC Check", description="Kredi kartı geçerliliğini kontrol eder", value="cccheck"),
            discord.SelectOption(label="Discord Token Check", description="Bot tokenini kontrol eder", value="dctoken"),
            discord.SelectOption(label="Telegram Token Check", description="Telegram tokenini kontrol eder", value="tgtoken"),
        ]
        super().__init__(placeholder="Bir sorgu sistemi seçin...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        secim = self.values[0]

        if secim == "idsorgu":
            await interaction.response.send_modal(SorguModal("ID Sorgu", "Discord ID (Örn: 92433932011724800)", ID_API))
        elif secim == "log":
            await interaction.response.send_modal(SorguModal("Log Çekme", "Site adı (Örn: sahibinden)", f"{API_BASE_1}/trlog?site="))
        elif secim == "eczane":
            await interaction.response.send_modal(SorguModal("Eczane Sorgu", "Eczane Adı", f"{API_BASE_1}/eczane?ad="))
        elif secim == "ipinfo":
            await interaction.response.send_modal(SorguModal("IP Bilgi", "IP Adresi", f"{API_BASE_1}/ipinfo?ip="))
        elif secim == "dns":
            await interaction.response.send_modal(SorguModal("DNS Sorgu", "Domain", f"{API_BASE_1}/dns?domain="))
        elif secim == "bahis":
            await interaction.response.send_modal(SorguModal("Bahis Sorgu", "İsim Soyisim", f"{API_BASE_1}/bahis?isimsoyisim="))
        elif secim == "plaka":
            await interaction.response.send_modal(SorguModal("Plaka Sorgu", "Plaka Kodu", f"{API_BASE_1}/plaka?plate="))
        elif secim == "bedrock":
            await interaction.response.send_modal(SorguModal("MC Bedrock", "Sunucu IP", f"{API_BASE_2}/bedrock?adres="))
        elif secim == "nitro":
            await interaction.response.send_modal(SorguModal("Nitro Üret", "Adet", f"{API_BASE_1}/fakeNitro?count="))
        elif secim == "cccheck":
            await interaction.response.send_modal(SorguModal("CC Check", "Kart", f"{API_BASE_2}/check?data="))
        elif secim == "dctoken":
            await interaction.response.send_modal(SorguModal("Discord Token Check", "Token", f"{API_BASE_2}/dcbottokencheck?token="))
        elif secim == "tgtoken":
            await interaction.response.send_modal(SorguModal("Telegram Token Check", "Token", f"{API_BASE_2}/tgtokencheck?token="))
        elif secim == "exxen":
            await interaction.response.send_modal(BosSorguModal("Exxen Hesap", f"{API_BASE_1}/exxengen"))
        elif secim == "predunyam":
            await interaction.response.send_modal(BosSorguModal("Predunyam Hesap", f"{API_BASE_1}/predunyam"))
        elif secim == "ua":
            await interaction.response.send_modal(BosSorguModal("User Agent", f"{API_BASE_1}/randomuseragent"))
        elif secim == "ccgen":
            await interaction.response.send_modal(BosSorguModal("CC Gen", f"{API_BASE_2}/ccgen"))

# ==================== BUTON SİSTEMİ (DATA ÇEKME) ====================
class DataView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Discord Data Çek", style=discord.ButtonStyle.green, emoji="📁")
    async def data_cek(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        urls = [url for url in [DATA_URL_1, DATA_URL_2, DATA_URL_3] if url]

        if not urls:
            await interaction.followup.send("❌ Hiçbir veri linki (`DATA_URL_1`, `2`, `3`) ayarlanmamış.", ephemeral=True)
            return

        await interaction.followup.send(f"⏳ {len(urls)} adet dosya indiriliyor, lütfen bekleyin...", ephemeral=True)

        all_lines = []
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(urls, 1):
                try:
                    async with session.get(url, timeout=120) as resp:
                        resp.raise_for_status()
                        content = await resp.text()
                        lines = [satir.strip() for satir in content.splitlines() if satir.strip()]
                        all_lines.extend(lines)
                except Exception as e:
                    await interaction.followup.send(f"⚠️ {i}. link indirilemedi: `{e}`", ephemeral=True)

        if not all_lines:
            await interaction.followup.send("❌ Veri bulunamadı.", ephemeral=True)
            return

        await interaction.followup.send(f"🚀 Toplam {len(all_lines)} veri bulundu. Kanala yazılıyor...", ephemeral=True)

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
            except Exception:
                await asyncio.sleep(2)

# ==================== BİRLEŞİK VIEW ====================
class MainMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # 1. Sorgu Menüsü
        self.add_item(SorguSecim())
        # 2. Data Çekme Butonu
        self.add_item(discord.ui.Button(
            label="Discord Data Çek", 
            style=discord.ButtonStyle.green, 
            emoji="📁", 
            custom_id="data_cek_btn"
        ))

    # Buton için özel bir dinleyici yazıyoruz
    @discord.ui.button(label="_", style=discord.ButtonStyle.secondary, row=2)
    async def dummy(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass # Bu butonu gizleyeceğiz, sadece aşağıda dinleyeceğiz

# Aslında tek bir view kullanmak yerine, Data butonunu manuel eklemek yerine view içinde tanımlayalım
class CombinedView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SorguSecim())
        
        # Data Çek Butonu
        btn = discord.ui.Button(label="Discord Data Çek", style=discord.ButtonStyle.green, emoji="📁")
        btn.callback = self.data_cek_callback
        self.add_item(btn)

    async def data_cek_callback(self, interaction: discord.Interaction):
        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        urls = [url for url in [DATA_URL_1, DATA_URL_2, DATA_URL_3] if url]

        if not urls:
            await interaction.followup.send("❌ Hiçbir veri linki (`DATA_URL_1`, `2`, `3`) ayarlanmamış.", ephemeral=True)
            return

        await interaction.followup.send(f"⏳ {len(urls)} adet dosya indiriliyor, lütfen bekleyin...", ephemeral=True)

        all_lines = []
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(urls, 1):
                try:
                    async with session.get(url, timeout=120) as resp:
                        resp.raise_for_status()
                        content = await resp.text()
                        lines = [satir.strip() for satir in content.splitlines() if satir.strip()]
                        all_lines.extend(lines)
                except Exception as e:
                    await interaction.followup.send(f"⚠️ {i}. link indirilemedi: `{e}`", ephemeral=True)

        if not all_lines:
            await interaction.followup.send("❌ Veri bulunamadı.", ephemeral=True)
            return

        await interaction.followup.send(f"🚀 Toplam {len(all_lines)} veri bulundu. Kanala yazılıyor...", ephemeral=True)

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
            except Exception:
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
        title="🕵️‍♂️ Yenilgi Sorgu Paneli",
        description="Aşağıdaki menüden sorgu yapabilir veya **Discord Data Çek** butonuyla dosyaları kanala çekebilirsiniz.",
        color=0x5865F2
    )
    embed.set_image(url=IMAGE_URL)
    embed.set_footer(text=FOOTER_TEXT)

    await ctx.send(embed=embed, view=CombinedView())

# ==================== ÇALIŞTIR ====================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ HATA: TOKEN bulunamadı! Render'da TOKEN değişkenini kontrol et.")
    else:
        keep_alive()
        bot.run(TOKEN)
