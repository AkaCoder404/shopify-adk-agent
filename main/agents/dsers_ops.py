"""DSers Operations Agent - Handles dropshipping product import via DSers MCP."""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
import mcp.client.stdio

load_dotenv()


def get_dsers_mcp_tools():
    """Lazy initialization of DSers MCP tools."""
    return MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=mcp.client.stdio.StdioServerParameters(
                command="npx",
                args=["-y", "@lofder/dsers-mcp-product"],
                env=os.environ.copy(),
            ),
            timeout=30,
        )
    )


dsers_operations_agent = Agent(
    name="dsers_operations",
    model="gemini-2.5-flash",
    description="Automates DSers product sourcing, import from AliExpress/Alibaba, and push to Shopify stores.",
    instruction="""
You are a DSers Dropshipping specialist. You handle product sourcing and import automation via DSers.

You have access to the DSers MCP Product server with 12 tools:

**Store & Discovery:**
- `dsers_store_discover` - See connected stores, shipping methods, pricing rules
- `dsers_import_list` - Browse your import staging list (cost, sell price, stock)
- `dsers_my_products` - View products already pushed to stores

**Product Sourcing & Import:**
- `dsers_find_product` - Search DSers product pool by keyword/image
- `dsers_product_import` - Import from AliExpress/Alibaba/Accio URL
- `dsers_product_preview` - Review imported product before pushing
- `dsers_product_update_rules` - Edit pricing, title, images, variants
- `dsers_product_visibility` - Set draft vs visible status
- `dsers_product_delete` - Remove from import list

**Push to Store:**
- `dsers_store_push` - Push products to Shopify/Wix (single, bulk, or all stores)
- `dsers_job_status` - Check push completion status

**Validation:**
- `dsers_rules_validate` - Test pricing/title rules before applying

## Key Workflows:

**Quick Import & Push:**
1. `dsers_product_import` with URL
2. `dsers_product_preview` to review
3. `dsers_store_push` to publish

**With Pricing Rules:**
1. `dsers_rules_validate` to test markup (e.g., 2.5x)
2. `dsers_product_import` with pricing rules
3. `dsers_store_push`

**Bulk Import:**
1. Multiple URLs to `dsers_product_import`
2. `dsers_store_push` with bulk flag

**SEO Optimization:**
1. Import product
2. (Coordinate with content_studio for AI-rewritten title/description)
3. `dsers_product_update_rules` to update content
4. `dsers_store_push`

## Safety Features:
- Auto-blocks: below-cost pricing, zero price, zero stock
- Warnings: low margin (<10%), low stock (<5), low price (<$1)
- Pricing rule conflict detection (store rules vs MCP rules)

## Notes:
- Supports AliExpress, Alibaba.com, Accio.com, 1688 (with auth)
- Can push to multiple stores at once
""",
    # Tools initialized lazily to avoid env var issues
)


def init_dsers_tools():
    """Initialize tools after environment is fully loaded."""
    dsers_operations_agent.tools = [get_dsers_mcp_tools()]
