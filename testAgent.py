import requests
import time
import subprocess
import os
import signal


def start_agent():
    return subprocess.Popen(["python", "ai-agent.py"])


def test_agent():
    base_url = "http://localhost:8000"

    agent_process = start_agent()
    time.sleep(3)

    try:
        print("Testing /tools endpoint...")
        response = requests.get(f"{base_url}/tools")
        print(f"Tools response: {response.json()}")

        print("\nTesting calculation...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Calculate 15 * 7 + 3"
        })
        print(f"Calculation response: {response.json()}")

        print("\nTesting direct calculation...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Use calculate tool: 25 + 17"
        })
        print(f"Direct calculation response: {response.json()}")

        print("\nTesting weather...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "What's the weather in Paris?"
        })
        print(f"Weather response: {response.json()}")

        print("\nTesting general chat...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Hello, how are you?"
        })
        print(f"Chat response: {response.json()}")

    except Exception as e:
        print(f"Test error: {e}")
    finally:
        agent_process.terminate()
        agent_process.wait()


if __name__ == "__main__":
    test_agent()