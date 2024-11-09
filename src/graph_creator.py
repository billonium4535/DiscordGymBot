import json
import os
from datetime import datetime
from typing import List, Tuple
from matplotlib import pyplot as plt
import random


def get_graph_data(json_file, exercise_to_get):
    """
    Returns formatted data for graphing.
    Args:
        json_file (str): The path to the json file.
        exercise_to_get (str): The name of the exercise.
    Returns:
        Tuple[List[datetime], List[int]]: Data for graphing.
    """
    with open(json_file, "r") as f:
        data = json.load(f)
        weight_progress = {}
        for workout in data:
            date_time = datetime.strptime(workout["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
            date_time = date_time.strftime("%d-%m-%Y %H:%M:%S")
            for exercise in workout["exercises"]:
                if exercise["title"] == exercise_to_get:
                    max_weight = 0
                    for weight_set in exercise["sets"]:
                        if weight_set["weight_kg"] > max_weight:
                            max_weight = weight_set["weight_kg"]
                    weight_progress[date_time] = max_weight

    dates = [datetime.strptime(date, '%d-%m-%Y %H:%M:%S') for date in weight_progress.keys()]
    values = list(weight_progress.values())

    return dates, values


def plot_single_graph(exercise_to_plot, dataset, user):
    """
    Plots a single user and exercise on a graph.
    Args:
        exercise_to_plot (str): The name of the exercise.
        dataset (Tuple[List[datetime], List[int]]): Data for graphing.
        user (str): The name of the user.
    Returns:
        None
    """
    plt.figure(figsize=(14, 8))
    plt.plot(dataset[0], dataset[1], marker='.', linestyle='-', color='b', label=user)
    plt.xlabel("Date")
    plt.ylabel("Weight (kg)")
    plt.title(exercise_to_plot)
    plt.tight_layout()
    plt.savefig(f"{os.path.dirname(__file__)}/Graphs/{user}.png")
    plt.close()


def plot_multiple_graph(exercise_to_plot, *args):
    """
    Plots users and an exercise on a graph.
    Args:
        exercise_to_plot (str): The name of the exercise.
        args: Datasets and users to plot.
    Returns:
        None
    """
    if len(args) % 2 != 0:
        raise ValueError("Number of datasets does not match the number of users.")

    datasets = []
    users = []

    for arg in args:
        if isinstance(arg, tuple):
            datasets.append(arg)
        elif isinstance(arg, str):
            users.append(arg)

    plt.figure(figsize=(14, 8))

    for i, dataset in enumerate(datasets):
        color = ()
        first_three_chars = users[i][:3]
        for char in first_three_chars:
            char = char.upper()
            color = color + ((ord(char) - ord('A')) / (ord('Z') - ord('A')),)
        plt.plot(dataset[0], dataset[1], marker='.', linestyle='-', color=color, label=users[i])

    plt.xlabel("Date")
    plt.ylabel("Weight (kg)")
    plt.title(exercise_to_plot)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{os.path.dirname(__file__)}/Graphs/users.png")
    plt.close()
