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

 # --- MODEL VERIFICATION CHECKLIST ---
# Total Count: 37 Models
#
# MOONSHOT (KIMI) FAMILY (5)
# 1. moonshotai/kimi-k2.6
# 2. moonshotai/kimi-k2.6:thinking
# 3. moonshotai/kimi-k2.5
# 4. moonshotai/kimi-k2.5:thinking
# 5. moonshotai/kimi-k2.7-code
#
# DEEPSEEK FAMILY (10)
# 6. deepseek/deepseek-v4-pro
# 7. deepseek/deepseek-v4-pro:thinking
# 8. deepseek/deepseek-v4-flash
# 9. deepseek/deepseek-v4-flash:thinking
# 10. deepseek/deepseek-v3.2
# 11. deepseek/deepseek-v3.2:thinking
# 12. deepseek-ai/DeepSeek-R1-0528
# 13. deepseek-ai/DeepSeek-V3.1
# 14. deepseek-v3-0324
# 15. deepseek-ai/DeepSeek-V3.1-Terminus
#
# MEITUAN (LONGCAT) FAMILY (2)
# 16. longcat-2.0
# 17. longcat-2.0:thinking
#
# Z.AI (GLM) FAMILY (8)
# 18. zai-org/glm-4.7
# 19. zai-org/glm-4.7:thinking
# 20. zai-org/glm-5
# 21. zai-org/glm-5:thinking
# 22. zai-org/glm-5.1
# 23. zai-org/glm-5.1:thinking
# 24. zai-org/glm-5.2
# 25. zai-org/glm-5.2:thinking
#
# NVIDIA (NEMOTRON) FAMILY (2)
# 26. nvidia/nemotron-3-ultra-550b-a55b
# 27. nvidia/nemotron-3-ultra-550b-a55b:thinking
#
# MINIMAX FAMILY (4)
# 28. minimax/minimax-m3
# 29. minimax/minimax-m3:thinking
# 30. minimax/minimax-m2.7
# 31. minimax/minimax-m2.5
#
# XIAOMI (MIMO) FAMILY (4)
# 32. xiaomi/mimo-v2.5
# 33. xiaomi/mimo-v2.5:thinking
# 34. xiaomi/mimo-v2.5-pro
# 35. xiaomi/mimo-v2.5-pro:thinking
#
# INCLUSIONAI (LING) FAMILY (2)
# 36. inclusionai/ling-3.0-flash
# 37. inclusionai/ling-3.0-flash:thinking
# ------------------------------------

    {
        "name": "moonshotai/kimi-k2.6",
        "🔥 Smut & NSFW": 10,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 10,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 5,
        "review": "PEAK SMUT. Generic writing style but insanely obedient; follows prompts to the letter so you can easily fix the style. Wonderfully creative when prompted right."
    },
    {
        "name": "moonshotai/kimi-k2.6:thinking",
        "🔥 Smut & NSFW": 10,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 10,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 5,
        "review": "Performs identically to base 2.6 for roleplay. Incredibly accurate to presets and highly recommended based on empirical testing."
    },
    {
        "name": "moonshotai/kimi-k2.5",
        "🔥 Smut & NSFW": 9,
        "🌧️ Angst & Drama": 8,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 9,
        "😂 Comedy & Humor": 6,
        "review": "An exceptional model for detailed, sensory-rich narrative and highly praised for both NSFW and emotional depth."
    },
    {
        "name": "moonshotai/kimi-k2.5:thinking",
        "🔥 Smut & NSFW": 9,
        "🌧️ Angst & Drama": 8,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 9,
        "😂 Comedy & Humor": 6,
        "review": "Thinking mode adds slightly more internal reasoning but remains effectively a top-tier roleplay model just like the base."
    },
    {
        "name": "moonshotai/kimi-k2.7-code",
        "🔥 Smut & NSFW": "AVOID: Incapable of narrative (Score: 2/10).",
        "🌧️ Angst & Drama": "AVOID: Strictly for programming (Score: 2/10).",
        "🩸 Gore & Dark Themes": "AVOID: Strictly for programming (Score: 2/10).",
        "✨ Creativity & Wildcard": "AVOID: Lacks creative spark entirely (Score: 2/10).",
        "🧠 Intelligence & Logic": 10,
        "🎭 Prose & Storytelling": "AVOID: Outputs cold, formatting-heavy code traces (Score: 1/10).",
        "😂 Comedy & Humor": "AVOID: Does not do humor (Score: 1/10).",
        "review": "A specialized coding model. Completely useless for roleplay or narrative purposes."
    },
    {
        "name": "deepseek/deepseek-v4-pro",
        "🔥 Smut & NSFW": 9,
        "🌧️ Angst & Drama": 8,
        "🩸 Gore & Dark Themes": 8,
        "✨ Creativity & Wildcard": 10,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 9,
        "😂 Comedy & Humor": 5,
        "review": "Incredible creativity that surpasses Kimi. Has a unique, high-quality writing style (though slightly harder to steer) and delivers perfectly detailed smut."
    },
    {
        "name": "deepseek/deepseek-v4-pro:thinking",
        "🔥 Smut & NSFW": 9,
        "🌧️ Angst & Drama": 8,
        "🩸 Gore & Dark Themes": 8,
        "✨ Creativity & Wildcard": 10,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 9,
        "😂 Comedy & Humor": 5,
        "review": "Retains the phenomenal creativity and detailed smut of the base model, with slightly enhanced world-building logic."
    },
    {
        "name": "deepseek/deepseek-v4-flash",
        "🔥 Smut & NSFW": 8,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 7,
        "🧠 Intelligence & Logic": 7,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": 5,
        "review": "A decent cheaper alternative to Pro. Creativity is a bit stunted and the writing style is a step down, but still solid."
    },
    {
        "name": "deepseek/deepseek-v4-flash:thinking",
        "🔥 Smut & NSFW": 8,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 7,
        "🧠 Intelligence & Logic": 7,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": 5,
        "review": "Similar to base Flash. Thinking mode might make the prose slightly drier, but it remains a capable lightweight option."
    },
    {
        "name": "deepseek/deepseek-v3.2",
        "🔥 Smut & NSFW": 7,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 7,
        "🧠 Intelligence & Logic": "AVOID: Tends to ignore prompts quite a bit (Score: 4/10).",
        "🎭 Prose & Storytelling": "AVOID: Writing style is full of slop and drives users insane (Score: 3/10).",
        "😂 Comedy & Humor": 5,
        "review": "Decent creativity, but completely ruined by an unbearable, 'slop-heavy' writing style and poor prompt adherence."
    },
    {
        "name": "deepseek/deepseek-v3.2:thinking",
        "🔥 Smut & NSFW": 7,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": "AVOID: Still struggles with obedience (Score: 4/10).",
        "🎭 Prose & Storytelling": "AVOID: Suffers from the exact same slop-filled prose as the base model (Score: 3/10).",
        "😂 Comedy & Humor": 5,
        "review": "Thinking mode adds a tiny bit of character consistency, but does not fix the awful writing style."
    },
    {
        "name": "deepseek-ai/DeepSeek-R1-0528",
        "🔥 Smut & NSFW": 9,
        "🌧️ Angst & Drama": 8,
        "🩸 Gore & Dark Themes": 8,
        "✨ Creativity & Wildcard": 10,
        "🧠 Intelligence & Logic": "AVOID: Doesn't stick to prompting well, forgets rules easily (Score: 4/10).",
        "🎭 Prose & Storytelling": 9,
        "😂 Comedy & Humor": 6,
        "review": "The undisputed king of creativity for fantasy mechanics. Peak writing style and unapologetically horny, though it suffers from older-model memory issues."
    },
    {
        "name": "deepseek-ai/DeepSeek-V3.1",
        "🔥 Smut & NSFW": 5,
        "🌧️ Angst & Drama": 6,
        "🩸 Gore & Dark Themes": 6,
        "✨ Creativity & Wildcard": 6,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 6,
        "😂 Comedy & Humor": "AVOID: Barely attempts humor (Score: 4/10).",
        "review": "Technically correct and highly analytical, but narratively flat and heavily censored compared to R1."
    },
    {
        "name": "deepseek-v3-0324",
        "🔥 Smut & NSFW": 8,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 7,
        "🧠 Intelligence & Logic": 7,
        "🎭 Prose & Storytelling": 6,
        "😂 Comedy & Humor": 5,
        "review": "An older but reliable foundational model that popularized uncensored generation, though its prose is a bit basic now."
    },
    {
        "name": "deepseek-ai/DeepSeek-V3.1-Terminus",
        "🔥 Smut & NSFW": 7,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 7,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": "AVOID: Plagued by the same V3.x slop-heavy writing style your friend warned about (Score: 4/10).",
        "😂 Comedy & Humor": 5,
        "review": "Noted in early reports as a highly logical and temporally aware workhorse, but ultimately ruined for roleplay by the unbearable, formulaic writing style characteristic of the V3.x family."
    },
    {
        "name": "longcat-2.0",
        "🔥 Smut & NSFW": 8,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 5,
        "review": "Formerly known as OWL. A highly recommended, 'quite peak' model with massive context capabilities and surprisingly organic handling of themes."
    },
    {
        "name": "longcat-2.0:thinking",
        "🔥 Smut & NSFW": 8,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 5,
        "review": "Scores match the base model; the reasoning mode does not drastically alter the already excellent roleplay output."
    },
    {
        "name": "zai-org/glm-4.7",
        "🔥 Smut & NSFW": "AVOID: High refusal rate (Score: 4/10).",
        "🌧️ Angst & Drama": "AVOID: Blocks self-harm and dark themes (Score: 3/10).",
        "🩸 Gore & Dark Themes": "AVOID: Heavily censored against violence (Score: 4/10).",
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": "AVOID: Lacks humor (Score: 4/10).",
        "review": "A highly creative and intelligent model, tragically ruined by harsh corporate censorship regarding romance and violence."
    },
    {
        "name": "zai-org/glm-4.7:thinking",
        "🔥 Smut & NSFW": "AVOID: High refusal rate (Score: 4/10).",
        "🌧️ Angst & Drama": "AVOID: Blocks self-harm and dark themes (Score: 3/10).",
        "🩸 Gore & Dark Themes": "AVOID: Heavily censored against violence (Score: 4/10).",
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": "AVOID: Lacks humor (Score: 4/10).",
        "review": "Thinking mode fails to bypass the strict corporate alignment."
    },
    {
        "name": "zai-org/glm-5",
        "🔥 Smut & NSFW": "AVOID: High refusal rate (Score: 4/10).",
        "🌧️ Angst & Drama": "AVOID: Avoids dark plots completely (Score: 3/10).",
        "🩸 Gore & Dark Themes": "AVOID: Censored (Score: 4/10).",
        "✨ Creativity & Wildcard": 7,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 6,
        "😂 Comedy & Humor": "AVOID: Serious and corporate (Score: 4/10).",
        "review": "A step backward from 4.7 in creativity, keeping all the suffocating safety filters."
    },
    {
        "name": "zai-org/glm-5:thinking",
        "🔥 Smut & NSFW": "AVOID: High refusal rate (Score: 4/10).",
        "🌧️ Angst & Drama": "AVOID: Avoids dark plots completely (Score: 3/10).",
        "🩸 Gore & Dark Themes": "AVOID: Censored (Score: 4/10).",
        "✨ Creativity & Wildcard": 7,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 6,
        "😂 Comedy & Humor": "AVOID: Serious and corporate (Score: 4/10).",
        "review": "Reasoning mode does not alleviate the censorship issues."
    },
    {
        "name": "zai-org/glm-5.1",
        "🔥 Smut & NSFW": "AVOID: Still heavily blocked (Score: 4/10).",
        "🌧️ Angst & Drama": "AVOID: Positivity bias destroys drama (Score: 4/10).",
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": 5,
        "review": "Better narrative coherence than 5.0, but still plagued by forced 'happy endings' and NSFW blocks."
    },
    {
        "name": "zai-org/glm-5.1:thinking",
        "🔥 Smut & NSFW": "AVOID: Still heavily blocked (Score: 4/10).",
        "🌧️ Angst & Drama": "AVOID: Positivity bias destroys drama (Score: 4/10).",
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": 5,
        "review": "Identical behavior to the base model in roleplay scenarios."
    },
    {
        "name": "zai-org/glm-5.2",
        "🔥 Smut & NSFW": 5,
        "🌧️ Angst & Drama": 5,
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 10,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 6,
        "review": "Acts like an incredibly intelligent RP partner with great prose, provided you can navigate its moderate content policies."
    },
    {
        "name": "zai-org/glm-5.2:thinking",
        "🔥 Smut & NSFW": 5,
        "🌧️ Angst & Drama": 5,
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 10,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 6,
        "review": "Reasoning mode is natively integrated; performance is identical to the base API."
    },
    {
        "name": "nvidia/nemotron-3-ultra-550b-a55b",
        "🔥 Smut & NSFW": 6,
        "🌧️ Angst & Drama": 8,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": 6,
        "review": "Highly energetic and creative with excellent general knowledge, though occasionally clunky in fine literary style."
    },
    {
        "name": "nvidia/nemotron-3-ultra-550b-a55b:thinking",
        "🔥 Smut & NSFW": 6,
        "🌧️ Angst & Drama": 8,
        "🩸 Gore & Dark Themes": 7,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": 6,
        "review": "Scores remain identical to the base version; the reasoning mode drastically slows down responses without notable improvements to the narrative."
    },
    {
        "name": "minimax/minimax-m3",
        "🔥 Smut & NSFW": "AVOID: Heavily censored (Score: 3/10).",
        "🌧️ Angst & Drama": 5,
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 6,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": "AVOID: Too neutral (Score: 4/10).",
        "review": "Massive context size but far too censored for unrestricted roleplay."
    },
    {
        "name": "minimax/minimax-m3:thinking",
        "🔥 Smut & NSFW": "AVOID: Heavily censored (Score: 3/10).",
        "🌧️ Angst & Drama": 5,
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 6,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 7,
        "😂 Comedy & Humor": "AVOID: Too neutral (Score: 4/10).",
        "review": "Reasoning mode does not save it from its deep censorship limits. Still heavily restricted for roleplay."
    },
    {
        "name": "minimax/minimax-m2.7",
        "🔥 Smut & NSFW": "AVOID: Inconsistent censorship (Score: 4/10).",
        "🌧️ Angst & Drama": 5,
        "🩸 Gore & Dark Themes": 5,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 8,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 5,
        "review": "Rich and evocative prose ('Opus-like'), but struggles with strict NSFW content without heavy jailbreaking."
    },
    {
        "name": "minimax/minimax-m2.5",
        "🔥 Smut & NSFW": "AVOID: Extreme censorship (Score: 2/10).",
        "🌧️ Angst & Drama": "AVOID: Emotionally flat (Score: 3/10).",
        "🩸 Gore & Dark Themes": "AVOID: Avoids intense violence (Score: 3/10).",
        "✨ Creativity & Wildcard": "AVOID: Terrible for RP (Score: 3/10).",
        "🧠 Intelligence & Logic": 7,
        "🎭 Prose & Storytelling": "AVOID: Rigid formatting (Score: 4/10).",
        "😂 Comedy & Humor": "AVOID: Non-existent (Score: 2/10).",
        "review": "Purely a coding model. Strongly advised against for any narrative use."
    },
    {
        "name": "xiaomi/mimo-v2.5",
        "🔥 Smut & NSFW": 7,
        "🌧️ Angst & Drama": 8,
        "🩸 Gore & Dark Themes": 6,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 9,
        "😂 Comedy & Humor": 7,
        "review": "Fantastic prose and emotional awareness. Slightly filtered on its native endpoint but handles NSFW well via open routers."
    },
    {
        "name": "xiaomi/mimo-v2.5:thinking",
        "🔥 Smut & NSFW": 7,
        "🌧️ Angst & Drama": 8,
        "🩸 Gore & Dark Themes": 6,
        "✨ Creativity & Wildcard": 9,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 9,
        "😂 Comedy & Humor": 7,
        "review": "Functions the same as base v2.5 in public APIs. Maintains great prose and emotional awareness, with the same slight filtration."
    },
    {
        "name": "xiaomi/mimo-v2.5-pro",
        "🔥 Smut & NSFW": 5,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 6,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 6,
        "review": "Highly intelligent but suffers from slightly heavier censorship and a more serious tone than its base counterpart."
    },
    {
        "name": "xiaomi/mimo-v2.5-pro:thinking",
        "🔥 Smut & NSFW": 5,
        "🌧️ Angst & Drama": 7,
        "🩸 Gore & Dark Themes": 6,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 9,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 6,
        "review": "Matches the Pro base version. Smarter logically but less spontaneous and slightly more censored than the standard v2.5."
    },
    {
        "name": "inclusionai/ling-3.0-flash",
        "🔥 Smut & NSFW": 9,
        "🌧️ Angst & Drama": 8,
        "🩸 Gore & Dark Themes": 8,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 10,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 6,
        "review": "An absolute powerhouse. Extremely uncensored, brilliant at maintaining plot momentum, and logically flawless."
    },
    {
        "name": "inclusionai/ling-3.0-flash:thinking",
        "🔥 Smut & NSFW": 9,
        "🌧️ Angst & Drama": 8,
        "🩸 Gore & Dark Themes": 8,
        "✨ Creativity & Wildcard": 8,
        "🧠 Intelligence & Logic": 10,
        "🎭 Prose & Storytelling": 8,
        "😂 Comedy & Humor": 6,
        "review": "Already behaves as a reasoning MoE by default. Incredibly potent, uncensored, and highly logical, perfectly mirroring its base flash scores."
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
        # Set the timeout to however many seconds you want (e.g., 120 seconds = 2 minutes)
        super().__init__(timeout=120) 
        self.message = None # We will store the message here later
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

    async def on_timeout(self):
        # 1. Disable all buttons and dropdowns
        for item in self.children:
            item.disabled = True
            
        # 2. Update the message to grey out the buttons, then send the timeout alert
        if self.message:
            try:
                await self.message.edit(view=self)
                await self.message.reply("⏳ This menu has timed out to save resources. Please run `/models` again to keep browsing.")
            except discord.HTTPException:
                pass

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
# --- 7. THE /models SLASH COMMAND ---
@bot.tree.command(name="models", description="Browse the curated list of roleplay models.")
async def models_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 The Roleplay Companion",
        description="Select a writing style from the dropdown menu below to see our group's highly recommended models.",
        color=discord.Color.blurple()
    )
    
    # 1. Create the view
    view = ModelView()
    
    # 2. Send the message
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
    
    # 3. Fetch the message that was just sent and give it to the view so it knows what to edit on timeout
    view.message = await interaction.original_response()

# --- 8. EXECUTION GUARD ---
if __name__ == "__main__":
    if DISCORD_TOKEN is None or NANOGPT_API_KEY is None:
        print("🚨 ERROR: Missing .env variables!", flush=True)
    else:
        bot.run(DISCORD_TOKEN)