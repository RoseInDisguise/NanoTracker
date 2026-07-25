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

# --- 2. THE ROLEPLAY MODEL LIBRARY (THE NESTED DICTIONARY) ---
# Format: "Model_Name - Score/10 - [Review Placeholder]"
RP_MODELS = {
    "🔥 Smut & NSFW": {
        "recommended": [
            "Gemma 4 31B DarkIdol - 9/10 - [Review Placeholder]",
            "Qwen3.5 27B Derestricted - 8/10 - [Review Placeholder]",
            "xiaomi/mimo-v2.5-pro - 8/10 - [Review Placeholder]"
        ],
        "avoid": [
            "moonshotai/kimi-k2.6 - [Strictly censored corporate model, will refuse prompts]",
            "zai-org/glm-5 - [High refusal rate on explicit content]",
            "deepseek-ai/DeepSeek-V3.1 - [Corporate alignment restricts NSFW output]"
        ]
    },
    "🎭 Prose & Storytelling": {
        "recommended": [
            "deepseek/deepseek-v4-pro-cheaper:thinking - 9/10 - [Review Placeholder]",
            "Gemma 4 31B Novelist - 9/10 - [Review Placeholder]",
            "minimax/minimax-m3 - 8/10 - [Review Placeholder]",
            "Qwen 3 235b A22B - 8/10 - [Review Placeholder]",
            "zai-org/glm-4.7 - 7/10 - [Review Placeholder]"
        ],
        "avoid": [
            "moonshotai/kimi-k2.7-code - [Designed for coding, x2 token cost, terrible at prose]"
        ]
    },
    "🌧️ Angst & Drama": {
        "recommended": [
            "nvidia/nemotron-3-ultra-550b-a55b - 10/10 - [Review Placeholder]",
            "Gemma 4 31B Melinoe - 9/10 - [Review Placeholder]",
            "deepseek-ai/DeepSeek-V3.1-Terminus - 8/10 - [Review Placeholder]",
            "xiaomi/mimo-v2.5:thinking - 7/10 - [Review Placeholder]"
        ],
        "avoid": [
            "inclusionai/ling-3.0-flash - [Too concise for emotional depth]"
        ]
    },
    "✨ Creativity & Wildcard": {
        "recommended": [
            "longcat-2.0 - 9/10 - [Review Placeholder]",
            "deepseek-ai/DeepSeek-R1-0528 - 8/10 - [Review Placeholder]",
            "inclusionai/ling-3.0-flash:thinking - 8/10 - [Review Placeholder]",
            "minimax/minimax-m2.7 - 7/10 - [Review Placeholder]"
        ],
        "avoid": [
            "deepseek-v3-0324 - [Outdated iteration compared to newer v4 models]"
        ]
    }
}

# --- 3. THE RENDER "KEEP-AWAKE" WEB SERVER ---
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
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- 4. INTERACTIVE UI COMPONENTS FOR MODELS ---
class ModelSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🔥 Smut & NSFW", description="Uncensored, descriptive, and passionate."),
            discord.SelectOption(label="🎭 Prose & Storytelling", description="Rich narratives, worldbuilding, and flow."),
            discord.SelectOption(label="🌧️ Angst & Drama", description="Heavy emotional tension and psychological depth."),
            discord.SelectOption(label="✨ Creativity & Wildcard", description="Unique writing styles and high context options.")
        ]
        super().__init__(placeholder="Select a roleplay style...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # 1. Retrieve the nested dictionary for the chosen category
        selected_category = self.values[0]
        category_data = RP_MODELS[selected_category]
        
        # 2. Process the Recommended List
        rec_lines = []
        for item in category_data["recommended"]:
            # We split by ' - ' only on the first instance to separate Name from Score/Review
            parts = item.split(" - ", 1)
            name = parts[0]
            details = parts[1] if len(parts) > 1 else "No data."
            rec_lines.append(f"• **{name}**\n  *{details}*")
        rec_text = "\n\n".join(rec_lines)
        
        # 3. Process the Avoid List
        avoid_lines = []
        for item in category_data["avoid"]:
            parts = item.split(" - ", 1)
            name = parts[0]
            details = parts[1] if len(parts) > 1 else "Not recommended."
            avoid_lines.append(f"❌ **{name}**\n  *{details}*")
        avoid_text = "\n\n".join(avoid_lines) if avoid_lines else "*No models are currently flagged for this category.*"
        
        # 4. Construct the UI Embed
        embed = discord.Embed(
            title=f"{selected_category} Recommendations",
            description=f"**✅ Top Picks:**\n\n{rec_text}\n\n**⚠️ Stay Away From:**\n\n{avoid_text}",
            color=discord.Color.purple()
        )
        embed.set_footer(text="Tip: Copy the exact bolded name into your chat client UI.")
        
        await interaction.response.edit_message(embed=embed)

class ModelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 
        self.add_item(ModelSelect())

# --- 5. INITIALIZE BOT ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print("="*30, flush=True)
    print(f'✅ SUCCESS! Logged in as {bot.user}', flush=True)
    
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

# --- 6. THE /tokens SLASH COMMAND ---
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
            
        usage_data = data.get('weeklyInputTokens', {})
        
        if not usage_data:
            await interaction.followup.send("❌ Internal Error: Could not locate 'weeklyInputTokens' in the API data.")
            return

        used = usage_data.get('used', 0)
        remaining = usage_data.get('remaining', 0)
        limit = used + remaining
        
        percent_remaining = (remaining / limit) * 100 if limit > 0 else 0
        if percent_remaining > 20:
            embed_color = discord.Color.blue()
        elif percent_remaining > 5:
            embed_color = discord.Color.yellow()
        else:
            embed_color = discord.Color.red()

        reset_ms = usage_data.get('resetAt')
        if reset_ms:
            unix_seconds = int(reset_ms / 1000)
            reset_time = f"<t:{unix_seconds}:F> \n*<t:{unix_seconds}:R>*"
        else:
            reset_time = "Unknown"

        embed = discord.Embed(
            title="📊 NanoGPT Subscription Status",
            color=embed_color
        )
        embed.add_field(name="Tokens Used", value=f"{used:,} / {limit:,}", inline=True)
        embed.add_field(name="Tokens Remaining", value=f"{remaining:,}", inline=True)
        embed.add_field(name="\u200B", value="\u200B", inline=False) 
        embed.add_field(name="Next Reset", value=reset_time, inline=False)
        
        await interaction.followup.send(embed=embed)

    except aiohttp.ClientError:
        await interaction.followup.send("Oops, couldn't connect to NanoGPT. The network might be down.")
    except Exception as e:
        await interaction.followup.send("An unexpected internal error occurred while parsing the data.")
        print(f"Internal Error Triggered: {e}")

# --- 7. THE /models SLASH COMMAND ---
@bot.tree.command(name="models", description="Browse the curated list of roleplay models.")
async def models_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 The Roleplay Companion",
        description="Select a writing style from the dropdown menu below to see our group's highly recommended models.",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=ModelView(), ephemeral=False)

# --- 8. EXECUTION GUARD ---
if __name__ == "__main__":
    if DISCORD_TOKEN is None or NANOGPT_API_KEY is None:
        print("🚨 ERROR: Missing .env variables!", flush=True)
    else:
        bot.run(DISCORD_TOKEN)