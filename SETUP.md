# Setup (for Claude)

The person who sent you here wants Recipe Genius: paste a recipe link, get an Apple Notes note on their phone. They are probably not technical. Do every step yourself, keep what you say short and friendly, and never ask them to type a command.

## 1. Check the Mac

This only works on a Mac, in Claude Code (the Code tab in the Claude app, or the `claude` terminal). If you are not on a Mac with a shell, say so in one friendly line and stop.

## 2. Install the skill

```bash
mkdir -p ~/.claude/skills
git clone --depth 1 https://github.com/EnergySteve/recipe-to-notes.git /tmp/recipe-to-notes
cp -R /tmp/recipe-to-notes/skill/recipe-to-notes ~/.claude/skills/
```

If `~/.claude/skills/recipe-to-notes` already exists, ask before replacing it.

## 3. Video links (optional)

If `brew` is installed and `yt-dlp` is not, run `brew install yt-dlp`. It reads Instagram, TikTok and YouTube captions. No Homebrew? Skip it. Recipe websites still work.

## 4. Test it once

Follow `~/.claude/skills/recipe-to-notes/SKILL.md` on this link:

https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/

The Mac will ask for permission the first time. Tell them exactly what to click:
- "Claude wants to control Notes" -> click **Allow**.
- "Not allowed to send keystrokes" -> open **System Settings > Privacy & Security > Accessibility**, turn on **Claude** (or whatever app they run Claude Code in), then run the test again.

Confirm the cookie note is in Notes > Recipes before moving on.

## 5. Show them how it works

Draw one simple picture (a visual if you can, a text box diagram if not), five boxes left to right:

1. You paste a link
2. I read the recipe
3. I tidy it up
4. It pops up in Notes > Recipes
5. It's on your phone

## 6. Hand it over

Until Claude Code restarts, the new skill may not load on its own, so for the rest of this chat follow SKILL.md yourself whenever they paste a link. Then end with exactly:

"You're all set, Recipe Genius! 🧑‍🍳 Now just give me a recipe link and watch it pop up in your Notes app."
