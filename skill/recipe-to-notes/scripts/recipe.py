#!/usr/bin/env python3
"""recipe-to-notes: turn any recipe link into an Apple Notes note.

Two commands, used by the Claude skill (SKILL.md) in this order:

  recipe.py fetch <url>          -> prints everything we could read from the link
  recipe.py save <recipe.json>   -> creates the note in Apple Notes (iCloud syncs it to your phone)

recipe.json shape:
  {"title": "...", "source": "Creator or site name", "url": "...",
   "meta": "serves 4 · 30 min" (optional),
   "ingredients": ["1 onion, chopped", ...],
   "steps": ["Cook the onion...", ...],
   "notes": "optional tip line"}

Settings (environment variables, all optional):
  RECIPE_NOTES_FOLDER   Notes folder to save into (default "Recipes", created if missing)
  RECIPE_NOTES_ACCOUNT  Notes account (default "iCloud", the one that syncs to iPhone)
  RECIPE_NOTES_CHECKLIST  "1" (default) turns ingredients into tappable checkboxes,
                          "0" leaves them as bullets and never touches the screen.

Standard library only. macOS only (Apple Notes).
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

VIDEO_HOSTS = ("instagram.com", "tiktok.com", "youtube.com", "youtu.be",
               "facebook.com", "fb.watch", "x.com", "twitter.com", "threads.net")


# ---------------------------------------------------------------- fetch

def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.geturl(), r.read().decode("utf-8", "replace")


def find_recipe_jsonld(page):
    """Most recipe sites embed schema.org Recipe data. Return it if present."""
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, re.S | re.I):
        try:
            data = json.loads(block.strip(), strict=False)  # many sites leave raw newlines in strings
        except ValueError:
            continue
        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, dict):
                kind = item.get("@type")
                kinds = kind if isinstance(kind, list) else [kind]
                if "Recipe" in kinds:
                    return item
                stack.extend(v for v in item.values() if isinstance(v, (list, dict)))
    return None


def meta_tag(page, name):
    m = re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]+content=["\']([^"\']*)' % re.escape(name), page, re.I)
    return html.unescape(m.group(1)) if m else ""


def visible_text(page, limit=6000):
    page = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", page))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def ytdlp_caption(url):
    if not shutil.which("yt-dlp"):
        return None
    try:
        out = subprocess.run(["yt-dlp", "--skip-download", "--no-warnings", "-J", url],
                             capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return None
    if out.returncode != 0:
        return None
    try:
        info = json.loads(out.stdout)
    except ValueError:
        return None
    return {"creator": info.get("uploader") or info.get("channel") or "",
            "title": info.get("title") or "",
            "caption": info.get("description") or ""}


def transcribe(url):
    """Last resort when the caption has no recipe: transcribe the spoken audio."""
    tool = shutil.which("whisperx") or shutil.which("whisper")
    if not (tool and shutil.which("yt-dlp")):
        return None
    tmp = tempfile.mkdtemp(prefix="recipe-")
    audio = os.path.join(tmp, "audio.m4a")
    if subprocess.run(["yt-dlp", "-q", "-f", "bestaudio", "-o", audio, url]).returncode != 0:
        return None
    subprocess.run([tool, audio, "--output_dir", tmp, "--output_format", "txt", "--language", "en"],
                   capture_output=True)
    txt = os.path.join(tmp, "audio.txt")
    return open(txt).read() if os.path.exists(txt) else None


def cmd_fetch(url):
    result = {"url": url}
    host = re.sub(r"^www\.", "", urllib.request.urlparse(url).netloc.lower())

    if any(h in host for h in VIDEO_HOSTS) or "pinterest." in host or "pin.it" in host:
        cap = ytdlp_caption(url)
        if cap:
            result.update(cap)

    if not any(h in host for h in VIDEO_HOSTS):
        try:
            final_url, page = http_get(url)
            result["final_url"] = final_url
            recipe = find_recipe_jsonld(page)
            if recipe:
                result["recipe_schema"] = {k: recipe.get(k) for k in (
                    "name", "author", "recipeYield", "totalTime", "recipeIngredient",
                    "recipeInstructions") if recipe.get(k)}
            else:
                result.setdefault("title", meta_tag(page, "og:title"))
                result["description"] = meta_tag(page, "og:description")
                # Pinterest pins usually point at the real recipe page.
                link = re.search(r'"link"\s*:\s*"(https?://(?!(?:[a-z]+\.)?pinterest)[^"]+)"', page)
                if link:
                    result["links_to"] = link.group(1).encode().decode("unicode_escape")
                    try:
                        linked = find_recipe_jsonld(http_get(result["links_to"])[1])
                        if linked:
                            result["recipe_schema"] = {k: linked.get(k) for k in (
                                "name", "author", "recipeYield", "totalTime", "recipeIngredient",
                                "recipeInstructions") if linked.get(k)}
                    except Exception:  # noqa: BLE001 - the pin text is still there
                        pass
                result["page_text"] = visible_text(page)
        except Exception as e:  # noqa: BLE001 - report, let the skill decide
            result["page_error"] = str(e)

    if any(h in host for h in VIDEO_HOSTS) and not looks_like_recipe(result.get("caption", "")):
        spoken = transcribe(url)
        if spoken:
            result["transcript"] = spoken

    print(json.dumps(result, indent=2, ensure_ascii=False))


def looks_like_recipe(text):
    t = text.lower()
    units = len(re.findall(r"\b(\d+|½|¼|¾)\s*(g|kg|ml|l|cup|cups|tbsp|tsp|oz|lb|tablespoons?|teaspoons?)\b", t))
    return units >= 3 or "ingredients" in t


# ---------------------------------------------------------------- save

def osa(script, *args):
    out = subprocess.run(["osascript", "-", *args], input=script, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip())
    return out.stdout.strip()


def note_html(r, checklist=True):
    e = html.escape
    head = ['<div><h1>%s</h1></div>' % e(r["title"])]
    byline = " · ".join(x for x in (r.get("source"), r.get("meta")) if x)
    if byline:
        head.append("<div>%s</div>" % e(byline))
    if r.get("url"):
        head.append('<div><a href="%s">%s</a></div>' % (e(r["url"]), e(r["url"])))
    head.append("<div><h2>Ingredients</h2></div>")
    if checklist:  # plain paragraphs, turned into checkboxes by the CHECKLIST step
        ingredients = ["<div>%s</div>" % e(i) for i in r["ingredients"]]
    else:
        ingredients = ["<ul>%s</ul>" % "".join("<li>%s</li>" % e(i) for i in r["ingredients"])]
    tail = ["<div><h2>Instructions</h2></div>",
            "<ol>%s</ol>" % "".join("<li>%s</li>" % e(s) for s in r["steps"])]
    if r.get("notes"):
        tail.append("<div><br></div><div><i>%s</i></div>" % e(r["notes"]))
    # Paragraphs before the first ingredient: title, byline?, url?, header
    lead = len(head)
    return "".join(head + ingredients + tail), lead


CREATE = r'''
on run argv
  set folderName to item 1 of argv
  set accountName to item 2 of argv
  set noteBody to item 3 of argv
  tell application "Notes"
    tell account accountName
      if not (exists folder folderName) then make new folder with properties {name:folderName}
      set n to make new note at folder folderName with properties {body:noteBody}
    end tell
    return id of n
  end tell
end run
'''

# Notes has no scripting command for checklists, so we use its own menu
# (Format > Checklist, cmd-shift-L) on exactly the ingredient paragraphs.
CHECKLIST = r'''
on run argv
  set noteId to item 1 of argv
  set leadCount to (item 2 of argv) as integer
  set itemCount to (item 3 of argv) as integer
  tell application "Notes"
    activate
    show note id noteId
  end tell
  delay 1.2
  tell application "System Events"
    tell process "Notes"
      set frontmost to true
      key code 126 using command down -- cmd-up: top of note
      delay 0.2
      repeat leadCount times
        key code 125 using option down -- option-down: end of paragraph
      end repeat
      key code 124 -- right: start of first ingredient
      repeat itemCount times
        key code 125 using {option down, shift down} -- extend to end of next paragraph
      end repeat
      delay 0.2
      click menu item "Checklist" of menu 1 of menu bar item "Format" of menu bar 1
      delay 0.3
      key code 126 using command down
    end tell
  end tell
end run
'''


def cmd_save(path):
    r = json.load(open(path))
    for k in ("title", "ingredients", "steps"):
        if not r.get(k):
            sys.exit("recipe.json is missing '%s'" % k)
    folder = os.environ.get("RECIPE_NOTES_FOLDER", "Recipes")
    account = os.environ.get("RECIPE_NOTES_ACCOUNT", "iCloud")
    checklist = os.environ.get("RECIPE_NOTES_CHECKLIST", "1") != "0"
    body, lead = note_html(r, checklist)
    note_id = osa(CREATE, folder, account, body)
    status = "bullets"
    if checklist:
        try:
            osa(CHECKLIST, note_id, str(lead), str(len(r["ingredients"])))
            status = "checklist"
        except RuntimeError as e:
            # Fall back to bullets so the note still reads well on the phone.
            osa('on run argv\ntell application "Notes" to set body of note id (item 1 of argv) to (item 2 of argv)\nend run',
                note_id, note_html(r, False)[0])
            status = "bullets (checklist step failed: %s)" % e
    print(json.dumps({"saved": r["title"], "folder": "%s / %s" % (account, folder),
                      "ingredients": status, "note_id": note_id}))


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("fetch", "save"):
        sys.exit(__doc__)
    (cmd_fetch if sys.argv[1] == "fetch" else cmd_save)(sys.argv[2])
