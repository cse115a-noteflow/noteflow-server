import requests

# Base URL for your Flask server
base_url = "http://127.0.0.1:5000/note"  # Update this to match your Flask route prefix

# Define the JSON data for the note
note_data = {
    "id": "note_123456",
    "title": "Notes",
    "description": "Notes.",
    "content": [
        {
            "type": "text",
            "id": "block_001",
            "position": None,
            "value": "Testing flask routing.",
            "style": {
                "formatting": [
                    {
                        "start": 0,
                        "end": 9,
                        "color": "#FF0000",
                        "highlight": "#FFFF00",
                        "link": None,
                        "types": ["bold"]
                    }
                ],
                "align": "left"
            }
        },
        {
            "type": "text",
            "id": "block_002",
            "position": {
                "x": 100,
                "y": 200,
                "zIndex": 1
            },
            "value": "Hopefully this works.",
            "style": {
                "formatting": [
                    {
                        "start": 9,
                        "end": 23,
                        "color": "#333333",
                        "highlight": None,
                        "link": None,
                        "types": ["italic"]
                    }
                ],
                "align": "center"
            }
        }
    ],
    "owner": {
        "id": "user_67890",
        "name": "Ryan Mee",
        "photo": "https://example.com/profile.jpg",
        "email": "ryan@example.com",
        "usage": {"generations": 42},
        "notes": None
    },
    "permissions": {
        "global": "view",
        "user": {"user_54321": "edit", "user_98765": "view"}
    }
}

# Function to test the /add endpoint


def test_add():
    url = f"{base_url}/add"
    print(f"Testing /add at {url}...")
    try:
        response = requests.post(url, json=note_data)
        print("Response status code:", response.status_code)
        try:
            print("Response JSON:", response.json())
        except requests.exceptions.JSONDecodeError:
            print("Response is not valid JSON:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error sending request to /add: {e}")

# Function to test the /get endpoint


def test_get():
    url = f"{base_url}/get"
    payload = {"id": note_data["id"]}  # Send ID in JSON body
    print(f"Testing /get at {url} with id={note_data['id']}...")
    try:
        response = requests.post(url, json=payload)  # Use POST with JSON payload
        print("Response status code:", response.status_code)
        try:
            print("Response JSON:", response.json())
        except requests.exceptions.JSONDecodeError:
            print("Response is not valid JSON:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error sending request to /get: {e}")

# Function to test the /remove endpoint


def test_remove():
    url = f"{base_url}/remove"
    payload = {"id": note_data["id"]}  # Send ID in JSON body
    print(f"Testing /remove at {url} with id={note_data['id']}...")
    try:
        response = requests.post(url, json=payload)
        print("Response status code:", response.status_code)
        try:
            print("Response JSON:", response.json())
        except requests.exceptions.JSONDecodeError:
            print("Response is not valid JSON:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error sending request to /remove: {e}")


if __name__ == "__main__":
    print("\n--- Testing Flask Endpoints ---\n")
    print("Choose an endpoint to test:")
    print("1. Add (/add)")
    print("2. Get (/get)")
    print("3. Remove (/remove)")

    choice = input("Enter the number of the test to run (1/2/3): ").strip()

    if choice == "1":
        test_add()
    elif choice == "2":
        test_get()
    elif choice == "3":
        test_remove()
    else:
        print("Invalid choice. Please enter 1, 2, or 3.")
