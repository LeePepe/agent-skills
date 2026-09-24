---
name: save-tool
description: Use when the user shares a message containing skills, tools, GitHub repos, or resource links they want to stockpile for later — "存起来", "save this tool", "collect these links", "先放着以后再看怎么用". Extracts every repo/link/tool from the pasted content, dedupes against what's already saved, and files each into ~/Development/Personal/collected-tools/ as a one-topic Markdown note with repo URL + link + how-to-use, updating the folder README index. Does NOT install or run anything.
allowed-tools: Read, Write, Edit, Bash, WebFetch
---

# Save Tool

Turn a pasted message (a video script, a tweet, a list of links, a "check out these tools" dump) into durable, organized notes under a single stockpile folder — so the user can decide *how to use* them later without re-finding them.

**Announce at start:** "I'm using the save-tool skill."

## The stockpile folder

`${COLLECTED_TOOLS_DIR:-~/Development/Personal/collected-tools}/`

- `README.md` — the index. A table: file | 種別 | one-line summary. Plus a short "使い方の方針" note.
- One `.md` file per topic (per tool/skill/resource-group). Kebab-case filename.
- Each note holds: repo URL, link(s), what it is, how it's used, and a "実際に使ったメモ" section (empty until tried).

Memory does NOT hold the tools themselves — only one pointer note (`collected-tools-folder`) saying the folder exists. Never grow memory per-tool.

## Steps

1. **Extract.** Scan the pasted content for every actionable item:
   - GitHub repos (`github.com/owner/repo`)
   - Websites / galleries / docs links (bare domains count: `landing.love`, `mobbin.com`)
   - Named tools/skills even without a link (note them, mark link as "unknown — needs lookup")
   Pull the surrounding one-line description the user gave for each.

2. **Group.** Decide what becomes its own file vs. what belongs together. Rule of thumb:
   - A distinct installable tool/skill/repo → its own file.
   - A themed *set* of similar resources (e.g. 8 design-gallery sites) → one file for the whole set.
   Don't over-split; don't dump unrelated things into one file.

3. **Dedupe.** `ls` the folder and read `README.md`. If a topic already has a file, **append** to it (add the new link/note) instead of creating a duplicate. Match by repo/domain, not just title.

4. **Enrich (light, optional).** For a GitHub repo whose purpose is unclear from the message, you MAY `WebFetch` the repo to get a one-line "what it is". Keep it to one fetch per unknown repo; skip if the user's own description is already clear. Never install, clone, or run anything — this skill only *saves*.

5. **Write the note(s).** For each file use this shape:

   ```markdown
   # <Tool / Topic name>

   <one-line what-it-is>

   - リポジトリ / link: <url>
   - 形態: <CLI / skill / plugin / website / component-lib / repo-collection ...>
   - (対応ツールや前提があれば)

   ## インストール / 使い方
   <commands or usage, if known>

   ## 実際に使ったメモ
   _(まだ未使用。試したらここに追記)_
   ```

   For a resource *set*, use a table of link | 用途 instead of the single-tool shape.

6. **Update the index.** Add/refresh the row(s) in `collected-tools/README.md`. Keep it one line per file.

7. **Report.** Tell the user, in their language, what was saved (new files vs. appended), and note any item whose link you couldn't resolve. Offer a concrete next step (e.g. "試しに1つインストールしてみる?") but do not act on it unless asked.

## Boundaries

- **Save only.** No `npm install`, no `git clone`, no `omm setup`, no running. If the user wants to try one, that's a separate ask.
- **One pointer in memory, not N.** If the folder-pointer memory note doesn't exist yet, create it once; otherwise leave memory alone.
- **Preserve the user's own words** for each item's description — they captured why it caught their eye.
