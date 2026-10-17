# Recipe to Notes

A free Claude Code skill. Paste any recipe link and it lands in Apple Notes on your iPhone:

- **Ingredients** as a checklist you can tick off at the store
- **Instructions** as numbered steps underneath
- The original link at the top

Works with Instagram reels, TikTok, YouTube, Pinterest pins, and any recipe website.

```
you:    https://www.instagram.com/reel/...
Claude: Saved "10-Minute Green Dahl" to iCloud / Recipes, ingredients as a checklist.
```

## What you need

- A Mac with Apple Notes signed in to iCloud (that is what puts it on your phone)
- [Claude Code](https://claude.com/claude-code)
- Python 3 (already on every Mac)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for video links: `brew install yt-dlp`
- Optional: [whisper](https://github.com/openai/whisper) for videos where the recipe is only spoken, not written in the caption

## Install

```bash
git clone https://github.com/EnergySteve/recipe-to-notes.git
mkdir -p ~/.claude/skills
cp -R recipe-to-notes/skill/recipe-to-notes ~/.claude/skills/
```

Restart Claude Code. Then paste a recipe link, or type `/recipe-to-notes <link>`.

## Turn on checkboxes (one time)

Apple does not let apps create checklists in the background, so the skill uses the Notes menu for you (Format > Checklist). Notes pops up for about 2 seconds per recipe.

The first time, macOS asks for permission. If it says it is "not allowed to send keystrokes":

1. Open **System Settings > Privacy & Security > Accessibility**
2. Turn on the app you run Claude Code in (Claude, Terminal, iTerm, VS Code...)
3. Run the recipe again

Rather not have Notes pop up? Set `RECIPE_NOTES_CHECKLIST=0` and ingredients are saved as bullets, fully in the background.

## Settings

| Variable | Default | What it does |
|---|---|---|
| `RECIPE_NOTES_FOLDER` | `Recipes` | Notes folder to save into (created if missing) |
| `RECIPE_NOTES_ACCOUNT` | `iCloud` | Notes account. iCloud is the one that syncs to your phone |
| `RECIPE_NOTES_CHECKLIST` | `1` | `0` = bullets, no screen pop-up |

## How it works

`scripts/recipe.py fetch <link>` reads the recipe: the structured recipe data most cooking sites publish, the caption of a video post, the site a Pinterest pin points to, or (last resort) the spoken audio. Claude turns that into clean ingredients and steps. `scripts/recipe.py save` writes the note through AppleScript.

No accounts, no API keys, nothing leaves your Mac except the request to the recipe page itself.

## License

MIT
