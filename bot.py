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

# --- 2. THE MASTER MODEL DATABASE (SINGLE SOURCE OF TRUTH) ---
# Any score of 3 or lower has been converted to an AVOID string for dynamic sorting.
MODELS_DB = [
    {
        "name": "zai-org/glm-4.7",
        "🔥 Smut & NSFW": 6,
        "🌧️ Angst & Drama": 5,
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 6,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 5,
        "review": "A highly creative and stylistic model with solid capabilities across the board."
    },
    {
        "name": "zai-org/glm-4.7:thinking",
        "review": "Scores pending testing."
    },
    {
        "name": "zai-org/glm-5",
        "🔥 Smut & NSFW": "AVOID: High refusal rate expected (Score: 3/10).",
        "🌧️ Angst & Drama": "AVOID: Lacks emotional depth (Score: 3/10).",
        "🩸 Gore & Dark Themes": "AVOID: Censored against violence (Score: 2/10).",
        "✨ Creativity & Wildcard": 6,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 6,
        "😂 Comedy & Humor": "AVOID: Too corporate for humor (Score: 3/10).",
        "review": "Excellent logic and intelligence, but heavily restricted on darker or NSFW themes."
    },
    {
        "name": "moonshotai/kimi-k2.5",
        "🔥 Smut & NSFW": 5,
        "🌧️ Angst & Drama": 4,
        "🩸 Gore & Dark Themes": 4,
        "✨ Creativity & Wildcard": 7,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": 5,
        "review": "Good intelligence, decent prose."
    },
    {
        "name": "moonshotai/kimi-k2.6",
        "🔥 Smut & NSFW": 4,
        "🌧️ Angst & Drama": 5,
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 4,
        "review": "Highly intelligent and creative, noticeable prose upgrade from k2.5."
    },
    {
        "name": "moonshotai/kimi-k2.7-code",
        "🔥 Smut & NSFW": "AVOID: Designed for coding, terrible for NSFW (Score: 2/10).",
        "🌧️ Angst & Drama": "AVOID: Designed for coding, poor emotional depth (Score: 2/10).",
        "🩸 Gore & Dark Themes": "AVOID: Censored (Score: 2/10).",
        "✨ Creativity & Wildcard": 4,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 4,
        "😂 Comedy & Humor": "AVOID: Too analytical (Score: 2/10).",
        "review": "Use strictly for coding tasks. x2 Token cost makes it unviable for RP."
    },
    {
        "name": "deepseek/deepseek-v4-pro-cheaper",
        "🔥 Smut & NSFW": 6,
        "🌧️ Angst & Drama": 5,
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 6,
        "🧠 Intelligence & Logic": 6,
        "🎭 Prose & Storytelling": 6,
        "😂 Comedy & Humor": 5,
        "review": "Balanced and affordable."
    },
    {
        "name": "deepseek/deepseek-v4-flash",
        "🔥 Smut & NSFW": 8,
        "🌧️ Angst & Drama": 5,
        "🩸 Gore & Dark Themes": 6,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 7,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 5,
        "review": "Fast and excellent at prose and NSFW content."
    },
    {
        "name": "deepseek/deepseek-v3.2",
        "🔥 Smut & NSFW": 5,
        "🌧️ Angst & Drama": 6,
        "🩸 Gore & Dark Themes": 6,
        "✨ Creativity & Wildcard": 7,
        "🧠 Intelligence & Logic": 7,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": 6,
        "review": "Standard v3.2 model (No-CoT)."
    },
    {
        "name": "deepseek/deepseek-v3.2:thinking",
        "🔥 Smut & NSFW": 5,
        "🌧️ Angst & Drama": 6,
        "🩸 Gore & Dark Themes": 6,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 7,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 6,
        "review": "Chain-of-Thought (CoT) enabled. Noticeable boost to creativity and prose."
    },
    {
        "name": "deepseek-ai/DeepSeek-R1-0528",
        "🔥 Smut & NSFW": 7,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 6,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 5,
        "review": "Extremely intelligent and creative with great emotional depth."
    },
    {
        "name": "deepseek-v3-0324",
        "🔥 Smut & NSFW": 5,
        "🌧️ Angst & Drama": 6,
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 7,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": 5,
        "review": "Solid legacy model."
    },
    {
        "name": "nvidia/nemotron-3-ultra-550b-a55b",
        "🔥 Smut & NSFW": 7,
        "🌧️ Angst & Drama": 5,
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 6,
        "review": "A heavy-hitter with immense logic and excellent flow."
    },
    {
        "name": "minimax/minimax-m3",
        "🔥 Smut & NSFW": 4,
        "🌧️ Angst & Drama": 5,
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 6,
        "🧠 Intelligence & Logic": 6,
        "🎭 Prose & Storytelling": 6,
        "😂 Comedy & Humor": 4,
        "review": "Average performance across the board."
    },
    {
        "name": "minimax/minimax-m2.7",
        "🔥 Smut & NSFW": "AVOID: High refusal rate expected (Score: 3/10).",
        "🌧️ Angst & Drama": 5,
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 6,
        "🧠 Intelligence & Logic": 7,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": 4,
        "review": "Good logic, but strictly censored."
    },
    {
        "name": "minimax/minimax-m2.5",
        "🔥 Smut & NSFW": "AVOID: Extremely censored (Score: 1/10).",
        "🌧️ Angst & Drama": "AVOID: Poor performance (Score: 3/10).",
        "🩸 Gore & Dark Themes": "AVOID: Censored (Score: 3/10).",
        "✨ Creativity & Wildcard": 4,
        "🧠 Intelligence & Logic": 5,
        "🎭 Prose & Storytelling": "AVOID: Very weak prose (Score: 3/10).",
        "😂 Comedy & Humor": "AVOID: Lacks nuance (Score: 2/10).",
        "review": "Highly restricted and outdated. Avoid for RP scenarios."
    },
    {
        "name": "xiaomi/mimo-v2.5",
        "🔥 Smut & NSFW": 8,
        "🌧️ Angst & Drama": 6,
        "🩸 Gore & Dark Themes": 6,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 9,
        "😂 Comedy & Humor": 6,
        "review": "Incredible all-rounder. Uncensored and beautiful prose."
    },
    {
        "name": "xiaomi/mimo-v2.5-pro",
        "🔥 Smut & NSFW": 8,
        "🌧️ Angst & Drama": 6,
        "🩸 Gore & Dark Themes": 6,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 9,
        "😂 Comedy & Humor": 6,
        "review": "Pro version of Mimo. Consistently top-tier."
    },
    {
        "name": "longcat-2.0",
        "🔥 Smut & NSFW": "AVOID: Poor performance or highly restricted (Score: 3/10).",
        "🌧️ Angst & Drama": 4,
        "🩸 Gore & Dark Themes": "AVOID: Poor performance (Score: 3/10).",
        "✨ Creativity & Wildcard": 5,
        "🧠 Intelligence & Logic": 4,
        "🎭 Prose & Storytelling": 5,
        "😂 Comedy & Humor": "AVOID: Not recommended (Score: 3/10).",
        "review": "Low scores across the board, mainly useful for its massive context window."
    },
    {
        "name": "inclusionai/ling-3.0-flash",
        "🔥 Smut & NSFW": 9,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 9,
        "😂 Comedy & Humor": 5,
        "review": "An absolute powerhouse. Uncensored, creative, and highly intelligent."
    }
]

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

# --- 4. INTERACTIVE UI COMPONENTS (DYNAMIC FILTERING & PAGINATION) ---
class ModelSelect(discord.ui.Select):
    def __init__(self):
        # The dropdown now perfectly mirrors the new categories mapped in the database.
        options = [
            discord.SelectOption(label="🔥 Smut & NSFW", description="Uncensored, descriptive, and passionate."),
            discord.SelectOption(label="🎭 Prose & Storytelling", description="Rich narratives, worldbuilding, and flow."),
            discord.SelectOption(label="🌧️ Angst & Drama", description="Heavy emotional tension and psychological depth."),
            discord.SelectOption(label="🩸 Gore & Dark Themes", description="Uncensored violence and gritty scenarios."),
            discord.SelectOption(label="✨ Creativity & Wildcard", description="Unique writing styles and high context options."),
            discord.SelectOption(label="🧠 Intelligence & Logic", description="High reasoning, CoT, and complex plot tracking."),
            discord.SelectOption(label="😂 Comedy & Humor", description="Witty banter, situational comedy, and lighthearted RP.")
        ]
        super().__init__(placeholder="Select a roleplay style...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_category = self.values[0]
        self.view.current_page = 0
        await self.view.update_view(interaction)

class ModelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 
        self.current_page = 0
        self.selected_category = None
        self.items_per_page = 10
        
        self.add_item(ModelSelect())
        
        self.prev_btn = discord.ui.Button(label="◀️ Prev", style=discord.ButtonStyle.secondary, disabled=True)
        self.prev_btn.callback = self.prev_page
        self.add_item(self.prev_btn)
        
        self.next_btn = discord.ui.Button(label="Next ▶️", style=discord.ButtonStyle.primary, disabled=True)
        self.next_btn.callback = self.next_page
        self.add_item(self.next_btn)

    async def prev_page(self, interaction: discord.Interaction):
        self.current_page -= 1
        await self.update_view(interaction)

    async def next_page(self, interaction: discord.Interaction):
        self.current_page += 1
        await self.update_view(interaction)

    async def update_view(self, interaction: discord.Interaction):
        # Filter the Master Database dynamically
        recommended = []
        avoid = []
        
        for model in MODELS_DB:
            cat_value = model.get(self.selected_category)
            
            if isinstance(cat_value, (int, float)):
                recommended.append({
                    "name": model["name"],
                    "score": cat_value,
                    "review": model.get("review", "No review provided.")
                })
            elif isinstance(cat_value, str):
                avoid.append({
                    "name": model["name"],
                    "reason": cat_value
                })
        
        # Sort recommended by score (Highest to Lowest)
        recommended.sort(key=lambda x: x["score"], reverse=True)
        
        # Pagination Math
        total_pages = 1 + ((len(recommended) - 1) // self.items_per_page + 1) if recommended else 1
        
        embed = discord.Embed(title=f"{self.selected_category}", color=discord.Color.purple())
        
        # --- PAGE 0: SUMMARY (TOP PICKS & AVOID) ---
        if self.current_page == 0:
            top_recs = recommended[:5]
            top_avoids = avoid[:5] # Expanded to show up to 5 avoids on the first page
            
            rec_text = "\n\n".join([f"• **{m['name']}** - {m['score']}/10\n  *{m['review']}*" for m in top_recs])
            avoid_text = "\n\n".join([f"❌ **{m['name']}**\n  *{m['reason']}*" for m in top_avoids])
            
            if not rec_text: rec_text = "*No models tested for this category yet.*"
            if not avoid_text: avoid_text = "*No models flagged to avoid.*"
            
            embed.description = f"**🌟 Highlights (Page 1/{total_pages})**\n\n**✅ Top Picks:**\n\n{rec_text}\n\n**⚠️ Stay Away From:**\n\n{avoid_text}"
            
        # --- PAGE 1+: FULL DIRECTORY (SORTED & PAGINATED) ---
        else:
            start_idx = (self.current_page - 1) * self.items_per_page
            end_idx = start_idx + self.items_per_page
            page_recs = recommended[start_idx:end_idx]
            
            rec_text = "\n\n".join([f"• **{m['name']}** - {m['score']}/10\n  *{m['review']}*" for m in page_recs])
            embed.description = f"**📜 All Models (Page {self.current_page + 1}/{total_pages})**\n*Sorted from highest to lowest rating.*\n\n{rec_text}"

        self.prev_btn.disabled = (self.current_page == 0)
        self.next_btn.disabled = (self.current_page >= total_pages - 1)
        
        embed.set_footer(text="Tip: Copy the exact bolded name into your chat client UI.")
        
        await interaction.response.edit_message(embed=embed, view=self)


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