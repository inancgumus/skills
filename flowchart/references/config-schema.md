# Architecture Viewer Config Schema

## Top-level config

```js
createArchitectureViewer({
  title:  "string",           // Page title
  tabs:   Tab[],              // Tab definitions
  nodes:  { [id]: Node },     // All node definitions (keyed by unique ID)
  scenes: { [id]: Scene },    // All scene definitions (keyed by unique ID)
  links:  Links,              // URL patterns for files and issues
  theme:  "string"            // Optional: default theme ID (e.g. "catppuccin-mocha", "tokyo-night")
})
```

## Theme

Optional. Sets the default colorscheme. The user can switch themes at runtime via a dropdown. Choice persists in localStorage.

34 themes available, grouped in the picker dropdown:

**Dark (23):** `catppuccin-mocha`, `catppuccin-frappe`, `catppuccin-macchiato`, `tokyo-night`, `tokyo-night-storm`, `tokyonight-moon`, `gruvbox-dark`, `nord`, `dracula`, `one-dark`, `solarized-dark`, `rose-pine`, `rose-pine-moon`, `kanagawa`, `everforest-dark`, `nightfox`, `carbonfox`, `github-dark`, `ayu-dark`, `ayu-mirage`, `monokai-pro`, `material-deep-ocean`, `palenight`

**Light (11):** `catppuccin-latte`, `tokyo-night-light`, `gruvbox-light`, `solarized-light`, `rose-pine-dawn`, `everforest-light`, `one-light`, `github-light`, `ayu-light`, `dayfox`, `kanagawa-lotus`

If omitted, the viewer uses its built-in dark style (close to One Dark).

## Tab

```js
{ id: "string", label: "string" }
```

## Node

Every node referenced by a scene must have an entry here.

```js
{
  title: "string",                    // Display name (shown in box)
  sub: "string",                      // Subtitle (file path, module name)
  category: "string",                 // Grouping label (shown in detail panel)
  description: "string",              // Full description (detail panel)

  // Optional
  changeStatus: "new"|"changed"|"removed"|"unchanged",  // For change-tracking scenes
  beforeState: "string",              // "Before" state text (for change nodes)
  afterState: "string",               // "After" state text (for change nodes)
  incomplete: true,                   // Red dot indicator (not yet implemented)

  files: ["path/to/file.go:42"],      // Source files (linked via links.files)

  functions: [{                       // Function signatures
    name: "FuncName",
    sig: "(ctx context.Context) error",
    desc: "What it does",
    file: "pkg/file.go:100"
  }],

  endpoints: [{                       // API endpoints (shown in detail panel)
    method: "GET"|"POST"|"PUT"|"DELETE",
    path: "/api/v1/resource/{id}",
    headers: ["Authorization: Bearer {token}"],
    requestBody: [{ name: "field", type: "string", desc: "Description" }],
    responseBody: [{ name: "field", type: "string", desc: "Description" }],
    statusCodes: [{ code: "200", desc: "OK" }, { code: "404", desc: "Not found" }],
    calledBy: "pkg/client.go:42"
  }],

  issues: [{                          // Tracked issues
    id: "PROJ-123",
    title: "Issue title",
    status: "done"|"open"|"pending",
    url: "https://..."
  }],

  notes: ["Free-text notes. URLs and code patterns auto-linked."]
}
```

## Scene

```js
{
  tab: "tab-id",                      // Which tab this scene belongs to
  label: "string",                    // Scene sub-tab label
  width: 1000,                        // Scene coordinate space width
  height: 600,                        // Scene coordinate space height (layout engine may expand)

  nodes: [{                           // Positioned nodes
    id: "node-id",                    // References a key in the nodes object
    x: 340,                           // X position in scene coordinates
    y: 120,                           // Y position in scene coordinates
    status: "changed"                 // Optional: change badge for this node in this scene
  }],

  edges: [{                           // Connections between nodes
    from: "node-id-a",
    to: "node-id-b",
    label: "edge label",              // Short label shown centered on the edge line
    desc: "Full description",         // Shown in modal when clicking the label

    endpoints: [{                     // Optional: API endpoint cards shown below the from-node
      method: "POST",
      path: "/v1/resource",           // Abbreviated path (shown on card)
      in: "name, type",              // Compact input summary
      out: "id, status"             // Compact output summary
    }]
  }],

  notes: "Flow annotation shown at bottom of scene"
}
```

## Links

```js
{
  files: [{
    baseUrl: "https://github.com/org/repo/blob/main/",
    pattern: /regex/                  // Optional: only match files matching this pattern
  }],

  issues: [{
    prefix: "PROJ-",                  // Matches "PROJ-123" in issue IDs
    url: "https://linear.app/org/issue/PROJ-"  // Number appended to this URL
  }]
}
```

## Layout Behavior

- The engine auto-adjusts node positions to avoid overlaps when endpoint cards are added
- Edge labels are always centered at the 50% point of the edge path
- Horizontal gaps between connected nodes are widened if needed to fit the label
- Scene height/width expand automatically to fit all elements
- Endpoint cards stack below their parent node (the `from` node of the edge)

## Positioning Tips

- Place nodes in a grid-like pattern with ~300px horizontal gaps and ~120px vertical gaps
- The engine uses 15rem-wide nodes (~195px at 13px root font)
- Scene coordinates map to CSS pixels at scale=1; the viewer auto-scales to fit
- For 3-column layouts, use x positions like 10, 340, 670
- For 4-column layouts, use 10, 340, 670, 1000
