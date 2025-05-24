from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
import uvicorn
import json
import re
import base64
import pathlib
import shutil

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


class SecureFileManager:
    def __init__(self):
        self.workspace_root = pathlib.Path("workspace").resolve()
        self.workspace_root.mkdir(exist_ok=True)

    def _validate_path(self, path_str: str):
        try:
            path = pathlib.Path(path_str)
            if path.is_absolute():
                raise ValueError("Absolute paths not allowed")

            full_path = (self.workspace_root / path).resolve()

            if not str(full_path).startswith(str(self.workspace_root)):
                raise ValueError("Path outside workspace")

            return full_path
        except Exception as e:
            raise ValueError(f"Invalid path: {e}")

    def read_file(self, path_str: str):
        path = self._validate_path(path_str)
        if not path.exists():
            return f"ERROR: File not found: {path_str}"
        if not path.is_file():
            return f"ERROR: Not a file: {path_str}"
        try:
            content = path.read_text(encoding='utf-8')
            return f"CONTENT: {content}"
        except Exception as e:
            return f"ERROR: {e}"

    def write_file(self, path_str: str, content: str):
        path = self._validate_path(path_str)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            return f"SUCCESS: Written to {path_str}"
        except Exception as e:
            return f"ERROR: {e}"

    def delete_file(self, path_str: str):
        path = self._validate_path(path_str)
        if not path.exists():
            return f"ERROR: File not found: {path_str}"
        try:
            if path.is_file():
                path.unlink()
                return f"SUCCESS: Deleted file {path_str}"
            elif path.is_dir():
                shutil.rmtree(path)
                return f"SUCCESS: Deleted directory {path_str}"
        except Exception as e:
            return f"ERROR: {e}"

    def list_directory(self, path_str: str = "."):
        path = self._validate_path(path_str)
        if not path.exists():
            return f"ERROR: Directory not found: {path_str}"
        if not path.is_dir():
            return f"ERROR: Not a directory: {path_str}"
        try:
            items = []
            for item in path.iterdir():
                item_type = "DIR" if item.is_dir() else "FILE"
                rel_path = item.relative_to(self.workspace_root)
                items.append(f"{item_type}: {rel_path}")
            return f"LISTING: {chr(10).join(items)}"
        except Exception as e:
            return f"ERROR: {e}"

    def create_directory(self, path_str: str):
        path = self._validate_path(path_str)
        try:
            path.mkdir(parents=True, exist_ok=True)
            return f"SUCCESS: Created directory {path_str}"
        except Exception as e:
            return f"ERROR: {e}"


class AdvancedAgent:
    def __init__(self):
        self.ollama = OllamaClient()
        self.file_manager = SecureFileManager()
        self.tools = {
            "calculate": self.calculate,
            "get_weather": self.get_weather,
            "create_image": self.create_image,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "delete_file": self.delete_file,
            "list_directory": self.list_directory,
            "create_directory": self.create_directory
        }

    def sanitize_output(self, text: str):
        patterns = [
            r"RESULT:\s*(.+)",
            r"WEATHER:\s*(.+)",
            r"CONTENT:\s*(.+)",
            r"SUCCESS:\s*(.+)",
            r"LISTING:\s*(.+)",
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

    def read_file(self, path: str):
        return self.file_manager.read_file(path)

    def write_file(self, path_and_content: str):
        parts = path_and_content.split('|', 1)
        if len(parts) != 2:
            return "ERROR: Use format: path|content"
        return self.file_manager.write_file(parts[0].strip(), parts[1])

    def delete_file(self, path: str):
        return self.file_manager.delete_file(path)

    def list_directory(self, path: str = "."):
        return self.file_manager.list_directory(path)

    def create_directory(self, path: str):
        return self.file_manager.create_directory(path)

    def process_request(self, message: str, sanitize: bool = True):
        tool_descriptions = """Available tools (workspace directory only):
FILE OPERATIONS:
- read_file(path): Read file content
- write_file(path|content): Write content to file 
- delete_file(path): Delete file or directory
- list_directory(path): List directory contents
- create_directory(path): Create directory

OTHER TOOLS:
- calculate(expression): Math calculations
- get_weather(city): Weather info
- create_image(color,size): Generate colored image

SECURITY: Only workspace/ directory accessible. No parent/sibling access.

To use: USE_TOOL:tool_name:arguments
Examples:
USE_TOOL:read_file:project1/readme.txt
USE_TOOL:write_file:project1/test.txt|Hello World
USE_TOOL:list_directory:project1
USE_TOOL:create_directory:project1/subfolder

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
            {"name": "read_file", "description": "Read file from workspace"},
            {"name": "write_file", "description": "Write file to workspace (path|content)"},
            {"name": "delete_file", "description": "Delete file/directory from workspace"},
            {"name": "list_directory", "description": "List directory contents"},
            {"name": "create_directory", "description": "Create directory in workspace"},
            {"name": "calculate", "description": "Mathematical calculations"},
            {"name": "get_weather", "description": "Get weather information"},
            {"name": "create_image", "description": "Create colored SVG image"}
        ]
    }


@app.get("/workspace")
async def list_workspace():
    try:
        result = agent.file_manager.list_directory(".")
        return {"workspace": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)