import asyncio
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
import mcp.types as types
import base64
from dotenv import load_dotenv

load_dotenv()

server = Server("advanced-tools")

SAMPLE_FILES = {
    "sample.txt": "This is a sample text file content.",
    "data.json": '{"name": "test", "value": 42}',
    "info.md": "# Sample Markdown\n\nThis is **bold** text."
}


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="file://sample.txt",
            name="Sample Text File",
            description="A sample text file",
            mimeType="text/plain"
        ),
        types.Resource(
            uri="file://data.json",
            name="Sample JSON Data",
            description="Sample JSON configuration",
            mimeType="application/json"
        ),
        types.Resource(
            uri="file://info.md",
            name="Sample Markdown",
            description="Sample markdown document",
            mimeType="text/markdown"
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    filename = uri.replace("file://", "")
    if filename in SAMPLE_FILES:
        return SAMPLE_FILES[filename]
    raise ValueError(f"Resource not found: {uri}")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="calculate",
            description="Perform mathematical calculations",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Mathematical expression"}
                },
                "required": ["expression"]
            }
        ),
        types.Tool(
            name="get_weather",
            description="Get weather information",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"]
            }
        ),
        types.Tool(
            name="create_image",
            description="Create a simple colored image",
            inputSchema={
                "type": "object",
                "properties": {
                    "color": {"type": "string", "description": "Color name (red, blue, green)"},
                    "size": {"type": "integer", "description": "Image size in pixels", "default": 100}
                },
                "required": ["color"]
            }
        ),
        types.Tool(
            name="embed_resource",
            description="Embed a resource file",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_uri": {"type": "string", "description": "Resource URI to embed"}
                },
                "required": ["resource_uri"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
        name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "calculate":
        if not arguments or "expression" not in arguments:
            raise ValueError("Missing expression")

        try:
            result = eval(arguments["expression"])
            return [types.TextContent(type="text", text=f"RESULT: {result}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"ERROR: {str(e)}")]

    elif name == "get_weather":
        if not arguments or "city" not in arguments:
            raise ValueError("Missing city")

        city = arguments["city"]
        return [types.TextContent(type="text", text=f"WEATHER: {city} - Sunny, 22°C")]

    elif name == "create_image":
        if not arguments or "color" not in arguments:
            raise ValueError("Missing color")

        color = arguments["color"]
        size = arguments.get("size", 100)

        svg_data = f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
            <rect width="{size}" height="{size}" fill="{color}"/>
            <text x="50%" y="50%" text-anchor="middle" fill="white" font-size="14">{color}</text>
        </svg>'''

        return [types.ImageContent(
            type="image",
            data=base64.b64encode(svg_data.encode()).decode(),
            mimeType="image/svg+xml"
        )]

    elif name == "embed_resource":
        if not arguments or "resource_uri" not in arguments:
            raise ValueError("Missing resource_uri")

        uri = arguments["resource_uri"]
        try:
            content = await handle_read_resource(uri)
            return [types.EmbeddedResource(
                type="resource",
                resource=types.Resource(
                    uri=uri,
                    name=f"Embedded {uri}",
                    mimeType="text/plain"
                ),
                text=content
            )]
        except Exception as e:
            return [types.TextContent(type="text", text=f"ERROR: {str(e)}")]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="advanced-tools",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())