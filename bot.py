import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
from requests.exceptions import RequestException

# Load environment variables
load_dotenv()

# Get the Discord bot token and validate it
discord_token = os.getenv("DISCORD_BOT_TOKEN")
if not discord_token:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is not set. Please check your .env file.")
print(f"DEBUG: discord_token type: {type(discord_token)}")  # Debug token type

# Configure intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent to read command arguments

# Initialize the bot with a command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Hugging Face API configuration
API_URL = "https://router.huggingface.co/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.getenv('HF_TOKEN')}",
}
print(f"DEBUG: HF_TOKEN in headers: {os.getenv('HF_TOKEN')[:5]}...")  # Debug token prefix (partial for security)

def send_hf_request(payload):
    """
    Send a query to the Hugging Face API and return the response.
    """
    print(f"DEBUG: send_hf_request called with payload: {payload}")  # Debug payload
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)  # 10-second timeout
        print(f"DEBUG: API response status code: {response.status_code}")  # Debug status code
        print(f"DEBUG: API response text: {response.text}")  # Debug response text
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except RequestException as e:
        print(f"DEBUG: RequestException: {str(e)}")  # Log detailed exception
        raise

@bot.event
async def on_ready():
    print(f"Bot is ready. Logged in as {bot.user}")

@bot.command(name="ai")
async def ai_command(ctx, *, query):
    """
    Command to query the Hugging Face Llama model.
    Usage: !ai <your question>
    """
    try:
        print(f"DEBUG: Entering ai_command, query type: {type(query)}")  # Debug query parameter
        print(f"DEBUG: query parameter value: {query}")  # Debug query value
        # Prepare payload and send request
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "model": "meta-llama/Llama-3.1-8B-Instruct:cerebras"
        }
        response = send_hf_request(payload)

        # Parse response to extract answer after </think> if present
        content = response["choices"][0]["message"]["content"]
        print(f"DEBUG: Raw content: {content}")  # Debug raw content
        if "<think>" in content and "</think>" in content:
            result = content.split("</think>")[1].strip()
        else:
            result = content.strip()

        # Ensure response fits Discord's 2000-character limit
        if len(result) > 2000:
            result = result[:1997] + "..."

        # Send response to Discord
        await ctx.send(result)

    except requests.RequestException as e:
        await ctx.send(f"Error: Unable to process request ({str(e)}). Please check the terminal for details.")
    except (KeyError, ValueError) as e:
        await ctx.send(f"Error: Invalid response from the API ({str(e)}). Please check the terminal for details.")

# Run the bot
bot.run(discord_token)