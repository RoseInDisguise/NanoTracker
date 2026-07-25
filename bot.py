import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

# --- 1. LOAD SECRETS SAFELY ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
NANOGPT_API_KEY = os.getenv('NANOGPT_API_KEY')

# --- 2. THE RENDER "KEEP-AWAKE" WEB SERVER ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"NanoGPT Token Tracker is alive and running!")
    
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

def run_dummy_server():
    # Render automatically passes a dynamic port via the PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

# Start the web server in an independent background thread
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- 3. INITIALIZE BOT ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print("="*30, flush=True)
    print(f'✅ SUCCESS! Logged in as {bot.user}', flush=True)
    
    # Reusing your smart Slash Command sync protection logic
    if not hasattr(bot, 'synced'):
        try:
            synced = await bot.tree.sync()
            print(f"🔄 Synced {len(synced)} secure slash commands to Discord.", flush=True)
            bot.synced = True 
        except Exception as e:
            print(f"🚨 Failed to sync slash commands: {e}", flush=True)
    else:
        print("⚡ Reconnected to Discord! (Commands already synced)", flush=True)
        
    print("="*30, flush=True)

# --- 4. THE NANO_GPT SLASH COMMAND ---
@bot.tree.command(name="tokens", description="Check remaining NanoGPT weekly token usage.")
async def tokens(interaction: discord.Interaction):
    url = "https://nano-gpt.com/api/subscription/v1/usage"
    headers = {
        "Authorization": f"Bearer {NANOGPT_API_KEY}"
    }
    
    await interaction.response.defer(ephemeral=False)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 401:
                    await interaction.followup.send("❌ Error: Invalid API Key configured in the bot settings.")
                    return
                if response.status == 404:
                    await interaction.followup.send("❌ Error: NanoGPT API endpoint not found.")
                    return
                response.raise_for_status() 
                data = await response.json()
        
        if not data.get('active', False):
            await interaction.followup.send("⚠️ The NanoGPT subscription does not appear to be active.")
            return
            
        # --- DIAGNOSTIC PROBE ---
        # We bypass our assumptions and print the raw JSON data to inspect the structure.
        import json
        formatted_json = json.dumps(data, indent=2)
        
        # Discord has a 2000 character limit per message, so we slice it just in case.
        await interaction.followup.send(f"**Diagnostic Data:**\n```json\n{formatted_json[:1900]}\n```")
        return
        # -------------------------

    except aiohttp.ClientError:
        await interaction.followup.send("Oops, couldn't connect to NanoGPT. The network might be down.")
    except Exception as e:
        await interaction.followup.send(f"An unexpected internal error occurred: ```{e}```")

# --- 5. EXECUTION GUARD ---
if __name__ == "__main__":
    if DISCORD_TOKEN is None or NANOGPT_API_KEY is None:
        print("🚨 ERROR: Missing .env variables!", flush=True)
    else:
        bot.run(DISCORD_TOKEN)