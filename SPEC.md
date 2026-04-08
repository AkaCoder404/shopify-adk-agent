# SPEC.md

Project Hierarchy, Database

## Project Hierarchy

```
main/
├── __init__.py
├── agent.py                    # Root coordinator agent (entry point)
├── agents/
│   ├── __init__.py
│   ├── shopify_ops.py         # Shopify MCP tools agent
│   ├── dsers_ops.py           # DSers MCP tools agent (AliExpress/Alibaba import)
│   ├── csv_sync.py            # CSV read/write & product mapping agent
│   └── content_studio.py      # AI content generation coordinator
├── tools/
│   ├── __init__.py
│   ├── csv_tools.py           # Sync State CSV utilities
│   ├── pipeline_tools.py      # Product Pipeline CSV utilities
│   ├── image_tools.py         # Image generation & manipulation
│   └── file_storage.py        # Local file storage utilities
└── prompts/
    ├── __init__.py
    ├── content_generation.py  # Prompts for title/description generation
    └── seo_optimization.py    # SEO optimization prompts
```

## Agent Descriptions

### ShopifyOperationsAgent
Direct Shopify API operations via MCP tools.
- **Tools**: `shopify-mcp`, `@shopify/dev-mcp`
- **Use for**: Product CRUD, customer management, orders, direct store operations

### DsersOperationsAgent
Automated product sourcing from AliExpress/Alibaba via DSers.
- **Tools**: `@lofder/dsers-mcp-product` (12 tools)
- **Use for**: Import from AliExpress/Alibaba/Accio, pricing rules, push to store
- **Key Features**:
  - Product sourcing from DSers product pool
  - Import from AliExpress, Alibaba, Accio.com, 1688
  - Pricing rules (markup multiplier, fixed markup, sale prices)
  - Multi-store push (Shopify + Wix)
  - Safety checks (below-cost, zero stock, zero price)

### CsvSyncAgent
Manages two-CSV system: Product Pipeline and Sync State.
- **Pipeline Tools**: `create_pipeline_entry`, `update_pipeline_status`, `get_ready_to_import`, `archive_old_pipelines`
- **Sync State Tools**: `create_sync_entry`, `update_sync_after_push`, `update_content_status`, `get_by_content_status`
- **Use for**: Research tracking, ID mapping, content workflow status

### ContentStudioAgent
Sequential pipeline for AI content generation.
- **Sub-agents**: `TextGenerator` → `ImageGenerator` → `SeoOptimizer`
- **Use for**: Generating titles, descriptions, images, SEO optimization

## Two-CSV System (Simplified Architecture)

With DSers integration, product data lives in DSers (source of truth). The CSVs only track:
1. **Research pipeline** (what to import)
2. **Sync state** (ID mappings and workflow status)

No data duplication. Flexible variant mapping.

### Directory Structure

```
workspace/csv/
├── pipeline/              # Product Pipeline CSVs (research phase)
│   └── sourcing.csv
├── sync/                  # Sync State CSVs (operational)
│   └── dsers_shopify_map.csv
├── archive/               # Archived Pipeline files (auto-cleanup)
└── exports/               # Export files for bulk operations

workspace/images/
├── generated/             # AI-generated images
└── content/               # Generated content JSONs
```

### CSV Schemas

#### 1. Product Pipeline CSV (`workspace/csv/pipeline/`)

**Purpose**: Research and planning before importing to DSers. Your "shopping list".

**When to use**: Track products you find on AliExpress/Alibaba before deciding to import.

**Schema**:

| Column            | Type     | Description                                            |
| ----------------- | -------- | ------------------------------------------------------ |
| `id`              | string   | **Primary Key.** Auto-generated (PIPE-XXXX)            |
| `source_url`      | string   | AliExpress/Alibaba/Accio/1688 product URL              |
| `source_platform` | string   | aliexpress \| alibaba \| accio \| 1688                 |
| `estimated_cost`  | decimal  | Expected cost price                                    |
| `suggested_price` | decimal  | Target sell price                                      |
| `notes`           | string   | Research notes, competitor analysis                    |
| `priority`        | enum     | high \| medium \| low                                  |
| `status`          | enum     | researching \| ready_to_import \| imported \| rejected |
| `dsers_import_id` | string   | Filled after import to DSers                           |
| `created_at`      | datetime | When record was created                                |
| `evaluated_at`    | datetime | Last status update                                     |

**Example**:
```csv
id,source_url,source_platform,estimated_cost,suggested_price,notes,priority,status,dsers_import_id,created_at,evaluated_at
PIPE-A1B2C3D4,https://aliexpress.com/item/123,aliexpress,5.99,19.99,Good reviews high demand,high,imported,DS-12345678,2026-04-08T10:00:00Z,2026-04-08T14:30:00Z
PIPE-E5F6G7H8,https://alibaba.com/product/456,alibaba,3.50,14.99,Check quality first,medium,researching,,2026-04-08T11:00:00Z,
```

**Lifecycle**:
```
researching → ready_to_import → imported → [linked to Sync State]
     ↓
  rejected
```

**Auto-cleanup**: Pipeline files archived after 7 days.

#### 2. Sync State CSV (`workspace/csv/sync/`)

**Purpose**: Lightweight ID mapping between DSers and Shopify. No product data, just sync status.

**When to use**: Track which DSers products are pushed, content generation status, variant mappings.

**Schema**:

| Column                | Type     | Description                                          |
| --------------------- | -------- | ---------------------------------------------------- |
| `dsers_product_id`    | string   | **Primary Key.** DSers import ID (source of truth)   |
| `shopify_product_id`  | string   | Shopify product GID after push                       |
| `shopify_variant_ids` | JSON     | Array of Shopify variant GIDs                        |
| `content_status`      | enum     | needs_content \| content_pending \| content_complete |
| `ai_content_path`     | string   | Path to generated content JSON file                  |
| `last_pushed_at`      | datetime | Last push to Shopify timestamp                       |
| `last_synced_at`      | datetime | Last sync check timestamp                            |
| `push_errors`         | string   | Error log if push failed                             |

**Example**:
```csv
ders_product_id,shopify_product_id,shopify_variant_ids,content_status,ai_content_path,last_pushed_at,last_synced_at,push_errors
DS-12345678,gid://shopify/Product/9876543210,"[""gid://shopify/ProductVariant/111"",""gid://shopify/ProductVariant/222""]",content_complete,workspace/images/content/DS-12345678_content.json,2026-04-08T15:00:00Z,2026-04-08T15:00:00Z,
DS-87654321,,"[]",needs_content,,,2026-04-08T14:00:00Z,
```

**Variant Mapping** (flexible 1:1 or 1:many):

```csv
# Simple case: 1 DSers → 1 Shopify product
ders_product_id,shopify_product_id,shopify_variant_ids
DS-001,gid://shopify/Product/100,"[""var_1"",""var_2"",""var_3"]"

# Split case: 1 DSers → Multiple Shopify products
# Example: Hosiery product split by color
DS-002,gid://shopify/Product/200,"[""black_s"",""black_m"]"
DS-002,gid://shopify/Product/201,"[""nude_s"",""nude_m"]"
# Same DS-002 appears twice - two separate Shopify products
```

**Content Status Flow**:
```
needs_content → content_pending → content_complete
                     ↓
               [AI generation in progress]
```

#### 3. Export CSV (`workspace/csv/exports/`)

Bulk operation results for external use (unchanged):

| Column               | Type     | Description                      |
| -------------------- | -------- | -------------------------------- |
| `sku`                | string   | Product SKU                      |
| `operation`          | enum     | `created` / `updated` / `failed` |
| `shopify_product_id` | string   | Resulting Shopify ID             |
| `error_message`      | string   | Error details if failed          |
| `processed_at`       | datetime | When operation completed         |

### Workflow Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                        RESEARCH PHASE                            │
│  ┌──────────────┐    add_product()    ┌──────────────────────┐  │
│  │ AliExpress   │ ─────────────────▶ │  Product Pipeline    │  │
│  │ Alibaba      │                    │  (workspace/csv/     │  │
│  │ Accio        │ ◀───────────────── │   pipeline/)         │  │
│  └──────────────┘   import_complete  │  - Research notes    │  │
│                                      │  - Pricing estimates │  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ import_to_dsers()
┌─────────────────────────────────────────────────────────────────┐
│                      OPERATIONAL PHASE                           │
│  ┌──────────────┐                   ┌──────────────────────┐    │
│  │    DSers     │ ◀──source of────▶ │     Sync State       │    │
│  │   (Import    │     truth        │  (workspace/csv/     │    │
│  │    Staging)  │                   │   sync/)             │    │
│  └──────┬───────┘                   │  - ID mappings       │    │
│         │                           │  - Content status    │    │
│         │ push_to_shopify()         │  - Push status       │    │
│         ▼                           └──────────────────────┘    │
│  ┌──────────────┐                                               │
│  │   Shopify    │                                               │
│  │   (Live      │                                               │
│  │    Store)    │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Key Workflows

#### 1. Research → Import → Push

```
1. User finds AliExpress product
   → create_pipeline_entry(source_url, ...)
   → Status: researching

2. User decides to import
   → update_pipeline_status(id, ready_to_import)
   → dsers_operations imports from URL
   → update_pipeline_status(id, imported, dsers_import_id=DS-XXX)
   → create_sync_entry(dsers_product_id=DS-XXX, content_status=needs_content)

3. AI Content Generation
   → content_studio generates content
   → save_content_json(dsers_product_id, content)
   → update_content_status(dsers_product_id, content_complete, ai_content_path=...)
   → dsers_operations updates product in DSers

4. Push to Shopify
   → dsers_operations pushes to store
   → update_sync_after_push(dsers_product_id, shopify_product_id, variant_ids)
```

#### 2. Content Refresh

```
1. Query products needing content
   → get_by_content_status(needs_content)

2. For each product:
   → Fetch current data from DSers (source of truth)
   → content_studio generates new content
   → save_content_json(dsers_product_id, content)
   → update_content_status(dsers_product_id, content_complete)
   → dsers_operations updates product
```

#### 3. Archive Cleanup (Auto)

```
→ archive_old_pipelines(days=7)
→ Moves old pipeline CSVs to workspace/csv/archive/
```

### Generated Content JSON

AI-generated content stored as JSON files in `workspace/images/content/`:

```json
{
  "dsers_product_id": "DS-12345678",
  "generated_at": "2026-04-08T15:00:00Z",
  "title": {
    "original": "Bluetooth Wireless Headphones Over Ear Foldable",
    "generated": "ProSound Wireless Headphones - Active Noise Cancelling",
    "seo_optimized": "ProSound Wireless Headphones | Active Noise Cancelling Over-Ear"
  },
  "description": {
    "html": "<p>Immersive audio experience...</p>",
    "plain": "Immersive audio experience with active noise cancelling..."
  },
  "seo": {
    "meta_title": "ProSound Wireless Headphones | Active Noise Cancelling",
    "meta_description": "Premium wireless headphones with active noise cancelling and 40-hour battery life...",
    "tags": ["headphones", "wireless", "bluetooth", "noise cancelling", "over-ear"]
  },
  "images": {
    "prompts": [
      "Professional product photography of wireless headphones on white background...",
      "Lifestyle shot of person wearing headphones in a cafe..."
    ],
    "generated_paths": [
      "workspace/images/generated/DS-12345678-hero.jpg",
      "workspace/images/generated/DS-12345678-lifestyle.jpg"
    ]
  }
}
```

## DSers MCP Integration

### Prerequisites
- DSers account (free plan works)
- Shopify or Wix store connected in DSers
- OAuth login: `npx @lofder/dsers-mcp-product login`

### Available Tools (12)

| #   | Tool                         | Description                                   |
| --- | ---------------------------- | --------------------------------------------- |
| 1   | `dsers_store_discover`       | See connected stores, shipping, pricing rules |
| 2   | `dsers_rules_validate`       | Test pricing/title rules before applying      |
| 3   | `dsers_product_import`       | Import from URL with optional rules           |
| 4   | `dsers_product_preview`      | Review imported product                       |
| 5   | `dsers_product_update_rules` | Edit pricing, content, images, variants       |
| 6   | `dsers_product_visibility`   | Set draft vs visible status                   |
| 7   | `dsers_store_push`           | Push to Shopify/Wix (single/bulk/all stores)  |
| 8   | `dsers_job_status`           | Check push completion                         |
| 9   | `dsers_product_delete`       | Remove from import list                       |
| 10  | `dsers_import_list`          | Browse staging list (cost, price, stock)      |
| 11  | `dsers_my_products`          | View pushed products                          |
| 12  | `dsers_find_product`         | Search DSers product pool                     |

### Supported Sources
- AliExpress
- Alibaba.com
- Accio.com (Alibaba's AI sourcing assistant)
- 1688.com (requires DSers authorization)

### Safety Checks
- **Hard blocks**: Below-cost pricing, zero sell price, zero stock
- **Warnings**: Low margin (<10%), low stock (<5), low price (<$1)

## Benefits of Two-CSV System

1. **No Data Duplication**: Original product data lives in DSers
2. **Flexible Variant Mapping**: Handle 1:1 or 1:many DSers→Shopify relationships
3. **Separation of Concerns**:
   - Pipeline = Research/planning phase (temporary)
   - Sync State = Operational tracking (permanent)
4. **Minimal CSV Size**: Only IDs and status, not full product data
5. **Easy Reconstruction**: Always fetch fresh data from DSers/Shopify
6. **Auto-Cleanup**: Pipeline files archived after 1 week
