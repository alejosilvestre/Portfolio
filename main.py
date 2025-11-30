import json
from dotenv import load_dotenv

load_dotenv(override=True)

import agente1


def load_restaurants(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    restaurants = []
    for place in data.get("local_results", []):
        restaurant = {
            "name": place.get("title"),
            "address": place.get("address"),
            "rating": place.get("rating"),
            "reviews": place.get("reviews"),
            "food": place.get("type"),
            "price_level": place.get("price"),
        }
        restaurants.append(restaurant)

    return restaurants


if __name__ == "__main__":
    restaurants = load_restaurants("restaurants.json")

    user_request = "Consígueme una reserva para las 9 en un restaurante mexicano en Madrid con buena puntuación"

    # Llamamos a la función `main` exportada por el módulo
    agente1.choose_restaurant(restaurants, user_request)
