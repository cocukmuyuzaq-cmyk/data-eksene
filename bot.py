import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
import json
import io
import time
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

# ==================== COOLDOWN ====================
DATACEK_COOLDOWN = 300   # 5 dakika
DIGER_COOLDOWN = 30      # 30 saniye

cooldowns = {}

def kalan_sure(user_id: int, tur: str) -> float:
    kayit = cooldowns.get(user_id)
    if not kayit:
        return 0
    son = kayit.get(tur, 0)
    gecen = time.time() - son
    limit = DATACEK_COOLDOWN if tur == "datacek" else DIGER_COOLDOWN
    kalan = limit - gecen
    return kalan if kalan > 0 else 0

def cooldown_baslat(user_id: int, tur: str):
    cooldowns.setdefault(user_id, {})[tur] = time.time()

def sure_format(sn: float) -> str:
    sn = int(sn) + 1
    dk, sn = divmod(sn, 60)
    if dk > 0:
        return f"{dk} dk {sn} sn"
    return f"{sn} sn"

# ==================== DATA OFFSET / HAFIZA ====================
# url -> son kalınan index
data_offsets = {}
# user_id -> set(gönderilen satırlar)   (tekrar göndermeyi engellemek için)
gonderilenler = {}

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
        self.sorgu = discord.ui.TextInput(label="Sorgu Değeri", placeholder=placeholder, required=True, max_length=100)
        self.add_item(self.sorgu)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        target_url = f"{self.api_url}{self.sorgu.value}"

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
                dosya = discord.File(io.BytesIO(sonuc_str.encode('utf-8')), filename="log.txt")
                embed = discord.Embed(title=f"✅ {self.title}", description="Dosya olarak gönderildi.", color=0x00E676)
                embed.set_image(url=IMAGE_URL)
                embed.set_footer(text=FOOTER_TEXT)
                await interaction.user.send(embed=embed, file=dosya)
                await interaction.followup.send("✅ DM'ye gönderildi!", ephemeral=True)
                return

            embed = discord.Embed(title=f"✅ {self.title}", description=f"```json\n{sonuc_str}\n```", color=0x00E676)
            embed.set_image(url=IMAGE_URL)
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.user.send(embed=embed)
            await interaction.followup.send("✅ DM'ye gönderildi!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {str(e)}", ephemeral=True)

class BosSorguModal(discord.ui.Modal):
    def __init__(self, title, api_url):
        super().__init__(title=title)
        self.api_url = api_url

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            return
        await interaction.response.defer(ephemeral=True)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, timeout=20) as resp:
                    if resp.status != 200:
                        return
                    try:
                        data = await resp.json()
                    except:
                        data = await resp.text()

            temiz_data = temizle(data)
            sonuc_str = json.dumps(temiz_data, indent=2, ensure_ascii=False) if isinstance(temiz_data, dict) else str(temiz_data)
            embed = discord.Embed(title=f"✅ {self.title}", description=f"```json\n{sonuc_str}\n```", color=0x00E676)
            embed.set_image(url=IMAGE_URL)
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.user.send(embed=embed)
            await interaction.followup.send("✅ DM'ye gönderildi!", ephemeral=True)
        except:
            pass

# ==================== DATA ÇEKME MODALI ====================
class DataCekModal(discord.ui.Modal):
    def __init__(self, channel: discord.TextChannel):
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
        if interaction.guild is None or interaction.guild.id not in ALLOWED_GUILD_IDS:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        if kalan_sure(interaction.user.id, "datacek") > 0:
            await interaction.response.send_message(
                f"⏳ Cooldown aktif. Kalan süre: **{sure_format(kalan_sure(interaction.user.id, 'datacek'))}**",
                ephemeral=True
            )
            return

        try:
            adet = int(self.adet.value.strip())
        except ValueError:
            await interaction.response.send_message("❌ Lütfen geçerli bir sayı gir (1-100).", ephemeral=True)
            return

        if adet < 1 or adet > 100:
            await interaction.response.send_message("❌ Sayı 1 ile 100 arasında olmalı.", ephemeral=True)
            return

        urls = [url for url in [DATA_URL_1, DATA_URL_2, DATA_URL_3] if url]
        if not urls:
            await interaction.response.send_message("❌ Linkler ayarlanmamış.", ephemeral=True)
            return

        cooldown_baslat(interaction.user.id, "datacek")
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        gonderilenler.setdefault(user_id, set())

        # Tüm URL'lerden satırları topla (hepsini indirir)
        tum_satirlar = []
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(urls, 1):
                try:
                    async with session.get(url, timeout=120) as resp:
                        resp.raise_for_status()
                        text = await resp.text()
                        lines = [l.strip() for l in text.splitlines() if l.strip()]
                        tum_satirlar.extend([(url, l) for l in lines])
                except Exception as e:
                    print(f"Link {i} hatası: {e}")

        if not tum_satirlar:
            await interaction.followup.send("⚠️ Hiç data bulunamadı.", ephemeral=True)
            return

        # Havuzdan kaldığı yerden devam et, tekrar edeni atla
        secilen = []
        denenen = 0
        max_deneme = len(tum_satirlar) * 2

        # Her URL için offset kullan
        # Basitleştirme: tüm havuzu sırayla tara, offset'leri URL bazlı tut
        url_index = {url: 0 for url in urls}
        # başlangıç offset'lerini yükle
        for url in urls:
            url_index[url] = data_offsets.get(url, 0)

        while len(secilen) < adet and denenen < max_deneme:
            denenen += 1
            ilerleme = False
            for url in urls:
                if len(secilen) >= adet:
                    break
                url_lines = [l for (u, l) in tum_satirlar if u == url]
                if not url_lines:
                    continue
                idx = url_index[url] % len(url_lines)
                satir = url_lines[idx]
                url_index[url] = idx + 1
                ilerleme = True

                if satir in gonderilenler[user_id]:
                    continue

                secilen.append((url, satir))
                gonderilenler[user_id].add(satir)

            if not ilerleme:
                break

        # Offset'leri kaydet
        for url in urls:
            url_lines = [l for (u, l) in tum_satirlar if u == url]
            if url_lines:
                data_offsets[url] = url_index[url] % len(url_lines)

        if not secilen:
            await interaction.followup.send(
                "⚠️ Havuzdaki tüm datalar zaten gönderildi. Yeni data eklenince tekrar denenebilir.",
                ephemeral=True
            )
            return

        toplam_gonderilen = 0
        for url, line in secilen:
            embed = discord.Embed(title="📁 Yenilgi Data", description=f"```yaml\n{line}\n```", color=0x5865F2)
            embed.set_image(url=IMAGE_URL)
            embed.set_footer(text=FOOTER_TEXT)
            try:
                await self.channel.send(embed=embed)
                toplam_gonderilen += 1
                await asyncio.sleep(0.6)
            except Exception:
                await asyncio.sleep(1.5)

        await interaction.followup.send(
            f"✅ İşlem tamamlandı. Toplam **{toplam_gonderilen}** data gönderildi.\n"
            f"⏳ Bir sonraki data çekimi için **{sure_format(DATACEK_COOLDOWN)}** beklemelisin.",
            ephemeral=True
        )

# ==================== MENÜ ====================
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
        user_id = interaction.user.id

        if secim == "datacek":
            tur = "datacek"
            kalan = kalan_sure(user_id, "datacek")
            if kalan > 0:
                await interaction.response.send_message(
                    f"⏳ Data çekme cooldown'u aktif. Kalan süre: **{sure_format(kalan)}**", ephemeral=True
                )
                return
        else:
            tur = "diger"
            kalan = kalan_sure(user_id, "diger")
            if kalan > 0:
                await interaction.response.send_message(
                    f"⏳ Cooldown aktif. Kalan süre: **{sure_format(kalan)}**", ephemeral=True
                )
                return

        cooldown_baslat(user_id, tur)

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
