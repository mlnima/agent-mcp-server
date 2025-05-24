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
        print("=== Testing MCP Agent with All Features ===\n")

        print("1. Testing /tools endpoint...")
        response = requests.get(f"{base_url}/tools")
        print(f"Tools: {response.json()}\n")

        print("2. Testing /resources endpoint...")
        response = requests.get(f"{base_url}/resources")
        print(f"Resources: {response.json()}\n")

        print("3. Testing TextContent - Math calculation...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Calculate 25 * 4 + 15"
        })
        print(f"Calculation (sanitized): {response.json()['response']}")

        response = requests.post(f"{base_url}/chat/raw", json={
            "message": "Use calculate tool for 25 * 4 + 15"
        })
        print(f"Calculation (raw): {response.json()['response']}\n")

        print("4. Testing TextContent - Weather...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Get weather for Tokyo"
        })
        print(f"Weather (sanitized): {response.json()['response']}")

        response = requests.post(f"{base_url}/chat/raw", json={
            "message": "Use get_weather tool for Tokyo"
        })
        print(f"Weather (raw): {response.json()['response']}\n")

        print("5. Testing ImageContent - Create image...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Create a red image with size 150"
        })
        print(f"Image creation (sanitized): {response.json()['response'][:100]}...")

        response = requests.post(f"{base_url}/chat/raw", json={
            "message": "Use create_image tool: red, 150"
        })
        print(f"Image creation (raw): {response.json()['response'][:100]}...\n")

        print("6. Testing Resource - Read text file...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Read the sample text file"
        })
        print(f"Read resource (sanitized): {response.json()['response']}")

        response = requests.post(f"{base_url}/chat/raw", json={
            "message": "Use read_resource tool: file://sample.txt"
        })
        print(f"Read resource (raw): {response.json()['response']}\n")

        print("7. Testing EmbeddedResource - Embed JSON...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Embed the JSON data file"
        })
        print(f"Embed resource (sanitized): {response.json()['response']}")

        response = requests.post(f"{base_url}/chat/raw", json={
            "message": "Use embed_resource tool: file://data.json"
        })
        print(f"Embed resource (raw): {response.json()['response']}\n")

        print("8. Testing general conversation...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Hello, what can you do?"
        })
        print(f"General chat: {response.json()['response']}\n")

        print("9. Testing error handling...")
        response = requests.post(f"{base_url}/chat", json={
            "message": "Calculate invalid expression: 5 / 0"
        })
        print(f"Error handling: {response.json()['response']}")

    except Exception as e:
        print(f"Test error: {e}")
    finally:
        agent_process.terminate()
        agent_process.wait()
        print("\n=== Test completed ===")


if __name__ == "__main__":
    test_agent()