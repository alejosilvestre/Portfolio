import json


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
    for restaurant in restaurants:
        print(restaurant)
