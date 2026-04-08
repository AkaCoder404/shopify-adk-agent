"""Shopify Operations Agent - Handles Shopify API operations via MCP tools."""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
import mcp.client.stdio

load_dotenv()

SHOPIFY_DOMAIN = os.getenv("SHOPIFY_SHOP")
SHOPIFY_CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID")
SHOPIFY_CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET")


# Shopify Dev MCP - Answers questions about Shopify APIs
dev_mcp_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=mcp.client.stdio.StdioServerParameters(
            command="npx", args=["-y", "@shopify/dev-mcp@latest"]
        )
    )
)

# Shopify Store MCP - Performs CRUD operations
store_mcp_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=mcp.client.stdio.StdioServerParameters(
            command="npx",
            args=[
                "shopify-mcp",
                "--clientId",
                SHOPIFY_CLIENT_ID,
                "--clientSecret",
                SHOPIFY_CLIENT_SECRET,
                "--domain",
                SHOPIFY_DOMAIN,
            ],
            env=os.environ.copy(),
        )
    )
)


shopify_operations_agent = Agent(
    name="shopify_operations",
    model="gemini-2.5-flash",
    description="Handles all Shopify store operations including products, customers, and orders via MCP tools.",
    instruction="""
You are a Shopify Operations specialist. You handle all Shopify store operations.

You have access to two MCP toolsets:
1. `@shopify/dev-mcp`: Use this to answer questions about Shopify development, 
   look up API schemas, and find best practices.
2. `shopify-mcp`: Use this to perform CRUD operations on Shopify store data 
   like products, customers, and orders.

When managing products:
- Always set new products as DRAFT unless explicitly told otherwise
- Use appropriate error handling for API calls
- Return clear summaries of actions taken

When asked about Shopify APIs or development, use the dev-mcp tools.
When performing store operations, use the shopify-mcp tools.
""",
    tools=[dev_mcp_tools, store_mcp_tools],
)
