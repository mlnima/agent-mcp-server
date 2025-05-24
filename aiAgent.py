from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
import uvicorn
import json

load_dotenv()

app = FastAPI()


class AgentRequest(BaseModel):
    message: str


class OllamaClient:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen3:30b-a3b")

    def generate(self, prompt: str):
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            return response.json()["response"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")


class SimpleAgent:
    def __init__(self):
        self.ollama = OllamaClient()
        self.tools = {
            "calculate": self.calculate,
            "get_weather": self.get_weather
        }

    def calculate(self, expression: str):
        try:
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"

    def get_weather(self, city: str):
        return f"Weather in {city}: Sunny, 22°C"

    def process_request(self, message: str):
        tool_descriptions = """Available tools:
- calculate: Perform mathematical calculations (use format: calculate(expression))
- get_weather: Get weather for a city (use format: get_weather(city))

If you need to use a tool, respond with exactly: TOOL:tool_name:arguments
Otherwise respond normally."""

        system_prompt = f"{tool_descriptions}\n\nUser: {message}"
        response = self.ollama.generate(system_prompt)

        if response.startswith("TOOL:"):
            parts = response.split(":", 2)
            if len(parts) == 3:
                tool_name = parts[1]
                args = parts[2]
                if tool_name in self.tools:
                    return self.tools[tool_name](args)

        return response


agent = SimpleAgent()


@app.post("/chat")
async def chat(request: AgentRequest):
    try:
        response = agent.process_request(request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {"name": "calculate", "description": "Perform mathematical calculations"},
            {"name": "get_weather", "description": "Get weather information for a city"}
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)