import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
import json
import io
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
    t = Thread(target=run_web_server, daemon=True)
    t.start()

# ==================== BOT AYARLARI ====================
TOKEN = os.getenv("TOKEN")
ALLOWED_GUILD_IDS = [1564299296097050855, 1563560298596536453]

API_BASE_1 = "https://wazely.vercel.app/api"
API_BASE_2 = "https://wazelyapi.vercel.app/api"
ID_API = "https://prox0959.netlify.app/api/search?id="

DATA_URL_1 = os.getenv("DATA_URL_1")
DATA_URL_2 = os.getenv("DATA_URL_2")
DATA_URL_3 = os.getenv("DATA_URL_3")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

IMAGE_URL = "https://cdn.discordapp.com/attachments/1566040841150140477/1568589689072517201/image0.jpg?ex=6af05e7c&is=6aef0cfc&hm=2ba98ebe9a1b762f154d732a13a478165a8d0fae0929392899608834df3d033c&"
FOOTER_TEXT = "discord.gg/yenilgi"

# ==================== HAFIZA ====================
data_offsets = {}
gonderilenler = {}

# ==================== FİLTRE ====================
def temizle(data):
    if isinstance(data, dict):
        return {k: temizle(v) for k, v in data.items() if k.lower() not in ['dev', 'author', 'provider', 'credit']}
    elif isinstance(data, list):
        return [temizle(i) for i in data]
    return data

# ==================== GÜVENLİ GÖNDERİM ====================
async def guvenli_gonder(channel, embed, max_deneme=3):
    for _ in range(max_deneme):
        try:
            await channel.send(embed=embed)
            return True
        except discord.HTTPException as e:
            if e.status == 429:
                bekle = getattr(e, "retry_after", 2)
                await asyncio.sleep(bekle + 0.5)
            else:
                await asyncio.sleep(1.5)
        except Exception:
            await asyncio.sleep(1.5)
    return False

# ==================== SORGU MODALLARI ====================
class SorguModal(discord.ui.Modal):
    def __init__(self, title, placeholder, api_url):
        super().__init__(title=title)
        self.api_url = api_url
        self.sorgu = discord.ui.TextInput(label="Sorgu Değeri", placeholder=placeholder, required=True, max_length=100)
        self.add_item(self.sorgu)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            await interaction.followup.send("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        target_url = f"{self.api_url}{self.sorgu.value}"

        try:
            timeout = aiohttp.ClientTimeout(total=25)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(target_url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send(f"❌ Sorgu Hatası: HTTP {resp.status}", ephemeral=True)
                        return
                    try:
                        data = await resp.json()
                    except Exception:
                        data = await resp.text()

            if not data:
                await interaction.followup.send("⚠️ Sonuç bulunamadı.", ephemeral=True)
                return

            temiz_data = temizle(data)
            sonuc_str = json.dumps(temiz_data, indent=2, ensure_ascii=False) if isinstance(temiz_data, dict) else str(temiz_data)

            if len(sonuc_str) > 1900:
                dosya = discord.File(io.BytesIO(sonuc_str.encode('utf-8')), filename="log.txt")
                embed = discord.Embed(title=f"✅ {self.title}", description="Dosya olarak gönderildi.", color=0x00E676)
                embed.set_image(url=IMAGE_URL)
                embed.set_footer(text=FOOTER_TEXT)
                try:
                    await interaction.user.send(embed=embed, file=dosya)
                    await interaction.followup.send("✅ DM'ye gönderildi!", ephemeral=True)
                except discord.Forbidden:
                    await interaction.followup.send("❌ DM kapalı, açıp tekrar dene.", ephemeral=True)
                return

            embed = discord.Embed(title=f"✅ {self.title}", description=f"```json\n{sonuc_str}\n```", color=0x00E676)
            embed.set_image(url=IMAGE_URL)
            embed.set_footer(text=FOOTER_TEXT)
            try:
                await interaction.user.send(embed=embed)
                await interaction.followup.send("✅ DM'ye gönderildi!", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("❌ DM kapalı, açıp tekrar dene.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ API zaman aşımına uğradı.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {str(e)[:200]}", ephemeral=True)

class BosSorguModal(discord.ui.Modal):
    def __init__(self, title, api_url):
        super().__init__(title=title)
        self.api_url = api_url

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            return
        try:
            timeout = aiohttp.ClientTimeout(total=25)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.api_url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send(f"❌ HTTP {resp.status}", ephemeral=True)
                        return
                    try:
                        data = await resp.json()
                    except Exception:
                        data = await resp.text()

            temiz_data = temizle(data)
            sonuc_str = json.dumps(temiz_data, indent=2, ensure_ascii=False) if isinstance(temiz_data, dict) else str(temiz_data)
            embed = discord.Embed(title=f"✅ {self.title}", description=f"```json\n{sonuc_str}\n```", color=0x00E676)
            embed.set_image(url=IMAGE_URL)
            embed.set_footer(text=FOOTER_TEXT)
            try:
                await interaction.user.send(embed=embed)
                await interaction.followup.send("✅ DM'ye gönderildi!", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("❌ DM kapalı.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Zaman aşımı.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {str(e)[:200]}", ephemeral=True)

# ==================== DATA ÇEKME MODALI ====================
class DataCekModal(discord.ui.Modal):
    def __init__(self, channel):
        super().__init__(title="Data Çekme")
        self.channel = channel
        self.adet = discord.ui.TextInput(
            label="Kaç data çekilsin? (1-100)",
            placeholder="Örnek: 25",
            required=True,
            max_length=3
        )
        self.add_item(self.adet)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            await interaction.followup.send("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        try:
            adet = int(self.adet.value.strip())
        except ValueError:
            await interaction.followup.send("❌ Geçerli bir sayı gir (1-100).", ephemeral=True)
            return

        if adet < 1 or adet > 100:
            await interaction.followup.send("❌ Sayı 1 ile 100 arasında olmalı.", ephemeral=True)
            return

        urls = [url for url in [DATA_URL_1, DATA_URL_2, DATA_URL_3] if url]
        if not urls:
            await interaction.followup.send("❌ Linkler ayarlanmamış.", ephemeral=True)
            return

        await interaction.followup.send(
            f"✅ İşlem başlatıldı. **{adet}** data çekiliyor, lütfen bekle...",
            ephemeral=True
        )

        asyncio.create_task(
            data_cek_gorevi(interaction.user, self.channel, urls, adet)
        )

# ==================== AĞIR GÖREV ====================
async def data_cek_gorevi(user, channel, urls, adet):
    user_id = user.id
    gonderilenler.setdefault(user_id, set())

    tum_satirlar = []
    timeout = aiohttp.ClientTimeout(total=120, connect=15)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i, url in enumerate(urls, 1):
            try:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    text = await resp.text()
                    lines = [l.strip() for l in text.splitlines() if l.strip()]
                    tum_satirlar.extend([(url, l) for l in lines])
            except asyncio.TimeoutError:
                print(f"[DataCek] Link {i} zaman aşımı: {url}")
            except Exception as e:
                print(f"[DataCek] Link {i} hatası: {e}")

    if not tum_satirlar:
        try:
            await channel.send("⚠️ Hiç data bulunamadı.")
        except Exception:
            pass
        return

    url_lines = {}
    for url, line in tum_satirlar:
        url_lines.setdefault(url, []).append(line)

    for url in urls:
        if url in url_lines:
            data_offsets.setdefault(url, 0)

    secilen = []
    denenen = 0
    max_deneme = len(tum_satirlar) * 2

    while len(secilen) < adet and denenen < max_deneme:
        ilerleme = False
        for url in urls:
            if len(secilen) >= adet:
                break
            if url not in url_lines:
                continue
            lines = url_lines[url]
            if not lines:
                continue
            idx = data_offsets[url] % len(lines)
            satir = lines[idx]
            data_offsets[url] = idx + 1
            denenen += 1
            ilerleme = True

            if satir in gonderilenler[user_id]:
                continue
            secilen.append((url, satir))
            gonderilenler[user_id].add(satir)

        if not ilerleme:
            break

    if not secilen:
        try:
            await channel.send("⚠️ Havuzdaki tüm datalar zaten gönderildi. Yeni data eklenince tekrar denenebilir.")
        except Exception:
            pass
        return

    toplam = 0
    for url, line in secilen:
        embed = discord.Embed(title="📁 Yenilgi Data", description=f"```yaml\n{line}\n```", color=0x5865F2)
        embed.set_image(url=IMAGE_URL)
        embed.set_footer(text=FOOTER_TEXT)
        if await guvenli_gonder(channel, embed):
            toplam += 1
        await asyncio.sleep(0.6)

    try:
        embed = discord.Embed(
            title="✅ Data Çekimi Tamamlandı",
            description=f"Toplam **{toplam}** data gönderildi.",
            color=0x00E676
        )
        embed.set_image(url=IMAGE_URL)
        embed.set_footer(text=FOOTER_TEXT)
        await user.send(embed=embed)
    except Exception:
        pass
    print(f"[DataCek] Kullanıcı {user_id} için {toplam} data gönderildi.")

# ==================== MENÜ SEÇENEKLERİ ====================
class SorguSecim(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Discord Data Çek", description="Dataları indirip kanala yazar", value="datacek", emoji="📁"),
            discord.SelectOption(label="ID Sorgu", description="Discord ID sorgular", value="idsorgu"),
            discord.SelectOption(label="Log Çekme", description="Site loglarını çeker", value="log"),
            discord.SelectOption(label="Eczane Sorgu", description="Eczane sorgular", value="eczane"),
            discord.SelectOption(label="IP Bilgi", description="IP bilgisi bulur", value="ipinfo"),
            discord.SelectOption(label="DNS Sorgu", description="DNS kayıtları", value="dns"),
            discord.SelectOption(label="Bahis Sorgu", description="Bahis kaydı arar", value="bahis"),
            discord.SelectOption(label="Plaka Sorgu", description="Araç bilgisi bulur", value="plaka"),
            discord.SelectOption(label="MC Bedrock", description="MC sunucu durumu", value="bedrock"),
            discord.SelectOption(label="Nitro Üret", description="Nitro kodları", value="nitro"),
            discord.SelectOption(label="Exxen Hesap", description="Exxen hesabı", value="exxen"),
            discord.SelectOption(label="Predunyam", description="Predunyam hesabı", value="predunyam"),
            discord.SelectOption(label="User Agent", description="Rastgele UA", value="ua"),
            discord.SelectOption(label="CC Gen", description="Kredi kartı üretir", value="ccgen"),
            discord.SelectOption(label="CC Check", description="Kart kontrol", value="cccheck"),
            discord.SelectOption(label="Discord Token Check", description="Token testi", value="dctoken"),
            discord.SelectOption(label="Telegram Token Check", description="Token testi", value="tgtoken"),
        ]
        super().__init__(placeholder="Bir işlem seçin...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            return

        secim = self.values[0]

        if secim == "datacek":
            await interaction.response.send_modal(DataCekModal(interaction.channel))
        elif secim == "idsorgu":
            await interaction.response.send_modal(SorguModal("ID Sorgu", "Discord ID", ID_API))
        elif secim == "log":
            await interaction.response.send_modal(SorguModal("Log Çekme", "Site adı", f"{API_BASE_1}/trlog?site="))
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

class GenelSorguView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SorguSecim())

# ==================== KOMUT ====================
@bot.event
async def on_ready():
    print(f"✅ Bot hazır: {bot.user}")
    await bot.change_presence(activity=discord.Game(name=f"!menü | {FOOTER_TEXT}"))

@bot.command(name="menü", aliases=["menu"])
async def menu(ctx):
    if ctx.guild is None or ctx.guild.id not in ALLOWED_GUILD_IDS:
        return

    embed = discord.Embed(
        title="🕵️‍♂️ Yenilgi Sorgu Paneli",
        description="Aşağıdaki menüden yapmak istediğiniz işlemi seçin.",
        color=0x5865F2
    )
    embed.set_image(url=IMAGE_URL)
    embed.set_footer(text=FOOTER_TEXT)

    await ctx.send(embed=embed, view=GenelSorguView())

# ==================== ÇALIŞTIR ====================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ HATA: TOKEN bulunamadı!")
    else:
        keep_alive()
        bot.run(TOKEN)
