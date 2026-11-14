import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord.ext import commands

# --- HTTP SERVER PRO RENDER & UPTIMEROBOT ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Meeting Bot is online 24/7!")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args):
        pass

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()
# ---------------------------------------------

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class MeetingModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Naplánovat meeting")
        self.title_input = discord.ui.TextInput(label="Nadpis meetingu", placeholder="Důležitá porada...", required=True, max_length=100)
        self.ping_input = discord.ui.TextInput(label="Koho pingnout", placeholder="@Vedení / @everyone...", required=True, max_length=100)
        self.time_input = discord.ui.TextInput(label="Kdy se meeting koná", placeholder="Zítra ve 20:00...", required=True, max_length=100)
        self.location_input = discord.ui.TextInput(label="Kde (místnost)", placeholder="Hlavní hlasovna...", required=True, max_length=100)
        self.content_input = discord.ui.TextInput(label="O čem se bude jednat", style=discord.TextStyle.paragraph, placeholder="Body k jednání...", required=True, max_length=1000)
        
        self.add_item(self.title_input)
        self.add_item(self.ping_input)
        self.add_item(self.time_input)
        self.add_item(self.location_input)
        self.add_item(self.content_input)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"📅 MEETING: {self.title_input.value.strip()}", description=self.content_input.value.strip(), color=discord.Color.from_rgb(231, 76, 60))
        embed.add_field(name="👥 Kdo se dostaví", value=self.ping_input.value.strip(), inline=False)
        embed.add_field(name="⏰ Kdy", value=self.time_input.value.strip(), inline=True)
        embed.add_field(name="📍 Kde", value=self.location_input.value.strip(), inline=True)
        embed.set_footer(text=f"Organizátor: {interaction.user.display_name}")
        embed.timestamp = discord.utils.utcnow()

        await interaction.channel.send(content=f"🔔 **Upozornění na meeting:** {self.ping_input.value.strip()}", embed=embed, view=MeetingResponseView())
        await interaction.response.send_message("✅ Pozvánka byla úspěšně vytvořena!", ephemeral=True)

class MeetingResponseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.attending_users = set()

    @discord.ui.button(label="Zúčastním se (0)", style=discord.ButtonStyle.success, emoji="✅", custom_id="meeting_attend_btn")
    async def attend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.attending_users:
            self.attending_users.remove(interaction.user.id)
            await interaction.response.send_message("❌ Účast zrušena.", ephemeral=True)
        else:
            self.attending_users.add(interaction.user.id)
            await interaction.response.send_message("✅ Účast potvrzena!", ephemeral=True)
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
    except:
        pass
    embed = discord.Embed(title="📅 PLÁNOVÁNÍ MEETINGŮ", description="Kliknutím níže vytvoříš pozvánku na meeting.", color=discord.Color.dark_theme())
    await ctx.send(embed=embed, view=MeetingPanelView())

bot.run(os.getenv("DISCORD_TOKEN"))
