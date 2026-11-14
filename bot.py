import discord
from discord.ext import commands
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- FIX PRO RENDER (Drží HTTP port 10000 otevřený pro 24/7 běh) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Meeting Bot is online 24/7!")
    def log_message(self, format, *args):
        pass

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()
# -------------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

class MeetingModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Naplánovat meeting")
        
        self.title_input = discord.ui.TextInput(
            label="Nadpis meetingu",
            style=discord.TextStyle.short,
            placeholder="Např. Důležitá porada vedení...",
            required=True,
            max_length=100
        )
        
        self.ping_input = discord.ui.TextInput(
            label="Koho pingnout (role nebo uživatelé)",
            style=discord.TextStyle.short,
            placeholder="Např. @Vedení nebo @everyone...",
            required=True,
            max_length=100
        )

        self.time_input = discord.ui.TextInput(
            label="Kdy se meeting koná",
            style=discord.TextStyle.short,
            placeholder="Např. Zítra ve 20:00...",
            required=True,
            max_length=100
        )

        self.location_input = discord.ui.TextInput(
            label="Kde (místnost / kanál)",
            style=discord.TextStyle.short,
            placeholder="Např. Hlavní hlasovna / Kancelář...",
            required=True,
            max_length=100
        )

        self.content_input = discord.ui.TextInput(
            label="O čem se bude jednat",
            style=discord.TextStyle.paragraph,
            placeholder="Stručný přehled bodů k jednání...",
            required=True,
            max_length=1000
        )

        self.add_item(self.title_input)
        self.add_item(self.ping_input)
        self.add_item(self.time_input)
        self.add_item(self.location_input)
        self.add_item(self.content_input)

    async def on_submit(self, interaction: discord.Interaction):
        meeting_title = self.title_input.value.strip()
        ping_target = self.ping_input.value.strip()
        meeting_time = self.time_input.value.strip()
        meeting_location = self.location_input.value.strip()
        content = self.content_input.value.strip()
        user_name = interaction.user.display_name

        embed = discord.Embed(
            title=f"📅 MEETING: {meeting_title}",
            description=content,
            color=discord.Color.from_rgb(231, 76, 60)
        )
        embed.add_field(name="👥 Kdo se dostaví", value=ping_target, inline=False)
        embed.add_field(name="⏰ Kdy", value=meeting_time, inline=True)
        embed.add_field(name="📍 Kde", value=meeting_location, inline=True)
        embed.set_footer(text=f"Organizátor: {user_name}")
        embed.timestamp = discord.utils.utcnow()

        await interaction.channel.send(
            content=f"🔔 **Upozornění na meeting:** {ping_target}",
            embed=embed,
            view=MeetingResponseView()
        )
        
        await interaction.response.send_message("✅ Pozvánka na meeting byla úspěšně vytvořena a odeslána!", ephemeral=True)

class MeetingResponseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.attending_users = set()

    @discord.ui.button(label="Zúčastním se (0)", style=discord.ButtonStyle.success, emoji="✅", custom_id="meeting_attend_btn")
    async def attend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        if user_id in self.attending_users:
            self.attending_users.remove(user_id)
            await interaction.response.send_message("❌ Vaše účast na meetingu byla zrušena.", ephemeral=True)
        else:
            self.attending_users.add(user_id)
            await interaction.response.send_message("✅ Účast na meetingu byla potvrzena!", ephemeral=True)
        
        button.label = f"Zúčastním se ({len(self.attending_users)})"
        await interaction.message.edit(view=self)

class MeetingPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Naplánovat meeting", style=discord.ButtonStyle.primary, emoji="📅", custom_id="panel_meeting_btn")
    async def create_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MeetingModal())

@bot.event
async def on_ready():
    bot.add_view(MeetingPanelView())
    bot.add_view(MeetingResponseView())
    print(f"Meeting Bot je online jako {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def meeting(ctx):
    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass

    embed = discord.Embed(
        title="📅 PLÁNOVÁNÍ MEETINGŮ",
        description="Kliknutím na tlačítko níže můžeš vytvořit oficiální pozvánku na meeting.",
        color=discord.Color.dark_theme()
    )
    embed.set_footer(text="Systém pro správu meetingů")
    
    await ctx.send(embed=embed, view=MeetingPanelView())

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
