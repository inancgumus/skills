---
name: flowchart
description: Generate flowcharts and architecture diagrams as interactive HTML or Markdown+ASCII. Use when asked to visualize, diagram, or map out any system, flow, or structure.
---

# Flowchart Generator

Generate architecture diagrams from any context the user provides. Two output formats:

1. **HTML** (default) — interactive single-file viewer, open in browser
2. **Markdown + ASCII** — text-based diagrams with box-drawing characters, embeddable in docs/READMEs

Use Markdown when the user asks for "ASCII", "text diagram", "markdown diagram", or when the output goes into a `.md` file, PR description, or doc. Use HTML for everything else.

## What you produce

### HTML output
A single `.html` file containing:
- The ArchitectureViewer engine (from the engine template)
- A `createArchitectureViewer()` call with extracted architecture data

The viewer provides: interactive node boxes, animated edge routing, API endpoint cards with I/O data, detail panels, centered modal popovers, search (Cmd+K), tab/scene navigation, hover path highlighting, and URL hash state.

### Markdown + ASCII output
A `.md` file containing:
- One ASCII box diagram per scene, using box-drawing characters (`┌─┐│└─┘`, arrows `──▶`, `──▷`, `│`, `▼`)
- Each diagram is a fenced code block (` ```text `)
- Below each diagram, a **Reference** section with linked details for every node
- File paths as markdown links: `[path/to/file.go](https://github.com/org/repo/blob/main/path/to/file.go)`
- Function signatures, descriptions, and notes as bullet points under each node heading

#### ASCII layout rules
- Nodes are boxes: `┌──────────────┐│  Node Title  ││  subtitle     │└──────────────┘`
- Box width: longest line + 4 padding. Minimum 16 chars.
- Horizontal edges: `───▶` or `◀───` between boxes on the same row, with label centered above the arrow
- Vertical edges: `│` with `▼` or `▲` arrow, label to the right of the line
- Grid layout: same column/row structure as the HTML scene positions
- Keep the same visual topology as the HTML version — same rows, columns, connections

#### Markdown reference structure
After each ASCII diagram:

```markdown
### Scene: Overview

(ascii diagram here)

#### Node: API Server
- **File:** [api/main.go](https://github.com/org/repo/blob/main/api/main.go)
- **Description:** REST API handling business logic.
- **Functions:**
  - `HandleRequest(w, r)` — Routes incoming HTTP requests
- **Notes:** Uses middleware chain for auth + logging
```

## Workflow

### 1. Gather context

Read whatever the user points you at — source code, design docs, API specs, conversations, README files, OpenAPI specs, Slack threads, etc. If the user gives a vague request like "diagram this repo", explore the codebase to understand the architecture before generating.

### 2. Extract architecture

From the context, identify:

- **Components** — services, modules, packages, classes, CLI commands, databases, queues, external APIs
- **Relationships** — which component calls/depends on/sends data to which other
- **API endpoints** — HTTP methods, paths, request/response fields
- **Data flows** — what data moves between components and how
- **Groupings** — logical layers (frontend, backend, storage, external), lifecycle phases, deployment stages
- **Issues/status** — if the context mentions tickets, PRs, or status, capture them

### 3. Design scenes

Organize the architecture into scenes (views):

- **Overview** — all major components and their connections
- **Focused views** — zoom into specific flows (e.g., "Auth Flow", "Order Pipeline", "Deploy Process")
- **Before/After** — if the context describes a migration or change, show both states plus a diff view

Group scenes into tabs. Common patterns:
- Single system: tabs = ["Overview"], scenes = overview + focused flows
- Migration: tabs = ["Current", "Target", "Changes"]
- Multi-environment: tabs = ["Dev", "Staging", "Prod"]

### 4. Generate the config

Read `references/config-schema.md` for the full schema. Key rules:

**Node positioning:**
- Use a grid layout: columns at x = 10, 310, 610, 910 (310px apart)
- Rows at y = 10, 140, 270, 400 (130px apart)
- The engine auto-adjusts for endpoint cards, so don't worry about exact spacing
- Place related nodes in the same column or row

**Edge labels:**
- Keep labels short (1-3 words): function names, protocols, or action verbs
- Labels are centered on the edge line automatically
- The `desc` field has the full explanation (shown in modal on click)

**Endpoint cards:**
- Add `endpoints` to edges that represent API calls
- Use abbreviated paths: `/v1/.../users` not `/api/v1/projects/{projectId}/users/{userId}`
- `in` and `out` are comma-separated field names (compact)

**Node detail:**
- `description` should be 1-2 sentences explaining the component's role
- `files[]` links to source code (if applicable)
- `endpoints[]` on nodes have full schema (headers, request/response body, status codes)
- `notes[]` for important context that doesn't fit elsewhere

### 5. Build the HTML file

Read the engine template from `references/engine-template.html`. This contains:
- The full HTML/CSS
- The viewer engine JS (layout, routing, components)
- A placeholder where your data goes

To produce the output file:
1. Copy the engine template
2. Replace the placeholder section with your generated `NODE_DATA` and `SCENES` constants
3. Add the `createArchitectureViewer()` call at the bottom with title, tabs, nodes, scenes, and links
4. Write to the user's specified path (default: `architecture.html` in the current directory)

The structure of the output file:
```
[HTML head + CSS from template]
<script type="text/babel">
[Engine JS from template — everything from React hooks through createArchitectureViewer function]

// ═══ GENERATED DATA ═══
const NODE_DATA = { ... };
const SCENES = { ... };

createArchitectureViewer({
  title: "...",
  tabs: [...],
  nodes: NODE_DATA,
  scenes: SCENES,
  links: { files: [...], issues: [...] }
});
</script>
</body></html>
```

### 6a. HTML: Open in browser

After writing the `.html` file, open it with `agent-browser` or tell the user where to find it.

### 6b. Markdown: Write the `.md` file

For each scene, render an ASCII box diagram inside a fenced code block, then add a **Reference** section below with markdown-linked details for every node. Use the same data extracted in steps 1-3. The reference section should link source files to the repo URL so readers can click through.

## Quality checklist

Before outputting, verify:
- Every node referenced in a scene has an entry in NODE_DATA
- Every edge's `from` and `to` reference nodes that exist in that scene
- No two nodes in the same scene have the same position
- Edge labels are short enough to fit between nodes (~15 chars max)
- At least one scene per tab
- The first scene in each tab is a good overview
- **Names come from the actual code.** Node titles, edge labels, function names, and file paths must match what exists in the codebase. Never invent names like "CacheManager" when the code calls it `cache.go` with a `func EnsureDocs()`. Read the source to find the real names — types, functions, packages, filenames. If there's no obvious name, use the filename or package name, not a made-up CamelCase noun.

## Example: minimal config

For a simple 3-service system:

```js
const NODE_DATA = {
  "client": {
    title: "Web Client", sub: "React SPA",
    category: "Frontend",
    description: "Single-page app served from CDN."
  },
  "api": {
    title: "API Server", sub: "api/main.go",
    category: "Backend",
    description: "REST API handling business logic.",
    endpoints: [
      { method: "POST", path: "/api/users", requestBody: [{ name: "email", type: "string", desc: "User email" }], responseBody: [{ name: "id", type: "int", desc: "Created user ID" }], statusCodes: [{ code: "201", desc: "Created" }] }
    ]
  },
  "db": {
    title: "PostgreSQL", sub: "users, orders",
    category: "Storage",
    description: "Primary data store."
  }
};

const SCENES = {
  "overview": {
    tab: "system", label: "Overview", width: 700, height: 200,
    nodes: [
      { id: "client", x: 10, y: 60 },
      { id: "api", x: 310, y: 60 },
      { id: "db", x: 610, y: 60 }
    ],
    edges: [
      { from: "client", to: "api", label: "REST", desc: "Client calls API over HTTPS.",
        endpoints: [{ method: "POST", path: "/api/users", in: "email", out: "id" }] },
      { from: "api", to: "db", label: "SQL", desc: "API queries PostgreSQL." }
    ]
  }
};

createArchitectureViewer({
  title: "My System",
  tabs: [{ id: "system", label: "System" }],
  nodes: NODE_DATA,
  scenes: SCENES,
  links: { files: [{ baseUrl: "https://github.com/myorg/myrepo/blob/main/" }], issues: [] }
});
```

## Example: Markdown + ASCII output

For the same 3-service system:

````markdown
# My System Architecture

## Overview

```text
┌──────────────┐         REST          ┌──────────────┐         SQL          ┌──────────────┐
│  Web Client  │ ─────────────────────▶ │  API Server  │ ─────────────────────▶ │  PostgreSQL  │
│  React SPA   │                        │  api/main.go │                        │  users,orders│
└──────────────┘                        └──────────────┘                        └──────────────┘
```

### Web Client
- **Category:** Frontend
- **Description:** Single-page app served from CDN.

### API Server
- **File:** [api/main.go](https://github.com/myorg/myrepo/blob/main/api/main.go)
- **Category:** Backend
- **Description:** REST API handling business logic.
- **Endpoints:**
  - `POST /api/users` — in: `email` → out: `id` (201 Created)

### PostgreSQL
- **Category:** Storage
- **Description:** Primary data store for users and orders.
````
