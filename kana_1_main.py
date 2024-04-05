import discord
from discord.ext import commands
from discord.ui import Button
import asyncio
import random
import json
import os

bot =  commands.Bot(command_prefix=";", intents=discord.Intents.all())
bot.remove_command("help")

# Define the path to the JSON file
JSON_FILE = 'registered_users.json'

parired_channel_id = #CHANNEL ID for announcement of successful pairing

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=';blinddate'))
    load_registered_users()
    print("Profiles loaded")
    print('Kana is here!!')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Type ;help for available commands!!")

@bot.command()
@commands.has_any_role("role_name")
async def clearprofile(ctx, user_id: int):
    # Retrieve registered users
    registered_users = load_registered_users()

    # Check if the member is registered
    if str(user_id) in registered_users:
        del registered_users[str(user_id)]
        save_registered_users(registered_users)
        await ctx.send(f"Profile cleared for user with ID: {user_id}")
    else:
        await ctx.send(f"No profile found for user with ID: {user_id}")

@bot.command()
@commands.has_any_role("role_name")
async def checkprofile(ctx, user_id: int):
    # Retrieve registered users
    registered_users = load_registered_users()

    # Check if the user ID exists in registered users
    if str(user_id) in registered_users:
        user_data = registered_users[str(user_id)]
        gender = user_data['gender']
        status = user_data['status']
        age = user_data['age']
        interest = user_data['interest']
        words = ', '.join(user_data['words'])
        partner = user_data['partner']

        # Create an embed to display the user's profile
        profile_embed = discord.Embed(
            title="Profile Information",
            description=f"User ID: {user_id}",
            color=0x00ff00
        )
        profile_embed.add_field(name="Gender", value=gender, inline=True)
        profile_embed.add_field(name="Status", value=status, inline=True)
        profile_embed.add_field(name="Age", value=age, inline=True)
        profile_embed.add_field(name="Interest", value=interest, inline=False)
        profile_embed.add_field(name="Three Words", value=words, inline=False)

        if partner is None:
            profile_embed.add_field(name="Partner", value="None", inline=True)
        else:
            profile_embed.add_field(name="Partner", value=partner, inline=True)

        await ctx.send(embed=profile_embed)
    else:
        await ctx.send(f"No profile found for user with ID: {user_id}")

@bot.event
async def on_member_remove(member):
    # Retrieve registered users
    registered_users = load_registered_users()

    # Check if the member is registered
    if str(member.id) in registered_users:
        if registered_users[str(member.id)]['partner'] is not None:
            partner_id = registered_users[str(member.id)]['partner']
            if str(partner_id) in registered_users:
                registered_users[str(partner_id)]['partner'] = None

        del registered_users[str(member.id)]
        save_registered_users(registered_users)

@bot.command()
async def register(ctx):
    registered_users = load_registered_users()

    # Check if the user is already registered
    if str(ctx.author.id) in registered_users:
        await ctx.send(f"{ctx.author.mention} You are already registered.")
        return

    # Create a new registration channel for the user
    channel_name = f"registration-{ctx.author.id}"
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }

    registration_channel = await ctx.guild.create_text_channel(channel_name, overwrites=overwrites)

    # Send a registration welcome message
    await registration_channel.send(f"{ctx.author.mention} Welcome to the registration channel! Please follow the instructions to complete your registration.")
    # Inform the user in the original channel
    await ctx.send(f"{ctx.author.mention}, a new registration channel has been created for you. Please check {registration_channel.mention} to complete your registration.")

    welcome_embed = discord.Embed(
        title=f"{ctx.author.mention} Welcome to Kana's Blind Date!",
        description="React with a tick to continue",
        color=0xffbb00
    )
    welcome_msg = await registration_channel.send(embed=welcome_embed)
    await welcome_msg.add_reaction('✅')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) == '✅'

    try:
        reaction, _ = await bot.wait_for('reaction_add', timeout=60, check=check)
    except asyncio.TimeoutError:
        await registration_channel.send(f"{ctx.author.mention} Registration has timed out. Use ;register to register again!")
        await ctx.send(f"{ctx.author.mention} Registration has timed out. Use ;register to register again!")
        await registration_channel.delete()
        return

    # Prompt the user to select their gender
    gender_embed = discord.Embed(title="Gender Selection", description=f"{ctx.author.mention} Please select your gender:")
    gender_embed.add_field(name="Male", value="React with 👨", inline=True)
    gender_embed.add_field(name="Female", value="React with 👩", inline=True)

    gender_message = await registration_channel.send(embed=gender_embed)
    await gender_message.add_reaction("👨")
    await gender_message.add_reaction("👩")

    try:
        reaction, _ = await bot.wait_for(
            "reaction_add",
            check=lambda r, u: r.message.id == gender_message.id and u.id == ctx.author.id
                               and str(r.emoji) in ["👨", "👩"],
            timeout=60,
        )
    except asyncio.TimeoutError:
        await registration_channel.send(f"{ctx.author.mention} Timeout: You took too long to select your gender.")
        await ctx.send(f"{ctx.author.mention} Timeout: You took too long to select your gender. Please use ;register to register again!")
        await registration_channel.delete()
        return

    gender = "male" if str(reaction.emoji) == "👨" else "female"

    # Age input
    age_embed = discord.Embed(
        title="Age Input",
        description=f"{ctx.author.mention} Please type your age:",
        color=0xFFFFFF
    )
    await registration_channel.send(embed=age_embed)

    def check_age(message):
        return message.author == ctx.author and message.channel == registration_channel

    try:
        age_message = await bot.wait_for("message", check=check_age, timeout=60)
    except asyncio.TimeoutError:
        await registration_channel.send(f"Time is up {ctx.author.mention}! You took too long to provide your age. Please use ;register to register again!")
        await ctx.send(f"Time is up {ctx.author.mention}! You took too long to provide your age. Please use ;register to register again!")
        await registration_channel.delete()
        return

    age = age_message.content

    if not age.isdigit():
        await registration_channel.send(f"{ctx.author.mention}, please enter a valid number for your age.")
        return

    age = int(age)

    # Interests selection
    interests_embed = discord.Embed(
        title="What are your interests/hobbies",
        description=f"{ctx.author.mention} Please type your interests:",
        color=0xFFFFFF
    )
    await registration_channel.send(embed=interests_embed)

    try:
        interests_message = await bot.wait_for("message", check=check_age, timeout=120)
    except asyncio.TimeoutError:
        await registration_channel.send(f"Time is up {ctx.author.mention}! You took too long to provide your interests. Please use ;register to register again!")
        await ctx.send(f"Time is up {ctx.author.mention}! You took too long to provide your interests. Please use ;register to register again!")
        await registration_channel.delete()
        return

    interest = interests_message.content

    # Three words about themselves
    words_embed = discord.Embed(
        title="Describe yourself with three words",
        description=f"{ctx.author.mention} Please type three words about yourself: (comma-separated):",
        color=0xFFFFFF
    )
    await registration_channel.send(embed=words_embed)

    try:
        words_message = await bot.wait_for("message", check=check_age, timeout=120)
    except asyncio.TimeoutError:
        await registration_channel.send(f"Time is up {ctx.author.mention}! You took too long to provide three words about yourself. Please use ;register to register again!")
        await ctx.send(f"Time is up {ctx.author.mention}! You took too long to provide three words about yourself. Please use ;register to register again!")
        await registration_channel.delete()
        return

    words = words_message.content.split(",")

    # Confirmation
    confirm_embed = discord.Embed(
        title="Registration Confirmation",
        description=f"{ctx.author.mention} To confirm your registration, react with ✅",
        color=0x28ba00
    )
    confirm_message = await registration_channel.send(embed=confirm_embed)
    await confirm_message.add_reaction("✅")

    def check_confirmation(reaction, user):
        return (
            reaction.message.id == confirm_message.id
            and user.id == ctx.author.id
            and str(reaction.emoji) == "✅"
        )

    try:
        reaction, _ = await bot.wait_for(
            "reaction_add",
            check=check_confirmation,
            timeout=60,
        )
    except asyncio.TimeoutError:
        await registration_channel.send(f"Time is up {ctx.author.mention}! You took too long to confirm your registration. Please use ;register to register again!")
        await ctx.send(f"Time is up {ctx.author.mention}! You took too long to confirm your registration. Please use ;register to register again!")
        await registration_channel.delete()
        return

    # Registration confirmed!
    await registration_channel.send(f"Thank you for registering, {ctx.author.mention}!")
    await ctx.send(f"Thank you for registering, {ctx.author.mention}! Start playing by typing ;blinddate!")
    await registration_channel.delete()

    # Register the user
    registered_users[str(ctx.author.id)] = {
        'gender': gender,
        'status': 'single',
        'age': age,
        'interest': interest,
        'words': words,
        'partner': None  # Initialize partner as None
    }

    save_registered_users(registered_users)

@bot.command()
@commands.has_any_role("role_name")
async def listusers(ctx):
    # Retrieve registered users
    registered_users = load_registered_users()
    guild = ctx.guild

    if registered_users:
        users_list = []
        for user_id, user_data in registered_users.items():
            member = guild.get_member(int(user_id))
            username = member.name if member else "Unknown User"
            user_info = f"User ID: {user_id}, Username: {username}"
            users_list.append(user_info)

        embed = discord.Embed(
            title="Registered Users",
            description="\n".join(users_list),
            color=0x00ff00
        )

        await ctx.send(embed=embed)
    else:
        await ctx.send("No registered users found.")

@bot.command()
async def taken(ctx):
    # Retrieve registered users
    registered_users = load_registered_users()
    
    # Update the user's status to "taken"
    if str(ctx.author.id) in registered_users:
        registered_users[str(ctx.author.id)]['status'] = 'taken'
        save_registered_users(registered_users)
        embed = discord.Embed(title="You are in a relationship now!💕", description=f"{ctx.author.mention} You will not be picked by other members in the blind date! Use ;breakup to get picked by others ~~", color=0x28ba00)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="You're not registered", description=f"{ctx.author.mention} Use ;register to save your spot!", color=0xf20c0c)
        await ctx.send(embed=embed)

@bot.command()
async def breakup(ctx):
    # Retrieve registered users
    registered_users = load_registered_users()
    
    # Update the user's status to "single"
    if str(ctx.author.id) in registered_users:
        user_data = registered_users[str(ctx.author.id)]
        if user_data['status'] == 'single':
            embed = discord.Embed(title="You are already single!💔", description=f"{ctx.author.mention} You are not currently in a relationship.", color=0x28ba00)
            await ctx.send(embed=embed)
            return

    if str(ctx.author.id) in registered_users:
        user_data = registered_users[str(ctx.author.id)]
        if user_data['partner'] is None:
            embed = discord.Embed(title="Your status is single now!💔", description=f"{ctx.author.mention} Use ;blinddate to play!", color=0x28ba00)
            await ctx.send(embed=embed)
             # Update the user's partner field and status
            registered_users[str(ctx.author.id)]['partner'] = None
            registered_users[str(ctx.author.id)]['status'] = 'single'
            save_registered_users(registered_users)
            return

        partner_id = user_data['partner']
        # Remove the paired user's partner field
        registered_users[partner_id]['partner'] = None

        # Update the user's partner field and status
        registered_users[str(ctx.author.id)]['partner'] = None
        registered_users[str(ctx.author.id)]['status'] = 'single'
        # Update the partner's status
        registered_users[partner_id]['status'] = 'single'

        save_registered_users(registered_users)

        embed = discord.Embed(title="You are single now!💔", description=f"{ctx.author.mention} You are no longer paired with {ctx.guild.get_member(int(partner_id)).mention}💔.", color=0x28ba00)
        await ctx.send(embed=embed)
        breakup_channel = bot.get_channel(parired_channel_id)
        await breakup_channel.send(f"{ctx.author.mention} is no longer paired with {ctx.guild.get_member(int(partner_id)).mention}💔.")

    else:
        embed = discord.Embed(title="You're not registered", description=f"{ctx.author.mention} Use ;register to save your spot!", color=0xf20c0c)
        await ctx.send(embed=embed)


@bot.command()
async def blinddate(ctx):
    registered_users = load_registered_users()
    requester_id = str(ctx.author.id)

    if requester_id not in registered_users:
        embed = discord.Embed(
            title="You are not registered!",
            description=f"{ctx.author.mention} Please use ;register before using the blinddate feature.",
            color=0xf20c0c
        )
        await ctx.send(embed=embed)
        return

    requester_gender = registered_users[requester_id]['gender']
    user_status = registered_users[requester_id]['status']

    if user_status == 'taken':
        tembed = discord.Embed(
            title="You can't join the blinddate when you are taken!",
            description=f"{ctx.author.mention} Use ;breakup to break up and join another round ~~",
            color=0x28ba00
        )
        await ctx.send(embed=tembed)
        return

    # Get the list of available dates (users)
    available_dates = [
        user_id for user_id in registered_users.keys()
        if user_id != requester_id and registered_users[user_id]['status'] == 'single'
        and registered_users[user_id]['gender'] != requester_gender
    ]

    # Shuffle the available dates list randomly
    random.shuffle(available_dates)

    if len(available_dates) < 4:
        embed = discord.Embed(
            title="Oops!",
            description=f"{ctx.author.mention} Not enough registered users to create a match. At least 4 single males and 4 single females are required! Invite your friends and play together!",
            color=0xf20c0c
        )
        await ctx.send(embed=embed)
        return

    # Create a list of pages containing users' information
    pages = []
    for user_id in available_dates:
        user = await bot.fetch_user(int(user_id))
        gender_d = registered_users[user_id]['gender']
        status_d = registered_users[user_id]['status']
        interest_d = registered_users[user_id]['interest']
        age_d = registered_users[user_id]['age']
        words_d = registered_users[user_id]['words']
        embed = discord.Embed(
            title="Select your date",
            description=f"{ctx.author.mention} Choose a date from the options below:"
        )
        embed.add_field(
            name=user.name,
            value=f"Gender: {gender_d}\nStatus: {status_d}\nAge: {age_d}\nInterests: {interest_d}\nPersonalities: {words_d}",
            inline=False
        )
        pages.append(embed)

    # Set up initial page and buttons
    current_page = 0
    buttons = [
        "\u23ee",  # "<<"
        "\u25c0",  # "<"
        "\u2705",  # "Select"
        "\u25b6",  # ">"
        "\u23ed",  # ">>"
    ]

    message = await ctx.send(embed=pages[current_page])

    for button in buttons:
        await message.add_reaction(button)

    def check(reaction, user):
        return (
            user == ctx.author
            and str(reaction.emoji) in buttons
            and reaction.message == message
        )

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=180, check=check)

            if str(reaction.emoji) == "\u23ee":  # "<<"
                current_page = 0
            elif str(reaction.emoji) == "\u25c0":  # "<"
                if current_page > 0:
                    current_page -= 1
            elif str(reaction.emoji) == "\u2705":  # "Select"
                selected_date_id = available_dates[current_page]
                selected_date = await bot.fetch_user(int(selected_date_id))

                registered_users[requester_id]['partner'] = selected_date_id  # Update requester's partner ID
                registered_users[selected_date_id]['partner'] = requester_id  # Update selected date's partner ID

                registered_users[requester_id]['status'] = 'taken'  # Update requester's status to "taken"
                registered_users[selected_date_id]['status'] = 'taken'  # Update selected date's status to "taken"
                save_registered_users(registered_users)  # Save updated registered users


                embed_pairing = discord.Embed(
                    title="💘Blinddates Matched!💘",
                    color=discord.Color.green()
                )
                embed_pairing.add_field(
                    name=f"{ctx.author.mention} You are now paired with {selected_date.name} for a blind date!",
                    value=f"Congratulations!! <@{ctx.author.id}> and <@{selected_date_id}> are paired together🤵🏻👰!!"
                )
                await ctx.send(embed=embed_pairing)
                await ctx.send(f"Congratulations!! <@{ctx.author.id}> and <@{selected_date_id}> are paired together🤵🏻👰!!")
                await ctx.send(f"<@{ctx.author.id}> and <@{selected_date_id}> : Chat with each other as you guys are paired together! Good Luck✨🎉!!")
                wedding_channel = bot.get_channel(parired_channel_id)
                await wedding_channel.send(f"Congratulations!! <@{ctx.author.id}> and <@{selected_date_id}> are paired together🤵🏻👰!!")
                break

            elif str(reaction.emoji) == "\u25b6":  # ">"
                if current_page < len(pages) - 1:
                    current_page += 1
            elif str(reaction.emoji) == "\u23ed":  # ">>"
                current_page = len(pages) - 1

            await message.edit(embed=pages[current_page])
            await message.remove_reaction(reaction, user)

        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.mention} You took too long to make a selection.")
            break

def load_registered_users():
    global JSON_FILE

    if not os.path.isfile(JSON_FILE):
        print("Balances file not found. Starting with empty profile.")
        # Create an empty JSON file
        with open(JSON_FILE, "w") as file:
            json.dump({}, file)
        return {}

    try:
        with open(JSON_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error loading balances file.")
        return {}
    

def save_registered_users(registered_users):
    with open(JSON_FILE, 'w') as file:
        json.dump(registered_users, file)


@bot.command()
async def datesoverview(ctx):
    # Retrieve registered users
    registered_users = load_registered_users()

    # Check if there are any registered users
    if not registered_users:
        await ctx.send('No users registered.')
        return

    # Count the number of registered males and females
    male_count = sum(1 for user in registered_users.values() if user['gender'] == 'male')
    female_count = sum(1 for user in registered_users.values() if user['gender'] == 'female')

    # Count the number of single and taken males and females
    male_singles = sum(1 for user in registered_users.values() if user['gender'] == 'male' and user['status'] == 'single')
    male_takens = sum(1 for user in registered_users.values() if user['gender'] == 'male' and user['status'] == 'taken')
    female_singles = sum(1 for user in registered_users.values() if user['gender'] == 'female' and user['status'] == 'single')
    female_takens = sum(1 for user in registered_users.values() if user['gender'] == 'female' and user['status'] == 'taken')

    # Create an embed to display the user counts
    embed = discord.Embed(title="Registered Users", color=discord.Color.blue())
    embed.add_field(name="Total Users", value=str(len(registered_users)), inline=False)
    embed.add_field(name="Male Users", value=str(male_count), inline=True)
    embed.add_field(name="Male Singles", value=str(male_singles), inline=True)
    embed.add_field(name="Male Takens", value=str(male_takens), inline=True)
    embed.add_field(name="Female Users", value=str(female_count), inline=True)
    embed.add_field(name="Female Singles", value=str(female_singles), inline=True)
    embed.add_field(name="Female Takens", value=str(female_takens), inline=True)
    embed.set_footer(text="Tip; ;blinddate will be locked if there are less than 4 single males and females! Invite your friends and play!")
    # Send the embed as a message in the Discord channel
    await ctx.send(embed=embed)
    
# convo starters

responses = responses = [
    'Tell me about yourself.',
    'What have been the best part of your day so far?',
    'What do you do to relax?',
    'What book are you reading right now?',
    'What is your favorite thing about your hometown?',
    'What would be your perfect weekend?',
    'What is something (besides your phone) that you take with you everywhere?',
    'What is your favorite season and why?',
    'What is your hidden talent?',
    'Do you have any pets?',
    'What is something you are obsessed with?',
    'What would be your perfect weekend?',
    'What is your favorite number? Why?',
    'What are you going to do this weekend?',
    'What did you do on your last vacation?',
    'What is the best / worst thing about your work/school?',
    'If you could have any animal as a pet, what animal would you choose?',
    'What is the strangest dream you have ever had?',
    'What is the most annoying habit someone can have?',
    'What animal or insect do you wish humans could eradicate?',
    'Do you believe in aliens, why or why not?',
    'What is the most disgusting habit some people have?',
    'Where is the most beautiful place near where you live?',
    'Where is the worst place you have been stuck for a long time?',
    'What do you fear is hiding in the dark?',

]

@bot.command()
async def convostarter(ctx):
    response = random.choice(responses)
    embed = discord.Embed(title=f"{response}", color=0x00f2ea)
    await ctx.send(embed=embed)

@bot.command()
async def mystatus(ctx):
    # Retrieve registered users
    registered_users = load_registered_users()

    # Check if the user is registered
    if str(ctx.author.id) not in registered_users:
        embed = discord.Embed(
            title="You are not registered!",
            description=f"{ctx.author.mention} Use ;register to join the blind date!",
            color=0xf20c0c
        )
        await ctx.send(embed=embed)
        return

    user_data = registered_users[str(ctx.author.id)]
    user_role = user_data['gender']
    user_status = user_data['status']
    user_age = user_data['age']
    user_interest = user_data['interest']
    user_words = user_data['words']
    user_couple_id = user_data['partner']

    # Get the partner's username if the user has a partner
    user_couple_username = None
    if user_couple_id:
        user_couple_username = bot.get_user(int(user_couple_id)).name

    # Create an embed to display the user's status and role
    embed = discord.Embed(title="My Status", color=discord.Color.orange())
    embed.add_field(name="Gender:", value=user_role, inline=False)
    embed.add_field(name="Status:", value=user_status, inline=False)
    embed.add_field(name="Age:", value=user_age, inline=False)
    embed.add_field(name="Interests:", value=user_interest, inline=False)
    embed.add_field(name="Personalities:", value=user_words, inline=False)
    embed.add_field(name="Partner:", value=user_couple_username or "None", inline=False)
    # Send the embed as a message in the Discord channel
    await ctx.send(embed=embed)

#custommsg
@bot.command()
@commands.has_any_role("role_name")
async def custommsg(ctx, embed_option: str, color: str, *, message):
    if embed_option.lower() == 'yes':
        embed = discord.Embed(description=message, color=discord.Color(int(color, 16)))
        await ctx.send(embed=embed)
    else:
        await ctx.send(message)

@bot.command()
async def changegender(ctx):

    # Retrieve registered users
    registered_users = load_registered_users()
    
    # Check if the user is registered
    if str(ctx.author.id) not in registered_users:
        embed = discord.Embed(title="You are not registered!", description=f"{ctx.author.mention} Use ;register to join the blind date!", color=0xf20c0c)
        await ctx.send(embed=embed)
        return
    
    # Prompt the user to select their gender
    genderedit_embed = discord.Embed(title="Gender Selection", description=f"{ctx.author.mention} Edit your gender:", color=discord.Color.gold())
    genderedit_embed.add_field(name="Male", value="React with 👨", inline=True)
    genderedit_embed.add_field(name="Female", value="React with 👩", inline=True)

    genderedit_message = await ctx.send(embed=genderedit_embed)
    await genderedit_message.add_reaction("👨")
    await genderedit_message.add_reaction("👩")

    try:
        reaction, _ = await bot.wait_for(
            "reaction_add",
            check=lambda r, u: r.message.id == genderedit_message.id and u.id == ctx.author.id
                               and str(r.emoji) in ["👨", "👩"],
            timeout=60,
        )
    except asyncio.TimeoutError:
        await ctx.send(f"Time is up {ctx.author.mention}! You took too long to select your gender, please use ;register to register again!")
        return

    new_gender = "male" if str(reaction.emoji) == "👨" else "female"

    # Update the user's role
    registered_users[str(ctx.author.id)]["gender"] = new_gender
    save_registered_users(registered_users)
    
    genderupdate_embed = discord.Embed(title=f"{ctx.author.mention} Your gender has been updated successfully.", color=0x28ba00)
    await ctx.send(embed=genderupdate_embed)
    
    # Send the embed as a message in the Discord channel
    await ctx.send(embed=embed)

@bot.command()
async def changeage(ctx):

    # Retrieve registered users
    registered_users = load_registered_users()

    user_id = str(ctx.author.id)

    if user_id not in registered_users:
        embed = discord.Embed(title="You are not registered!", description=f"{ctx.author.mention} Use ;register to join the blind date!", color=0xf20c0c)
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(title="What is your new age?", description=f"{ctx.author.mention} Please type your age in numerical form!", color=discord.Color.gold())
    await ctx.send(embed=embed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    while True:
        age_msg = await bot.wait_for("message", check=check)
        new_age = age_msg.content

        if not new_age.isdigit():
            age_embed_fail = discord.Embed(title=f"{ctx.author.mention} Please enter a valid number for your age.", color=0xf20c0c)
            await ctx.send(embed=age_embed_fail)
        else:
            new_age = int(new_age)
            break

    registered_users[str(ctx.author.id)]["age"] = new_age

    ageupdate_embed = discord.Embed(title=f"{ctx.author.mention} Your age has been updated successfully.", color=0x28ba00)
    await ctx.send(embed=ageupdate_embed)

    # Save registered_users to a file or database
    save_registered_users(registered_users)


@bot.command()
async def changeinterest(ctx):

    # Retrieve registered users
    registered_users = load_registered_users()

    user_id = str(ctx.author.id)

    if user_id not in registered_users:
        embed = discord.Embed(title="You are not registered!", description=f"{ctx.author.mention} Use ;register to join the blind date!", color=0xf20c0c)
        await ctx.send(embed=embed)
        return

    interestembed = discord.Embed(title="Edit your interest/hobbies", description=f"{ctx.author.mention} Let other see your interests/hobbies!!", color=discord.Color.gold())
    await ctx.send(embed=interestembed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    interest_msg = await bot.wait_for("message", check=check)
    new_interest = interest_msg.content

    registered_users[str(ctx.author.id)]["interest"] = new_interest

    interestupdate_embed = discord.Embed(title=f"{ctx.author.mention} Your interests has been updated successfully.", color=0x28ba00)
    await ctx.send(embed=interestupdate_embed)

    # Save registered_users to a file or database
    save_registered_users(registered_users)

@bot.command()
async def changewords(ctx):

    # Retrieve registered users
    registered_users = load_registered_users()

    user_id = str(ctx.author.id)

    if user_id not in registered_users:
        embed = discord.Embed(title="You are not registered!", description=f"{ctx.author.mention} Use ;register to join the blind date!", color=0xf20c0c)
        await ctx.send(embed=embed)
        return

    wordembed = discord.Embed(title="Edit your three words to describe yourself!", description=f"{ctx.author.mention} Example: 'curious', 'shy', 'happy'.", color=discord.Color.gold())
    await ctx.send(embed=wordembed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    words_msg = await bot.wait_for("message", check=check)
    new_words = words_msg.content

    registered_users[str(ctx.author.id)]["words"] = new_words

    interestupdate_embed = discord.Embed(title=f"{ctx.author.mention} Your interests has been updated successfully.",  color=0x28ba00)
    await ctx.send(embed=interestupdate_embed)

    # Save registered_users to a file or database
    save_registered_users(registered_users)

@bot.command()
async def help(ctx):
  embed = discord.Embed(title="Help", description="Commands that can be used by the bot:", color=0x0ffc76)
  embed.add_field(name=";register", value="Join the blind date!", inline=False)
  embed.add_field(name=";blinddate", value="Match you with a partner that is single and registered", inline=False)
  embed.add_field(name=";taken", value="You are in a relationship and will not be picked by others in the blind date", inline=False)
  embed.add_field(name=";breakup", value="Opt out of a relationship and be picked by others in the blind date", inline=False)
  embed.add_field(name=";convostarter", value="Use this to start conversations", inline=False)
  embed.add_field(name=";mystatus", value="See your dating profile!", inline=False)
  embed.add_field(name=";changegender", value="Change your gender!", inline=False)
  embed.add_field(name=";changeage", value="Change your age!", inline=False)
  embed.add_field(name=";changeinterest", value="Change your interests/hobbies!", inline=False)
  embed.add_field(name=";changewords", value="Change your three word description!", inline=False)
  embed.add_field(name=";datesoverview", value="Show total users and total gender count!", inline=False)
  embed.set_footer(text="Bot made by LeonTheGreat21, report any bugs if found")
  await ctx.send(embed=embed)

# Run the bot using your bot token
bot.run('token')