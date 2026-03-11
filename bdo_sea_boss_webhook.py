#!/usr/bin/env python3
"""
BDO SEA World Boss Discord Webhook
====================================
- Alerts 15 min AND 5 min before each boss spawns (separate messages)
- Announces the moment a boss spawns
- Only alerts for the boss that is actually about to spawn — not all bosses at once
- Full SEA schedule including LOML bosses (Bulgasal, Uturi, Sangoon, Golden Pig King)
- Cron-safe: designed to run every 5 minutes via GitHub Actions

SETUP:
  1. Set DISCORD_WEBHOOK_URL env var (or paste it below)
  2. GitHub Actions cron:  */5 * * * *
  3. pip install requests
"""

import os
import requests
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "YOUR_DISCORD_WEBHOOK_URL_HERE")

# Alert windows in minutes — script checks each one every run
ALERT_WINDOWS = [15, 5, 0]   # 0 = "spawning now"

# Tolerance in seconds: how far off the cron can be and still trigger
# 150s = ±2.5 min, safe for a 5-min cron that may run slightly late
TOLERANCE = 150

# UTC+8 (SEA / WITA)
UTC8 = timezone(timedelta(hours=8))

# ─────────────────────────────────────────────
#  BOSS METADATA
# ─────────────────────────────────────────────
BOSS_INFO = {
    "Kzarka": {
        "color":    0xE74C3C,
        "icon":     "https://mmotimer.com/img/kzarka_big.png",
        "location": "Serendia Temple (south of Heidel)",
        "drops":    "Kzarka Main Weapon Box, Hunter Seals, Black Stones",
        "tag":      "classic",
    },
    "Karanda": {
        "color":    0x9B59B6,
        "icon":     "https://mmotimer.com/img/karanda_big.png",
        "location": "Karanda Ridge (northeast Calpheon)",
        "drops":    "Dandelion Awakening Weapon Box, Hunter Seals, Black Stones",
        "tag":      "classic",
    },
    "Kutum": {
        "color":    0xF39C12,
        "icon":     "https://mmotimer.com/img/kutum_big.png",
        "location": "Kutum Cave (Valencia Desert)",
        "drops":    "Kutum Sub-weapon Box, Hunter Seals, Black Stones",
        "tag":      "classic",
    },
    "Nouver": {
        "color":    0x3498DB,
        "icon":     "https://mmotimer.com/img/nouver_big.png",
        "location": "Nouver's Pit (Valencia Desert) — Bring desert potions!",
        "drops":    "Nouver Sub-weapon Box, Hunter Seals, Black Stones",
        "tag":      "classic",
    },
    "Garmoth": {
        "color":    0xC0392B,
        "icon":     "https://mmotimer.com/img/garmoth_big.png",
        "location": "Garmoth's Nest (Drieghan) — Destroy statues to reveal her!",
        "drops":    "Garmoth's Heart (rare!), Garmoth Scales, Garmoth's Horn",
        "tag":      "classic",
    },
    "Offin": {
        "color":    0x2ECC71,
        "icon":     "https://mmotimer.com/img/offin_big.png",
        "location": "Holo Forest (Kamasylvia)",
        "drops":    "Offin Tett Weapon Box, Valtarra's Eclipsed Belt",
        "tag":      "classic",
    },
    "Vell": {
        "color":    0x1ABC9C,
        "icon":     "https://mmotimer.com/img/vell_big.png",
        "location": "Vell's Realm — Open ocean north of Lema Island 🚢",
        "drops":    "Vell's Heart, Gold Bars, Rare Accessories",
        "tag":      "classic",
    },
    "Quint": {
        "color":    0x95A5A6,
        "icon":     "https://mmotimer.com/img/quint_big.png",
        "location": "Quint Hill (northwest Calpheon) — Only 15 min to kill!",
        "drops":    "Hunter Seals, Cron Stones, Silver",
        "tag":      "classic",
    },
    "Muraka": {
        "color":    0x795548,
        "icon":     "https://mmotimer.com/img/muraka_big.png",
        "location": "West of Mansha Forest / Lake Kaia — Only 15 min to kill!",
        "drops":    "Hunter Seals, Cron Stones, Silver",
        "tag":      "classic",
    },
    "Bulgasal": {
        "color":    0xE67E22,
        "icon":     "https://mmotimer.com/img/bulgasal_big.png",
        "location": "Land of the Morning Light — Hadum's Realm (Hwanghae Party)",
        "drops":    "Flame of the Primordial ★, Primordial Crystal, Asadal Necklace, Caphras Bundle",
        "tag":      "loml",
    },
    "Uturi": {
        "color":    0xF1C40F,
        "icon":     "https://mmotimer.com/img/uturi_big.png",
        "location": "Land of the Morning Light — Martial God Tournament Arena",
        "drops":    "Flame of the Primordial ★, Primordial Crystal, Asadal Belt, Caphras Bundle",
        "tag":      "loml",
    },
    "Sangoon": {
        "color":    0xE91E63,
        "icon":     "https://mmotimer.com/img/sangoon_big.png",
        "location": "Land of the Morning Light — Hadum's Domain",
        "drops":    "Flame of the Primordial ★, Primordial Crystal, Asadal Necklace, Caphras Bundle",
        "tag":      "loml",
    },
    "Golden Pig King": {
        "color":    0xFFD700,
        "icon":     "https://mmotimer.com/img/pig_big.png",
        "location": "Land of the Morning Light — Roams the open fields",
        "drops":    "Flame of the Primordial ★, Primordial Crystal, Asadal Belt, Gold Bars",
        "tag":      "loml",
    },
}

# ─────────────────────────────────────────────
#  SEA BOSS SCHEDULE  (UTC+8 / WITA)
#  Corrected against official Garmoth.com timetable screenshot
#  day: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
# ─────────────────────────────────────────────
SEA_SCHEDULE = [
    # ── Monday ──────────────────────────────────────────────────────────
    {"day": 0, "hour":  1, "min": 30, "bosses": ["Karanda",  "Bulgasal"]},
    {"day": 0, "hour": 11, "min":  0, "bosses": ["Kzarka",   "Uturi"]},
    {"day": 0, "hour": 14, "min":  0, "bosses": ["Garmoth"]},
    {"day": 0, "hour": 15, "min":  0, "bosses": ["Kutum",    "Golden Pig King"]},
    {"day": 0, "hour": 20, "min":  0, "bosses": ["Karanda",  "Sangoon"]},
    {"day": 0, "hour": 23, "min": 15, "bosses": ["Garmoth"]},
    # ── Tuesday ─────────────────────────────────────────────────────────
    {"day": 1, "hour":  1, "min": 30, "bosses": ["Nouver",   "Sangoon"]},
    {"day": 1, "hour": 11, "min":  0, "bosses": ["Kutum",    "Golden Pig King"]},
    {"day": 1, "hour": 14, "min":  0, "bosses": ["Garmoth"]},
    {"day": 1, "hour": 15, "min":  0, "bosses": ["Kzarka",   "Sangoon"]},
    {"day": 1, "hour": 19, "min":  0, "bosses": ["Quint",    "Muraka"]},
    {"day": 1, "hour": 20, "min":  0, "bosses": ["Kzarka",   "Uturi"]},
    {"day": 1, "hour": 23, "min": 15, "bosses": ["Garmoth"]},
    {"day": 1, "hour": 23, "min": 30, "bosses": ["Nouver",   "Bulgasal"]},
    # ── Wednesday ───────────────────────────────────────────────────────
    {"day": 2, "hour":  1, "min": 30, "bosses": ["Offin",    "Golden Pig King"]},
    {"day": 2, "hour": 11, "min":  0, "bosses": ["Nouver",   "Bulgasal"]},
    {"day": 2, "hour": 14, "min":  0, "bosses": ["Garmoth"]},
    {"day": 2, "hour": 15, "min":  0, "bosses": ["Karanda",  "Uturi"]},
    {"day": 2, "hour": 20, "min":  0, "bosses": ["Kutum",    "Bulgasal"]},
    {"day": 2, "hour": 23, "min": 15, "bosses": ["Garmoth"]},
    # ── Thursday ────────────────────────────────────────────────────────
    {"day": 3, "hour":  0, "min":  0, "bosses": ["Vell"]},
    {"day": 3, "hour":  1, "min": 30, "bosses": ["Kutum",    "Uturi"]},
    {"day": 3, "hour": 11, "min":  0, "bosses": ["Kzarka",   "Sangoon"]},
    {"day": 3, "hour": 14, "min":  0, "bosses": ["Garmoth"]},
    {"day": 3, "hour": 15, "min":  0, "bosses": ["Nouver",   "Golden Pig King"]},
    {"day": 3, "hour": 20, "min":  0, "bosses": ["Kzarka",   "Sangoon"]},
    {"day": 3, "hour": 23, "min": 15, "bosses": ["Garmoth"]},
    {"day": 3, "hour": 23, "min": 30, "bosses": ["Karanda",  "Uturi"]},
    # ── Friday ──────────────────────────────────────────────────────────
    {"day": 4, "hour":  1, "min": 30, "bosses": ["Nouver",   "Sangoon"]},
    {"day": 4, "hour": 11, "min":  0, "bosses": ["Kutum",    "Bulgasal"]},
    {"day": 4, "hour": 14, "min":  0, "bosses": ["Garmoth"]},
    {"day": 4, "hour": 15, "min":  0, "bosses": ["Karanda",  "Uturi"]},
    {"day": 4, "hour": 20, "min":  0, "bosses": ["Nouver",   "Golden Pig King"]},
    {"day": 4, "hour": 23, "min": 15, "bosses": ["Garmoth"]},
    {"day": 4, "hour": 23, "min": 30, "bosses": ["Offin",    "Bulgasal"]},
    # ── Saturday ────────────────────────────────────────────────────────
    {"day": 5, "hour":  1, "min": 30, "bosses": ["Karanda",  "Golden Pig King"]},
    {"day": 5, "hour": 11, "min":  0, "bosses": ["Karanda",  "Golden Pig King"]},
    {"day": 5, "hour": 14, "min":  0, "bosses": ["Garmoth"]},
    {"day": 5, "hour": 15, "min":  0, "bosses": ["Kutum",    "Sangoon"]},
    {"day": 5, "hour": 18, "min":  0, "bosses": ["Garmoth"]},
    {"day": 5, "hour": 19, "min":  0, "bosses": ["Quint",    "Muraka"]},
    {"day": 5, "hour": 20, "min":  0, "bosses": ["Karanda",  "Bulgasal"]},
    # ── Sunday ──────────────────────────────────────────────────────────
    {"day": 6, "hour":  1, "min": 30, "bosses": ["Kzarka",   "Golden Pig King"]},
    {"day": 6, "hour": 11, "min":  0, "bosses": ["Nouver",   "Sangoon"]},
    {"day": 6, "hour": 14, "min":  0, "bosses": ["Garmoth"]},
    {"day": 6, "hour": 15, "min":  0, "bosses": ["Kutum",    "Bulgasal"]},
    {"day": 6, "hour": 16, "min":  0, "bosses": ["Vell"]},
    {"day": 6, "hour": 20, "min": 15, "bosses": ["Kzarka",   "Uturi"]},
    {"day": 6, "hour": 23, "min": 15, "bosses": ["Garmoth"]},
    {"day": 6, "hour": 23, "min": 30, "bosses": ["Nouver",   "Golden Pig King"]},
]


def get_all_upcoming(hours_ahead=24):
    """Return all spawn slots within the next N hours."""
    now = datetime.now(UTC8)
    cutoff = now + timedelta(hours=hours_ahead)
    results = []
    for day_offset in range(8):
        check_date = now + timedelta(days=day_offset)
        weekday = check_date.weekday()
        for entry in SEA_SCHEDULE:
            if entry["day"] != weekday:
                continue
            spawn_dt = check_date.replace(
                hour=entry["hour"], minute=entry["min"], second=0, microsecond=0
            )
            if now < spawn_dt <= cutoff:
                results.append({"dt": spawn_dt, "bosses": entry["bosses"]})
    results.sort(key=lambda x: x["dt"])
    return results


def build_embed(boss, spawn_dt, alert_type):
    """Build a single Discord embed for one boss at one alert level."""
    info    = BOSS_INFO.get(boss, {})
    is_loml = info.get("tag") == "loml"

    if alert_type == 0:
        title     = f"🔴  {boss} IS SPAWNING NOW!"
        time_line = "**BOSS IS LIVE — Get there NOW!**"
    elif alert_type == 5:
        title     = f"⚠️  {boss} — 5 Minutes!"
        time_line = "Spawning in **~5 minutes**"
    else:
        title     = f"⏰  {boss} — 15 Minutes"
        time_line = "Spawning in **~15 minutes**"

    loml_note = "\n> 🌅 *LOML boss — requires party, once-per-week loot*" if is_loml else ""

    description = (
        f"{time_line}\n"
        f"🕐 **Spawn:** {spawn_dt.strftime('%A %d %b — %H:%M (UTC+8)')}\n"
        f"📍 **Location:** {info.get('location', 'Unknown')}\n"
        f"🎁 **Drops:** {info.get('drops', 'Various items')}"
        f"{loml_note}"
    )

    return {
        "title":       title,
        "description": description,
        "color":       info.get("color", 0x95A5A6),
        "thumbnail":   {"url": info.get("icon", "")},
        "footer": {
            "text":     "BDO SEA • garmoth.com/boss-timer",
            "icon_url": "https://garmoth.com/favicon.ico",
        },
        "timestamp": spawn_dt.isoformat(),
    }


def send_embeds(embeds, content=None):
    """POST to Discord webhook. Discord allows max 10 embeds per call."""
    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        import json
        print("[WARN] No webhook URL — preview only:")
        print(json.dumps({"content": content, "embeds": embeds}, indent=2, default=str))
        return

    for i in range(0, len(embeds), 10):
        chunk = embeds[i:i+10]
        payload = {
            "username":   "BDO SEA Boss Timer",
            "avatar_url": "https://garmoth.com/favicon.ico",
            "embeds":     chunk,
        }
        if content and i == 0:
            payload["content"] = content
        resp = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code in (200, 204):
            print(f"[OK] Sent {len(chunk)} embed(s).")
        else:
            print(f"[ERR] Discord {resp.status_code}: {resp.text}")


def main():
    now = datetime.now(UTC8)
    print(f"[INFO] {now.strftime('%A %d %b %Y %H:%M:%S')} UTC+8")

    triggered = []  # (boss, spawn_dt, alert_type)
    upcoming  = get_all_upcoming(hours_ahead=24)

    for spawn in upcoming:
        for alert_min in ALERT_WINDOWS:
            target_dt = spawn["dt"] - timedelta(minutes=alert_min)
            diff = abs((now - target_dt).total_seconds())
            if diff <= TOLERANCE:
                for boss in spawn["bosses"]:
                    triggered.append((boss, spawn["dt"], alert_min))

    if not triggered:
        print("[INFO] Nothing to alert right now.")
        return

    # Send one message per alert level, each with its own embeds
    for alert_type in [15, 5, 0]:
        group = [(b, dt) for (b, dt, at) in triggered if at == alert_type]
        if not group:
            continue

        names  = " & ".join(b for b, _ in group)
        embeds = [build_embed(b, dt, alert_type) for b, dt in group]

        if alert_type == 0:
            content = f"🔴 **{names}** {'is' if len(group) == 1 else 'are'} spawning right now!"
        elif alert_type == 5:
            content = f"⚠️ **{names}** {'spawns' if len(group) == 1 else 'spawn'} in ~5 minutes!"
        else:
            content = f"⏰ **{names}** in ~15 minutes."

        print(f"[ALERT] {alert_type}min — {names}")
        send_embeds(embeds, content=content)


if __name__ == "__main__":
    main()
