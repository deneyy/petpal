import discord
from discord.ext import commands, tasks
import json
import os
import random
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

intents = discord.Intents.default()
intents.message_content = True

PET_TYPES = {
    'car': ['car', 'big car', 'tiger'],
    'dawg': ['dawg', 'big dawg', 'wolf'],
    'dragon': ['baby dragon', 'dragon', 'elder dragon'],
    'hampter': ['hampter', 'guinea pig', 'capybara'],
    'bird': ['chick', 'parrot', 'phoenix']
}

PET_EMOJIS = {
    'car': '😺', 'big car': '🐈‍⬛', 'tiger': '🐯',
    'dawg': '🐶', 'big dawg': '🐕', 'wolf': '🐺',
    'baby dragon': '🦎', 'dragon': '🐉', 'elder dragon': '🐲',
    'hampter': '🐹', 'guinea pig': '🐹', 'capybara': '🦫',
    'chick': '🐤', 'parrot': '🦜', 'phoenix': '🔥'
}

DATA_FILE = 'petpal_data.json'

bot = commands.Bot(command_prefix='/', intents=intents)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_evolution_stage(level):
    if level < 5:
        return 0
    elif level < 10:
        return 1
    else:
        return 2

def calculate_xp_needed(level):
    return 100 + (level * 50)

def create_pet_card(pet_data, username):
    img = Image.new('RGB', (500, 400), color=(44, 47, 51))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        stat_font = ImageFont.truetype("arial.ttf", 18)
    except:
        title_font = ImageFont.load_default()
        stat_font = ImageFont.load_default()

    emoji = PET_EMOJIS.get(pet_data['current_name'], '🐾')
    title = f"{emoji} {pet_data['name']} {emoji}"
    draw.text((250, 30), title, fill=(255, 255, 255), font=title_font, anchor="mm")

    type_text = f"{pet_data['current_name']} | level {pet_data['level']}"
    draw.text((250, 70), type_text, fill=(255, 255, 255), font=stat_font, anchor="mm")

    xp_needed = calculate_xp_needed(pet_data['level'])
    xp_percent = pet_data['xp'] / xp_needed
    draw.rectangle([50, 100, 450, 120], fill=(70, 70, 70))
    draw.rectangle([50, 100, 50 + int(400 * xp_percent), 120], fill=(88, 101, 242))
    draw.text((250, 110), f"XP: {pet_data['xp']}/{xp_needed}", fill=(255, 255, 255), font=stat_font, anchor="mm")

    stats = [
        ('hunger', pet_data['hunger'], (137, 66, 69)),
        ('happiness', pet_data['happiness'], (254, 231, 92)),
        ('energy', pet_data['energy'], (87, 242, 135))
    ]

    y_pos = 160
    for stat_name, value, color in stats:
        draw.text((70, y_pos), f"{stat_name}:", fill=(200, 200, 200), font=stat_font)

        draw.rectangle([170, y_pos - 5, 450, y_pos + 20], fill=(70, 70, 70))

        bar_width = int(280 * (value / 100))
        draw.rectangle([170, y_pos - 5, 170 + bar_width, y_pos + 20], fill=color)

        draw.text((310, y_pos + 7), f"{value}/100", fill=(255, 255, 255), font=stat_font, anchor="mm")

        y_pos += 50

    draw.text((250, 350), f"owner: {username}", fill=(150, 150, 150), font=stat_font, anchor="mm")

    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

@bot.event
async def on_ready():
    print(f'{bot.user} is online! woohoo')
    decay_stats.start()

@bot.command()
async def adopt(ctx):
    """adopt a new pet"""
    data = load_data()
    user_id = str(ctx.author.id)

    if user_id in data:
        await ctx.send("sorry, you already have a pet. use `/abandon` if you want another one.")
        return
    
    pet_type = random.choice(list(PET_TYPES.keys()))
    evolution_chain = PET_TYPES[pet_type]

    data[user_id] = {
        'name': evolution_chain[0],
        'type': pet_type,
        'current_name': evolution_chain[0],
        'level': 1,
        'xp': 0,
        'hunger': 50,
        'happiness': 80,
        'energy': 100,
        'evolution': 0,
        'last_update': datetime.now().isoformat(),
        'coins': 0
    }

    save_data(data)

    emoji = PET_EMOJIS.get(evolution_chain[0], '🐾')
    embed = discord.Embed(
        title=f"congrats!",
        description=f"you adopted a {emoji} **{evolution_chain[0]}**!\n\ntake care of your new pet by feeding, playing and making sure the pet rests well!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command()
async def petinfo(ctx, user: discord.Member = None):
    """view your pets stats"""
    data = load_data()
    target = user if user else ctx.author
    user_id = str(target.id)

    if user_id not in data:
        await ctx.send("this user does not have a pet yet!")
        return
    
    pet = data[user_id]

    try:
        img = create_pet_card(pet, target.display_name)
        file = discord.File(img, filename="pet_card.png")
        await ctx.send(file=file)
    except Exception as e:
        emoji = PET_EMOJIS.get(pet['current_name'], '🐾')
        xp_needed = calculate_xp_needed(pet['level'])

        embed = discord.Embed(
            title=f"{emoji} {pet['name']}",
            description=f"**type:** {pet['current_name']}\n**level:** {pet['level']} ({pet['xp']}/{xp_needed} xp)",
            color=discord.Color.blue()
        )
        embed.add_field(name="hunger", value=f"{pet['hunger']}/100", inline=True)
        embed.add_field(name="happiness", value=f"{pet['happiness']}/100", inline=True)
        embed.add_field(name="energy", value=f"{pet['energy']}/100", inline=True)
        embed.add_field(name="coins", value=f"{pet['coins']}", inline=True)
        embed.set_footer(text=f"owner: {target.display_name}")

        await ctx.send(embed=embed)

@bot.command()
async def feed(ctx):
    """feed your pet"""
    data = load_data()
    user_id = str(ctx.author.id)

    if user_id not in data:
        await ctx.send("you dont have a pet yet! use `/adopt` to get one.")
        return
    
    pet = data[user_id]

    if pet['hunger'] <= 10:
        await ctx.send(f"{pet['name']} is already full!")
        return
    
    pet['hunger'] = max(0, pet['hunger'] - 30)
    pet['happiness'] = min(100, pet['happiness'] + 10)
    pet['xp'] += 5

    check_level_up(pet)
    save_data(data)

    emoji = PET_EMOJIS.get(pet['current_name'], '🐾')
    await ctx.send(f"{emoji} **{pet['name']}** enjoyed the meal!\n+10 happiness, -30 hunger, +5 xp")

@bot.command()
async def play(ctx):
    """play with your pet"""
    data = load_data()
    user_id = str(ctx.author.id)

    if user_id not in data:
        await ctx.send("you dont have a pet yet! use `/adopt` to get one.")
        return

    pet = data[user_id]

    if pet['energy'] < 20:
        await ctx.send(f"{pet['name']} is too tired to play. rest by using `/sleep`.")
        return
    
    pet['energy'] = max(0, pet['energy'] - 20)
    pet['happiness'] = min(100, pet['happiness'] + 20)
    pet['xp'] += 10
    coins_earned = random.randint(1, 5)
    pet['coins'] += coins_earned

    check_level_up(pet)
    save_data(data)

    emoji = PET_EMOJIS.get(pet['current_name'], '🐾')
    activities = ['fetch', 'tug-of-war', 'hide and seek', 'catch the toy']
    activity = random.choice(activities)

    await ctx.send(f"{emoji} **{pet['name']}** had fun playing {activity}!\n+20 happiness, -20 energy, +10 xp, +{coins_earned} coins")

@bot.command()
async def sleep(ctx):
    """let your pet sleep"""
    data = load_data()
    user_id = str(ctx.author.id)

    if user_id not in data:
        await ctx.send("you dont have a pet yet! use `/adopt` to get one.")
        return
    
    pet = data[user_id]

    if pet['energy'] >= 90:
        await ctx.send(f"{pet['name']} is too full of energy to sleep!")
        return
    
    pet['energy'] = min(100, pet['energy'] + 40)
    pet['hunger'] = min(100, pet['hunger'] + 10)
    pet['xp'] += 3

    check_level_up(pet)
    save_data(data)

    emoji = PET_EMOJIS.get(pet['current_name'], '🐾')
    await ctx.send(f"{emoji} **{pet['name']}** had a good nap!\n+40 energy, +10 hunger, +3 xp")

@bot.command()
async def rename(ctx, *, new_name: str):
    """rename your pet"""
    data = load_data()
    user_id = str(ctx.author.id)

    if user_id not in data:
        await ctx.send("you dont have a pet yet! use `/adopt` to get one.")
        return
    
    if len(new_name) > 20:
        await ctx.send("sorry, but your pet name is too long! please make one using 20 characters or less!")
        return
    
    old_name = data[user_id]['name']
    data[user_id]['name'] = new_name
    save_data(data)

    emoji = PET_EMOJIS.get(data[user_id]['current_name'], '🐾')
    await ctx.send(f"{emoji} your pet ({old_name}) has been renamed to **{new_name}**!")

@bot.command()
async def leaderboard(ctx):
    """view the top pets from the entire server"""
    data = load_data()

    if not data:
        await ctx.send("no pets have been adopted yet. be the first one by typing in `/adopt`!")
        return
    
    sorted_pets = sorted(data.items(), key=lambda x: (x[1]['level'], x[1]['xp']), reverse=True)[:10]

    embed = discord.Embed(
        title="petpal leaderboard",
        description="top 10 pets by level",
        color=discord.Color.gold()
    )

    for idx, (user_id, pet) in enumerate(sorted_pets, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            username = user.display_name
        except:
            username = "unknown"
        
        emoji = PET_EMOJIS.get(pet['current_name'], '🐾')
        embed.add_field(
            name=f"{idx}. {emoji} {pet['name']}",
            value=f"level {pet['level']} | owner: {username} | happiness: {pet['happiness']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command()
async def abandon(ctx):
    """abandon your pet"""
    data = load_data()
    user_id = str(ctx.author.id)

    if user_id not in data:
        await ctx.send("you dont have a pet yet! use `/adopt` to get one.")
        return
    
    pet_name = data[user_id]['name']
    del data[user_id]
    save_data(data)

    await ctx.send(f"you abandoned **{pet_name}**...")

def check_level_up(pet):
    """check if the pet should level up or evolve"""
    xp_needed = calculate_xp_needed(pet['level'])

    while pet['xp'] >= xp_needed:
        pet['xp'] -= xp_needed
        pet['level'] += 1

        evolution_stage = get_evolution_stage(pet['level'])
        if evolution_stage > pet['evolution']:
            pet['evolution'] = evolution_stage
            evolution_chain = PET_TYPES[pet['type']]
            pet['current_name'] = evolution_chain[evolution_stage]
        
        xp_needed = calculate_xp_needed(pet['level'])

@tasks.loop(hours=1)
async def decay_stats():
    """slowly decrease pet stats over time"""
    data = load_data()

    for user_id, pet in data.items():
        pet['hunger'] = min(100, pet['hunger'] + 5)
        if pet['hunger'] > 80 or pet['energy'] < 20:
            pet['happiness'] = max(0, pet['happiness'] - 10)
        else:
            pet['happiness'] = max(0, pet['happiness'] - 2)
        
        pet['last_update'] = datetime.now().isoformat()

    save_data(data)

# Run the bot
if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables!")
    else:
        bot.run(token)
