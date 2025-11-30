# test_stdio_client.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_stdio_client():
    # Configuration du serveur stdio
    server_params = StdioServerParameters(
        command="python", 
        args=["basketcoach_mcp_server.py", "stdio"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialise la connexion
            await session.initialize()

            # Liste les outils
            tools = await session.list_tools()
            print("Tools:", tools)

            # Appel d'un outil
            result = await session.call_tool("get_nba_live_ranking", {})
            print("Result:", result)

if __name__ == "__main__":
    asyncio.run(test_stdio_client())