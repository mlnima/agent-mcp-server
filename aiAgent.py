from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
import uvicorn
import json
import re
import base64

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


class AdvancedAgent:
    def __init__(self):
        self.ollama = OllamaClient()
        self.resources = {
            "file://sample.txt": "This is a sample text file content.",
            "file://data.json": '{"name": "test", "value": 42}',
            "file://info.md": "# Sample Markdown\n\nThis is **bold** text."
        }
        self.tools = {
            "calculate": self.calculate,
            "get_weather": self.get_weather,
            "create_image": self.create_image,
            "embed_resource": self.embed_resource,
            "read_resource": self.read_resource
        }

    def sanitize_output(self, text: str):
        patterns = [
            r"RESULT:\s*(.+)",
            r"WEATHER:\s*(.+)",
            r"RESOURCE:\s*(.+)",
            r"ERROR:\s*(.+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        lines = text.strip().split('\n')
        return lines[-1] if lines else text

    def calculate(self, expression: str):
        try:
            result = eval(expression)
            return f"RESULT: {result}"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def get_weather(self, city: str):
        return f"WEATHER: {city} - Sunny, 22°C"

    def create_image(self, color: str, size: int = 100):
        svg_data = f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
            <rect width="{size}" height="{size}" fill="{color}"/>
            <text x="50%" y="50%" text-anchor="middle" fill="white" font-size="14">{color}</text>
        </svg>'''

        encoded = base64.b64encode(svg_data.encode()).decode()
        return f"IMAGE: data:image/svg+xml;base64,{encoded}"

    def embed_resource(self, resource_uri: str):
        if resource_uri in self.resources:
            content = self.resources[resource_uri]
            return f"RESOURCE: {resource_uri} - {content[:100]}..."
        return f"ERROR: Resource not found: {resource_uri}"

    def read_resource(self, resource_uri: str):
        if resource_uri in self.resources:
            return f"RESOURCE: {self.resources[resource_uri]}"
        return f"ERROR: Resource not found: {resource_uri}"

    def process_request(self, message: str, sanitize: bool = True):
        tool_descriptions = """Available tools and resources:
TOOLS:
- calculate(expression): Math calculations
- get_weather(city): Weather info
- create_image(color, size): Generate colored image
- embed_resource(uri): Embed resource content
- read_resource(uri): Read resource content

RESOURCES:
- file://sample.txt: Sample text file
- file://data.json: JSON data
- file://info.md: Markdown document

To use a tool, respond with: USE_TOOL:tool_name:arguments
Example: USE_TOOL:calculate:15*7+3
Example: USE_TOOL:get_weather:Paris
Example: USE_TOOL:read_resource:file://sample.txt

User: {message}"""

        system_prompt = tool_descriptions.format(message=message)
        response = self.ollama.generate(system_prompt)

        if "USE_TOOL:" in response:
            try:
                tool_line = [line for line in response.split('\n') if 'USE_TOOL:' in line][0]
                parts = tool_line.split(':', 2)
                if len(parts) >= 3:
                    tool_name = parts[1].strip()
                    args = parts[2].strip()

                    if tool_name in self.tools:
                        if tool_name == "create_image":
                            color_size = args.split(',')
                            color = color_size[0].strip()
                            size = int(color_size[1].strip()) if len(color_size) > 1 else 100
                            result = self.tools[tool_name](color, size)
                        else:
                            result = self.tools[tool_name](args)

                        return self.sanitize_output(result) if sanitize else result
            except Exception as e:
                return f"Tool execution error: {str(e)}"

        return self.sanitize_output(response) if sanitize else response


agent = AdvancedAgent()


@app.post("/chat")
async def chat(request: AgentRequest):
    try:
        response = agent.process_request(request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/raw")
async def chat_raw(request: AgentRequest):
    try:
        response = agent.process_request(request.message, sanitize=False)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {"name": "calculate", "description": "Perform mathematical calculations"},
            {"name": "get_weather", "description": "Get weather information"},
            {"name": "create_image", "description": "Create colored SVG image"},
            {"name": "embed_resource", "description": "Embed resource content"},
            {"name": "read_resource", "description": "Read resource content"}
        ]
    }


@app.get("/resources")
async def list_resources():
    return {
        "resources": [
            {"uri": "file://sample.txt", "name": "Sample Text", "type": "text/plain"},
            {"uri": "file://data.json", "name": "JSON Data", "type": "application/json"},
            {"uri": "file://info.md", "name": "Markdown", "type": "text/markdown"}
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)