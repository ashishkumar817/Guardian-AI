import requests

BASE_URL = "http://127.0.0.1:8000"


class GuardianAPI:

    def __init__(self):
        self.token = None
        self.prev_hip_y = None
        self.prev_time = None

    def login(self, email, password):

        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": email,
                "password": password
            },
            timeout=5
        )

        print("Login Status:", response.status_code)

        if response.status_code != 200:
            print(response.text)
            raise Exception("Login Failed")

        self.token = response.json()["access_token"]

        print("✅ Logged In")

    def create_incident(self, confidence, image_path):

        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        response = requests.post(
            f"{BASE_URL}/incidents/",
            json={
                "confidence": float(confidence),
                "image_path": image_path
            },
            headers=headers,
            timeout=5
        )

        print("Incident Status:", response.status_code)

        try:
            print(response.json())
        except Exception:
            print(response.text)