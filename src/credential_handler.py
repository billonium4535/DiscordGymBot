import json
import os

json_file = f'{os.path.dirname(__file__)}/user_credentials.json'


def load_credentials():
    """
    Load existing credentials from the JSON file.
    Returns:
        credentials (dict): Dictionary of user credentials.
    """
    if os.path.exists(json_file):
        with open(json_file, 'r') as file:
            return json.load(file)
    return {}


def save_credentials(credentials):
    """
    Save the updated credentials to the JSON file.
    Returns:
        None
    """
    with open(json_file, 'w') as file:
        json.dump(credentials, file, indent=4)


def add_user(discord_id, username, password, frequency):
    """
    Add a new user with the given username and password.
    Args:
        discord_id (int): The discord id linked to the account.
        username (str): The username to add.
        password (str): The password to add.
        frequency (int): The frequency to remind.
    Returns:
        bool: True if the user was successfully added.
    """
    credentials = load_credentials()
    if str(discord_id) in credentials:
        userAdded = False
    else:
        credentials[discord_id] = {
            "username": username,
            "password": password,
            "frequency": frequency,
            "time_updated": None
        }
        save_credentials(credentials)
        userAdded = True
    return userAdded


def update_time_updated(discord_id, time_updated):
    """
    Updates the frequency of the user.
    Args:
        discord_id (int): The discord id linked to the account.
        time_updated (int): The times to update.
    Returns:
        bool: True if the user was successfully updated.
    """
    credentials = load_credentials()
    if str(discord_id) not in credentials:
        userUpdated = False
    else:
        userUpdated = True
        credentials[str(discord_id)]["time_updated"] = time_updated
        save_credentials(credentials)

    return userUpdated


def update_frequency(discord_id, frequency):
    """
    Updates the frequency of the user.
    Args:
        discord_id (int): The discord id linked to the account.
        frequency (int): The frequency to remind.
    Returns:
        bool: True if the user was successfully updated.
    """
    credentials = load_credentials()
    if str(discord_id) not in credentials:
        userUpdated = False
    else:
        userUpdated = True
        credentials[str(discord_id)]["frequency"] = frequency
        save_credentials(credentials)

    return userUpdated
