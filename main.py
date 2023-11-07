import requests
import json
import os

# Function to get the API URL from environment variables
def get_api_url():
    return os.getenv('API_URL')

# Function to make a GraphQL query
def query_graphql(url, headers, payload):
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        return response.json()
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Oops: Something Else", err)

# Function to check housing availability
def check_availability(response_data):
    if response_data["data"]["housings"]["housingRentalObjects"]:
        return "HOUSING_RENTAL_OBJECTS_AVAILABLE"
    else:
        return "NO_HOUSING_RENTAL_OBJECTS_AVAILABLE"

# Function to print housing availability details
def print_availability_details(response_data):
    available_apartments = response_data["data"]["housings"]["housingRentalObjects"]
    if available_apartments:
        print("Available apartments:")
        for apartment in available_apartments:
            if apartment['isAvailable']:
                print(f"ID: {apartment['rentalObjectId']}, "
                      f"Available From: {apartment['availableFrom']}, "
                      f"Available To: {apartment['availableTo']}")
    else:
        print("No available housing rental objects at the moment.")

# Function to send notifications (stubbed)
def send_notification(message):
    discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')  # Make sure to set this in your environment variables
    data = {
        "content": message,
        "username": "Housing Bot"
    }
    try:
        response = requests.post(discord_webhook_url, json=data)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"Failed to send Discord notification: {err}")


# Main logic
if __name__ == "__main__":
    url = get_api_url()
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    payload = {
        "operationName": "GetHousingIds",
        "query": """
        query GetHousingIds($input: GetHousingsInput!) {
          housings(filter: $input) {
            housingRentalObjects {
              rentalObjectId
              isAvailable
              availableFrom
              availableTo
              hasActiveReservation
              __typename
            }
            filterCounts {
              locations {
                key
                value
                __typename
              }
              residenceCategories {
                key
                value
                __typename
              }
              categories {
                key
                value
                __typename
              }
              notAvailableCount
              __typename
            }
            totalCount
            __typename
          }
        }
        """,
        "variables": {
            "input": {
                "location": [{"parent": "Trondheim", "children": []}],
                "availableMaxDate": "2024-01-07T00:00:00.000Z",
                "includeFilterCounts": True,
                "offset": 0,
                "pageSize": 10,
                "residenceCategories": ["1-roms", "2-roms"],
                "showUnavailable": False
            }
        }
    }

    # Make the query
    data = query_graphql(url, headers, payload)

    # Check and act on availability
    if data:
        status = check_availability(data)
        print(status)
        print_availability_details(data)

        # If apartments are available, send a notification
        if status == "HOUSING_RENTAL_OBJECTS_AVAILABLE":
            send_notification("New housing rental objects are available.")
