import json
import os
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import token

# File penyimpanan data
AGENDA_FILE = 'agenda.json'

# Fungsi untuk memuat data agenda
def load_agenda():
    if os.path.exists(AGENDA_FILE):
        with open(AGENDA_FILE, 'r') as f:
            return json.load(f)
    return {}

# Fungsi untuk menyimpan data agenda
def save_agenda(agenda):
    with open(AGENDA_FILE, 'w') as f:
        json.dump(agenda, f, indent=4)

# Inisialisasi bot
intents = discord.Intents.default()
intents.message_content = True  # Diperlukan untuk membaca pesan
bot = commands.Bot(command_prefix='/', intents=intents)

# Scheduler untuk pengingat
scheduler = AsyncIOScheduler()

@bot.command()
async def about(ctx):
    await ctx.send('Ini adalah bot untuk pengingat jadwal!')

# Perintah /add: Menambah kegiatan (format: /add YYYY-MM-DD HH:MM Deskripsi)
@bot.command()
async def add(ctx, date_str: str, time_str: str, *, desc: str):
    try:
        event_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        agenda = load_agenda()
        date_key = date_str
        if date_key not in agenda:
            agenda[date_key] = []
        agenda[date_key].append({"time": time_str, "desc": desc, "reminder": True, "channel_id": ctx.channel.id})
        save_agenda(agenda)
        
        await ctx.send(f"Kegiatan ditambahkan: {desc} pada {date_str} {time_str}")
    except ValueError:
        await ctx.send("Format tanggal/waktu salah. Gunakan YYYY-MM-DD HH:MM")

# Perintah /agenda: Menampilkan agenda harian (format: /agenda YYYY-MM-DD)
@bot.command()
async def agenda(ctx, date_str: str = None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    agenda = load_agenda()
    if date_str in agenda:
        events = agenda[date_str]
        response = f"Agenda untuk {date_str}:\n" + "\n".join([f"- {e['time']}: {e['desc']}" for e in events])
    else:
        response = f"Tidak ada kegiatan untuk {date_str}"
    await ctx.send(response)

# Fungsi pengingat otomatis (dicek setiap menit)
async def send_reminders():
    now = datetime.now()
    agenda = load_agenda()
    for date, events in agenda.items():
        for event in events:
            if event.get("reminder"):
                event_time = datetime.strptime(f"{date} {event['time']}", "%Y-%m-%d %H:%M")
                if now <= event_time <= now + timedelta(minutes=15):  # Pengingat 15 menit sebelum
                    channel = bot.get_channel(event['channel_id'])
                    if channel:
                        await channel.send(f"Pengingat: {event['desc']} pada {event['time']}")

# Event saat bot siap
@bot.event
async def on_ready():
    print(f'Bot {bot.user} siap!')
    scheduler.add_job(send_reminders, 'interval', minutes=1)
    scheduler.start()

# Jalankan bot
bot.run(token)