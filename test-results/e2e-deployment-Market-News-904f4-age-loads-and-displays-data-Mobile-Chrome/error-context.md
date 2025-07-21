# Page snapshot

```yaml
- img
- text: Market Analysis
- navigation:
  - link "Dashboard":
    - /url: /
    - img
    - text: Dashboard
  - link "Articles":
    - /url: /articles
    - img
    - text: Articles
  - link "Positions":
    - /url: /positions
    - img
    - text: Positions
  - link "Settings":
    - /url: /settings
    - img
    - text: Settings
- main:
  - heading "Articles" [level=1]
  - paragraph: Browse and search scraped financial news articles
  - img
  - textbox "Search articles..."
  - combobox:
    - option "All Sources" [selected]
    - option "FinViz"
    - option "BizToc"
  - textbox "Filter by ticker..."
  - button "Clear Filters":
    - img
    - text: Clear Filters
  - paragraph: Loading articles...
```