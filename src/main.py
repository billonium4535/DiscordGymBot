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
import graph_creator
from typing import List

BASIC_HEADERS = {
    "x-api-key": "with_great_power",
    "Content-Type": "application/json",
    "accept-encoding": "gzip",
}

guild = int(open(f"{os.path.dirname(__file__)}/guild.txt", "r").read())
channel = int(open(f"{os.path.dirname(__file__)}/channel.txt", "r").read())
VALID_EXERCISES = [item.strip() for item in open(f"{os.path.dirname(__file__)}/valid_exercises.txt", "r").read().split(", ")]


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


def get_workouts_batch(user: str, password: str):
    all_workouts = []

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

        response = session.get("https://api.hevyapp.com/workouts_batch/0", headers=headers)

        workouts = response.json()

        all_workouts += workouts

        while len(workouts) == 10:
            response = session.get('https://api.hevyapp.com/workouts_batch/' + str(workouts[9]["index"]), headers=headers)
            workouts = response.json()
            formatted_workouts = workouts.copy()
            formatted_workouts.pop(0)
            all_workouts += formatted_workouts

        return all_workouts
    else:
        return "Too many API requests, please wait"


def update_workouts_batch(user: str, password: str, credentials):
    all_workouts = []

    headers = BASIC_HEADERS.copy()
    session = requests.Session()
    response = session.post(
        "https://api.hevyapp.com/login",
        data=json.dumps({"emailOrUsername": user, "password": password}),
        headers=headers,
    )
    if response.status_code == 200:
        try:
            json_content = response.json()
        except json.JSONDecodeError:
            raw_json_workouts = get_workouts_batch(user, password)
            if raw_json_workouts != "Too many API requests, please wait":
                with open(f"{os.path.dirname(__file__)}/Workout_Data/{credentials}.json", "w") as file:
                    json.dump(raw_json_workouts, file, indent=4)
                file.close()

        session.headers.update({"auth-token": json_content["auth_token"]})

        with open(f"{os.path.dirname(__file__)}/Workout_Data/{credentials}.json", "r") as file:
            data = json.load(file)
        file.close()
        all_workouts += data

        last_index = int(data[len(data) - 1]["index"])

        response = session.get(f"https://api.hevyapp.com/workouts_batch/{last_index}", headers=headers)

        workouts = response.json()
        formatted_workouts = workouts.copy()
        formatted_workouts.pop(0)
        all_workouts += formatted_workouts

        while len(workouts) == 10:
            response = session.get('https://api.hevyapp.com/workouts_batch/' + str(workouts[9]["index"]), headers=headers)
            workouts = response.json()
            formatted_workouts = workouts.copy()
            formatted_workouts.pop(0)
            all_workouts += formatted_workouts

        return all_workouts
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
    await interaction.response.defer()
    await interaction.followup.send('Login to Hevy using `/login <username> <password>`\nYour details are private and only you can see them\nYour password is encrypted\nThis will start the *encouragement*', ephemeral=True)


@tree.command(
    name="source-code",
    description="Gets a link to the source code",
    guild=discord.Object(id=guild)
)
async def source_code_command(interaction):
    await interaction.response.defer()
    await interaction.followup.send('**Source Code:**\n<https://github.com/billonium4535/DiscordGymBot>\n\n**Policies:**\n<https://billonium4535.github.io/DiscordGymBot/>', ephemeral=True)


@tree.command(
    name="login",
    description="Log's into your hevy account (only you can see)",
    guild=discord.Object(id=guild)
)
async def login_command(interaction, username: str, password: str):
    await interaction.response.defer()
    if hevy_login(username, password):
        if credential_handler.add_user(interaction.user.id, username, password_handler.encrypt_password(password), frequency=7):
            await interaction.followup.send("You have successfully logged in to Hevy", ephemeral=True)
        else:
            await interaction.followup.send("You are already logged in to Hevy", ephemeral=True)
    else:
        await interaction.followup.send("login failed, incorrect username or password", ephemeral=True)


@tree.command(
    name="last-workout",
    description="Gets the last time you've worked out",
    guild=discord.Object(id=guild)
)
async def last_workout_command(interaction):
    await interaction.response.defer()
    creds = credential_handler.load_credentials()
    if str(interaction.user.id) in creds:
        last_workout_time = get_last_workout(creds[str(interaction.user.id)]["username"], password_handler.decrypt_password(creds[str(interaction.user.id)]["password"]))
        await interaction.followup.send(f"Your last work out was {last_workout_time}")
    else:
        await interaction.followup.send("You are not logged in to Hevy, please log in using `/login <username> <password>`", ephemeral=True)


@tree.command(
    name="all-last-workouts",
    description="Gets the last time everyone's worked out",
    guild=discord.Object(id=guild)
)
async def all_last_workouts_command(interaction):
    await interaction.response.defer()
    creds = credential_handler.load_credentials()
    last_workout_array = ""
    if str(interaction.user.id) in creds:
        for cred in creds:
            last_workout_array += f'{creds[str(cred)]["username"]}: {get_last_workout(creds[str(cred)]["username"], password_handler.decrypt_password(creds[str(cred)]["password"]))}\n'
        await interaction.followup.send(f"Everyone's last workout:\n{last_workout_array}")
    else:
        await interaction.followup.send("You are not logged in to Hevy, please log in using `/login <username> <password>`", ephemeral=True)


@tree.command(
    name="gym-frequency",
    description="Sets the amount to time before you are reminded to go to the gym (frequency in days)",
    guild=discord.Object(id=guild)
)
async def gym_frequency_command(interaction, frequency:int):
    await interaction.response.defer()
    if 0 < frequency < 14:
        if credential_handler.update_frequency(interaction.user.id, frequency):
            await interaction.followup.send(f"You will now be reminded every {frequency} days")
        else:
            await interaction.followup.send("You are not logged in to Hevy, please log in using `/login <username> <password>`", ephemeral=True)
    elif frequency <= 0:
        await interaction.followup.send("Please enter a number larger than 0")
    elif frequency >= 14:
        await interaction.followup.send("Please enter a number smaller than 14 and stop being so lazy")


@tree.command(
    name="exercise-graph",
    description="Gives you a graph of your max weight for an exercise",
    guild=discord.Object(id=guild)
)
async def exercise_graph_command(interaction, exercise: str, all_members: bool):
    await interaction.response.defer()
    if exercise not in VALID_EXERCISES:
        await interaction.followup.send("Please pick a valid exercise", ephemeral=True)
    else:
        if all_members:
            data_list = []
            user_list = []

            for file in os.listdir(f"{os.path.dirname(__file__)}/Workout_Data/"):
                data = graph_creator.get_graph_data(f"{os.path.dirname(__file__)}/Workout_Data/{file}", exercise)
                data_list.append(data)
                converted_name = await client.fetch_user(int(os.path.splitext(file)[0]))
                user_list.append(converted_name.global_name)

            graph_creator.plot_multiple_graph(exercise, *data_list, *user_list)

            await interaction.followup.send(file=discord.File(f"{os.path.dirname(__file__)}/Graphs/users.png"))
        else:
            graph_creator.plot_single_graph(exercise, graph_creator.get_graph_data(f"{os.path.dirname(__file__)}/Workout_Data/{interaction.user.id}.json", exercise), str(interaction.user.id))
            await interaction.followup.send(file=discord.File(f"{os.path.dirname(__file__)}/Graphs/{interaction.user.id}.png"))


@exercise_graph_command.autocomplete('exercise')
async def exercise_graph_autocomplete(interaction, current: str) -> List[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=choice, value=choice)
        for choice in VALID_EXERCISES if current.lower() in choice.lower()
    ]


@tree.command(
    name="max-weight",
    description="Gives you your max weight for an exercise",
    guild=discord.Object(id=guild)
)
async def max_weight_command(interaction, exercise: str, all_members: bool):
    await interaction.response.defer()
    if exercise not in VALID_EXERCISES:
        await interaction.followup.send("Please pick a valid exercise", ephemeral=True)
    else:
        data_list = []
        if all_members:
            user_list = []
            output = ""

            for file in os.listdir(f"{os.path.dirname(__file__)}/Workout_Data/"):
                data = graph_creator.get_graph_data(f"{os.path.dirname(__file__)}/Workout_Data/{file}", exercise)
                data_list.append(data[1])
                converted_name = await client.fetch_user(int(os.path.splitext(file)[0]))
                user_list.append(converted_name.global_name)

            i = 0
            for person in data_list:
                max_weight = 0
                for weight in person:
                    if weight > max_weight:
                        max_weight = weight
                output = output + f"{user_list[i]}: {max_weight}kg\n"
                i = i + 1
            await interaction.followup.send(f"**{exercise} PRs**\n{output}")
        else:
            data = graph_creator.get_graph_data(f"{os.path.dirname(__file__)}/Workout_Data/{interaction.user.id}.json", exercise)
            data_list.append(data[1])
            max_weight = 0
            for weight in data_list[0]:
                if weight > max_weight:
                    max_weight = weight
            await interaction.followup.send(f"Your **{exercise}** PR is:\n{max_weight}kg")


@max_weight_command.autocomplete('exercise')
async def max_weight_autocomplete(interaction, current: str) -> List[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=choice, value=choice)
        for choice in VALID_EXERCISES if current.lower() in choice.lower()
    ]


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
        if os.path.isfile(f"{os.path.dirname(__file__)}/Workout_Data/{cred}.json"):
            raw_json_workouts = update_workouts_batch(creds[str(cred)]["username"], password_handler.decrypt_password(creds[str(cred)]["password"]), cred)
            if raw_json_workouts != "Too many API requests, please wait":
                with open(f"{os.path.dirname(__file__)}/Workout_Data/{cred}.json", "w") as file:
                    json.dump(raw_json_workouts, file, indent=4)
                file.close()
        else:
            raw_json_workouts = get_workouts_batch(creds[str(cred)]["username"], password_handler.decrypt_password(creds[str(cred)]["password"]))
            if raw_json_workouts != "Too many API requests, please wait":
                with open(f"{os.path.dirname(__file__)}/Workout_Data/{cred}.json", "w") as file:
                    json.dump(raw_json_workouts, file, indent=4)
                file.close()


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=guild))
    await client.change_presence(activity=discord.Game("Heavy ass weights"))
    # await tree.sync()
    gym_reminder.start()
    print(f'Logged in as {client.user.name}')


client.run(open(f"{os.path.dirname(__file__)}/token.txt", "r").read())
# client.run(open(f"{os.path.dirname(__file__)}/testing_token.txt", "r").read())
