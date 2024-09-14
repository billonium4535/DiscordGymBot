import asyncio
import json
import requests
import os
import discord
from discord import app_commands
from discord.ext import tasks
from datetime import datetime, timedelta
import credential_handler
import password_handler

BASIC_HEADERS = {
    "x-api-key": "with_great_power",
    "Content-Type": "application/json",
    "accept-encoding": "gzip",
}

guild = int(open(f"{os.path.dirname(__file__)}/guild.txt", "r").read())
channel = int(open(f"{os.path.dirname(__file__)}/channel.txt", "r").read())


def hevy_login(user: str, password: str):
    headers = BASIC_HEADERS.copy()
    session = requests.Session()
    response = session.post(
        "https://api.hevyapp.com/login",
        data=json.dumps({"emailOrUsername": user, "password": password}),
        headers=headers,
    )

    if response.status_code == 200:
        loginSuccess = True
    else:
        loginSuccess = False

    return loginSuccess


def get_last_workout(user: str, password: str):
    headers = BASIC_HEADERS.copy()
    session = requests.Session()
    response = session.post(
        "https://api.hevyapp.com/login",
        data=json.dumps({"emailOrUsername": user, "password": password}),
        headers=headers,
    )
    if response.status_code == 200:
        json_content = response.json()
        session.headers.update({"auth-token": json_content["auth_token"]})

        response = session.get("https://api.hevyapp.com/account", headers=headers)

        return datetime.strptime(json.loads(response.text)["last_workout_at"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d-%m-%Y %H:%M:%S")
    else:
        return "Too many API requests, please wait"


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(
    name="help",
    description="Help command",
    guild=discord.Object(id=guild)
)
async def help_command(interaction):
    await interaction.response.send_message('Login to Hevy using `/login <username> <password>`\nYour details are private and only you can see them\nYour password is encrypted\nThis will start the *encouragement*', ephemeral=True)


@tree.command(
    name="login",
    description="Log's into your hevy account (only you can see)",
    guild=discord.Object(id=guild)
)
async def login_command(interaction, username:str, password:str):
    if hevy_login(username, password):
        if credential_handler.add_user(interaction.user.id, username, password_handler.encrypt_password(password), frequency=7):
            await interaction.response.send_message("You have successfully logged in to Hevy", ephemeral=True)
        else:
            await interaction.response.send_message("You are already logged in to Hevy", ephemeral=True)
    else:
        await interaction.response.send_message("login failed, incorrect username or password", ephemeral=True)


@tree.command(
    name="last-workout",
    description="Gets the last time you've worked out",
    guild=discord.Object(id=guild)
)
async def last_workout_command(interaction):
    creds = credential_handler.load_credentials()
    if str(interaction.user.id) in creds:
        last_workout_time = get_last_workout(creds[str(interaction.user.id)]["username"], password_handler.decrypt_password(creds[str(interaction.user.id)]["password"]))
        await interaction.response.send_message(f"Your last work out was {last_workout_time}")
    else:
        await interaction.response.send_message("You are not logged in to Hevy, please log in using `/login <username> <password>`", ephemeral=True)


@tree.command(
    name="all-last-workouts",
    description="Gets the last time everyone's worked out",
    guild=discord.Object(id=guild)
)
async def all_last_workouts_command(interaction):
    creds = credential_handler.load_credentials()
    last_workout_array = ""
    if str(interaction.user.id) in creds:
        for cred in creds:
            last_workout_array += f'{creds[str(cred)]["username"]}: {get_last_workout(creds[str(cred)]["username"], password_handler.decrypt_password(creds[str(cred)]["password"]))}\n'
        await interaction.response.send_message(f"Everyone's last workout:\n{last_workout_array}")
    else:
        await interaction.response.send_message("You are not logged in to Hevy, please log in using `/login <username> <password>`", ephemeral=True)


@tree.command(
    name="gym-frequency",
    description="Sets the amount to time before you are reminded to go to the gym (frequency in days)",
    guild=discord.Object(id=guild)
)
async def gym_frequency_command(interaction, frequency:int):
    if 0 < frequency < 14:
        if credential_handler.update_frequency(interaction.user.id, frequency):
            await interaction.response.send_message(f"You will now be reminded every {frequency} days")
        else:
            await interaction.response.send_message("You are not logged in to Hevy, please log in using `/login <username> <password>`", ephemeral=True)
    elif frequency <= 0:
        await interaction.response.send_message("Please enter a number larger than 0")
    elif frequency >= 14:
        await interaction.response.send_message("Please enter a number smaller than 14 and stop being so lazy")


@tasks.loop(hours=1)
async def gym_reminder():
    creds = credential_handler.load_credentials()
    now = datetime.now()
    for cred in creds:
        checked = False
        while not checked:
            last_workout_time = get_last_workout(creds[str(cred)]["username"], password_handler.decrypt_password(creds[str(cred)]["password"]))
            if last_workout_time != "Too many API requests, please wait":
                checked = True
                formatted_time = datetime.strptime(last_workout_time, "%d-%m-%Y %H:%M:%S")
                frequency = int(creds[str(cred)]["frequency"])
                time_updated = creds[str(cred)]["time_updated"]
                if time_updated is not None:
                    time_updated = datetime.strptime(time_updated, "%Y-%m-%d %H:%M:%S.%f")
                if now >= formatted_time + timedelta(days=frequency):
                    if time_updated is None or now - time_updated > timedelta(days=1):
                        credential_handler.update_time_updated(int(cred), str(now))
                        time_since = now - formatted_time
                        hours, remainder = divmod(time_since.seconds, 3600)
                        minutes = int(remainder / 60)
                        await client.get_channel(channel).send(f"<@{int(cred)}>\nYou haven't been to the gym in {time_since.days} days, {hours:02d} hours and {minutes:02d} minutes\nStop being lazy and go gym")
            else:
                await asyncio.sleep(30)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=guild))
    await client.change_presence(activity=discord.Game("Heavy ass weights"))
    # await tree.sync()
    gym_reminder.start()
    print(f'Logged in as {client.user.name}')


client.run(open(f"{os.path.dirname(__file__)}/token.txt", "r").read())
