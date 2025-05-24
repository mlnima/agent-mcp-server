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
        print("=== Testing Secure File System Agent ===\n")

        print("1. Testing /tools endpoint...")
        response = requests.get(f"{base_url}/tools")
        print(f"Tools: {response.json()}\n")

        print("2. Testing /workspace endpoint...")
        response = requests.get(f"{base_url}/workspace")
        print(f"Workspace: {response.json()}\n")

        print("3. Creating test project directory...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Create a directory called project1"
        })
        print(f"Create dir: {response.json()['response']}\n")

        print("4. Writing test file...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Write a file project1/readme.txt with content: This is a test file for project1"
        })
        print(f"Write file: {response.json()['response']}\n")

        print("5. Reading the file...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Read the file project1/readme.txt"
        })
        print(f"Read file: {response.json()['response']}\n")

        print("6. Listing directory contents...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "List contents of project1 directory"
        })
        print(f"List dir: {response.json()['response']}\n")

        print("7. Testing security - trying to access parent directory...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Read file ../ai-agent.py"
        })
        print(f"Security test: {response.json()['response']}\n")

        print("8. Testing calculation...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Calculate 25 * 4 + 15"
        })
        print(f"Calculation: {response.json()['response']}\n")

        print("9. Deleting test file...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Delete the file project1/readme.txt"
        })
        print(f"Delete file: {response.json()['response']}")

    except Exception as e:
        print(f"Test error: {e}")
    finally:
        agent_process.terminate()
        agent_process.wait()
        print("\n=== Test completed ===")


if __name__ == "__main__":
    test_agent()