// Popular vim/neovim colorscheme themes mapped to the Architecture Viewer CSS variables.
// Each theme uses its SIGNATURE/ICONIC color as the accent — the color that makes it
// immediately recognizable. This is NOT always the theme's "blue" — it's the color
// people associate with that theme (e.g. Dracula=pink, Gruvbox=orange, Monokai=pink).
//
// Themes are grouped by "dark" or "light" and shown in separate sections in the picker.
// This file is a standalone reference. The engine template embeds these inline.

const THEMES = {
  // ─── Dark (23 themes) ───
  // Accent = signature color for each theme
  "catppuccin-mocha":     { group: "dark", label: "Catppuccin Mocha",     accent: "mauve #cba6f7" },
  "catppuccin-frappe":    { group: "dark", label: "Catppuccin Frappé",    accent: "mauve #ca9ee6" },
  "catppuccin-macchiato": { group: "dark", label: "Catppuccin Macchiato", accent: "mauve #c6a0f6" },
  "tokyo-night":          { group: "dark", label: "Tokyo Night",          accent: "purple #bb9af7" },
  "tokyo-night-storm":    { group: "dark", label: "Tokyo Night Storm",    accent: "magenta #ff007c" },
  "tokyonight-moon":      { group: "dark", label: "Tokyo Night Moon",     accent: "purple #c099ff" },
  "gruvbox-dark":         { group: "dark", label: "Gruvbox Dark",         accent: "orange #fe8019" },
  "nord":                 { group: "dark", label: "Nord",                 accent: "frost #88c0d0" },
  "dracula":              { group: "dark", label: "Dracula",              accent: "pink #ff79c6" },
  "one-dark":             { group: "dark", label: "One Dark",             accent: "purple #c678dd" },
  "solarized-dark":       { group: "dark", label: "Solarized Dark",       accent: "yellow #b58900" },
  "rose-pine":            { group: "dark", label: "Rosé Pine",            accent: "rose #ebbcba" },
  "rose-pine-moon":       { group: "dark", label: "Rosé Pine Moon",       accent: "iris #c4a7e7" },
  "kanagawa":             { group: "dark", label: "Kanagawa",             accent: "oniViolet #957fb8" },
  "everforest-dark":      { group: "dark", label: "Everforest Dark",      accent: "green #a7c080" },
  "nightfox":             { group: "dark", label: "Nightfox",             accent: "coral #c94f6d" },
  "carbonfox":            { group: "dark", label: "Carbonfox",            accent: "magenta #ee5396" },
  "github-dark":          { group: "dark", label: "GitHub Dark",          accent: "blue #58a6ff" },
  "ayu-dark":             { group: "dark", label: "Ayu Dark",             accent: "orange #e6b450" },
  "ayu-mirage":           { group: "dark", label: "Ayu Mirage",           accent: "yellow #ffcc66" },
  "monokai-pro":          { group: "dark", label: "Monokai Pro",          accent: "pink #ff6188" },
  "material-deep-ocean":  { group: "dark", label: "Material Deep Ocean",  accent: "cyan #89ddff" },
  "palenight":            { group: "dark", label: "Palenight",            accent: "purple #c792ea" },

  // ─── Light (11 themes) ───
  "catppuccin-latte":     { group: "light", label: "Catppuccin Latte",    accent: "mauve #8839ef" },
  "tokyo-night-light":    { group: "light", label: "Tokyo Night Light",   accent: "brown #965027" },
  "gruvbox-light":        { group: "light", label: "Gruvbox Light",       accent: "orange #af3a03" },
  "solarized-light":      { group: "light", label: "Solarized Light",     accent: "orange #cb4b16" },
  "rose-pine-dawn":       { group: "light", label: "Rosé Pine Dawn",      accent: "love #b4637a" },
  "everforest-light":     { group: "light", label: "Everforest Light",    accent: "green #8da101" },
  "one-light":            { group: "light", label: "One Light",           accent: "purple #a626a4" },
  "github-light":         { group: "light", label: "GitHub Light",        accent: "blue #0969da" },
  "ayu-light":            { group: "light", label: "Ayu Light",           accent: "orange #f2ae49" },
  "dayfox":               { group: "light", label: "Dayfox",              accent: "red #a5222f" },
  "kanagawa-lotus":       { group: "light", label: "Kanagawa Lotus",      accent: "violet #624c83" }
};

// See engine-template.html for full vars definitions per theme.
