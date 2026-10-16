---
name: recipe-to-notes
description: Turn any recipe link (Instagram reel, TikTok, YouTube, Pinterest pin, or any recipe website) into an Apple Notes note with the ingredients as a tappable checklist and the cooking steps underneath, synced to the iPhone through iCloud. Use whenever someone pastes a recipe link, says "save this recipe", "add this to my recipes", "/recipe", or drops a food video link with no other instructions.
---

# Recipe to Notes

A link goes in. A note comes out on the phone: title, source, link, an ingredients checklist, then numbered instructions.

## Steps

1. **Fetch.** Run:
   ```bash
   python3 "<this skill folder>/scripts/recipe.py" fetch "<link>"
   ```
   It prints JSON with whatever the link gave up. Use the first of these that holds a real recipe:
   - `recipe_schema`: structured recipe from the website (or the site a Pinterest pin points to). Most reliable.
   - `caption`: the post caption on Instagram / TikTok / YouTube. Usually has the recipe.
   - `transcript`: the spoken audio, only when the caption had no recipe (needs `whisper` or `whisperx` installed).
   - `page_text`: raw page text, last resort.
   If none of them has ingredients, stop and say so in one line. **Never invent a recipe.**

2. **Write `recipe.json`** in a temp folder:
   ```json
   {"title": "10-Minute Green Dahl", "source": "The Happy Pear", "meta": "serves 4 · 10 min",
    "url": "<the original link>",
    "ingredients": ["1 tbsp oil", "2 garlic cloves, chopped"],
    "steps": ["Cook the garlic and onion in oil for 1 minute.", "Add everything else and simmer 3 minutes."],
    "notes": "optional: one short tip from the creator"}
   ```
   Rules:
   - One ingredient per line, amount first. Keep the creator's amounts; tidy decimals (`0.25 cup` -> `1/4 cup`).
   - Split run-on captions into separate ingredients and separate steps. One action per step, in order.
   - Title is the dish name, not the post title ("Video by ..." is not a title).
   - Drop hashtags, emojis, "link in bio", and promo lines.
   - `meta` and `notes` are optional; leave them out if the source does not say.

3. **Save.** Run:
   ```bash
   python3 "<this skill folder>/scripts/recipe.py" save /path/to/recipe.json
   ```
   Notes jumps to the front for about 2 seconds while it turns the ingredients into checkboxes. Do not type during that.

4. **Report** in one or two lines: the recipe name, the folder, and whether the ingredients are a checklist or bullets. If the output says `bullets (checklist step failed ...)`, tell the user the one-time fix in the README ("Turn on checkboxes").

## Settings

Environment variables, all optional:
- `RECIPE_NOTES_FOLDER` folder name (default `Recipes`, created if missing)
- `RECIPE_NOTES_ACCOUNT` Notes account (default `iCloud`, the one that syncs to the phone)
- `RECIPE_NOTES_CHECKLIST=0` skip the checkbox step; nothing on screen moves, ingredients are bullets
