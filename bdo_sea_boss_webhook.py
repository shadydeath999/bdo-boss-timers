#!/usr/bin/env python3
"""
BDO SEA World Boss Discord Webhook
====================================
Sends upcoming world boss alerts to a Discord channel via webhook.
Data is based on the official SEA server schedule (UTC+8 / WITA).

HOW TO USE:
  1. Set your DISCORD_WEBHOOK_URL below (or as an env var).
  2. Optionally set ALERT_MINUTES to how many minutes before spawn to alert.
  3. Run manually:           python bdo_sea_boss_webhook.py
  4. Run on a cron (every minute is ideal):
       * * * * *  /usr/bin/python3 /path/to/bdo_sea_boss_webhook.py

REQUIREMENTS:
  pip install requests
"""

import os
import json
import requests
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "YOUR_DISCORD_WEBHOOK_URL_HERE")

# Fire an alert this many minutes before a boss spawns.
# Set to 30 to match the GitHub Actions cron interval.
ALERT_MINUTES = 30

# How wide the trigger window is (in seconds).
# 900 = ±15 min window, safe for GitHub Actions which may run slightly late.
TRIGGER_WINDOW_SECONDS = 900

# ─────────────────────────────────────────────
#  BOSS IMAGES  (official Garmoth / BDO assets)
# ─────────────────────────────────────────────
BOSS_ICONS = {
    "Kzarka":   "https://mmotimer.com/img/kzarka_big.png",
    "Karanda":  "https://mmotimer.com/img/karanda_big.png",
    "Kutum":    "https://mmotimer.com/img/kutum_big.png",
    "Nouver":   "https://mmotimer.com/img/nouver_big.png",
    "Garmoth":  "https://mmotimer.com/img/garmoth_big.png",
    "Offin":    "https://mmotimer.com/img/offin_big.png",
    "Vell":     "https://mmotimer.com/img/vell_big.png",
    "Quint":    "https://mmotimer.com/img/quint_big.png",
    "Muraka":   "https://mmotimer.com/img/muraka_big.png",
    "Bulgasal": "https://mmotimer.com/img/bulgasal_big.png",
    "Uturi":    "https://mmotimer.com/img/uturi_big.png",
    "Sangoon":  "https://mmotimer.com/img/sangoon_big.png",
}

BOSS_COLORS = {
    "Kzarka":   0xE74C3C,   # red
    "Karanda":  0x9B59B6,   # purple
    "Kutum":    0xF39C12,   # orange
    "Nouver":   0x3498DB,   # blue
    "Garmoth":  0xE74C3C,   # red (dragon)
    "Offin":    0x2ECC71,   # green
    "Vell":     0x1ABC9C,   # teal
    "Quint":    0x95A5A6,   # grey
    "Muraka":   0x795548,   # brown
    "Bulgasal": 0xE67E22,   # dark orange
    "Uturi":    0xF1C40F,   # yellow
    "Sangoon":  0xE91E63,   # pink
}

BOSS_LOCATIONS = {
    "Kzarka":   "Serendia Temple (south of Heidel)",
    "Karanda":  "Karanda Ridge (northeast Calpheon)",
    "Kutum":    "Kutum Cave (Valencia Desert)",
    "Nouver":   "Nouver's Pit (Valencia Desert) — Bring desert potions!",
    "Garmoth":  "Garmoth's Nest (Drieghan) — Destroy statues first!",
    "Offin":    "Holo Forest (Kamasylvia)",
    "Vell":     "Vell's Realm (open ocean north of Lema Island) — Bring a ship!",
    "Quint":    "Quint Hill (northwest Calpheon)",
    "Muraka":   "West of Mansha Forest / Lake Kaia (Calpheon)",
    "Bulgasal": "Land of the Morning Light",
    "Uturi":    "Land of the Morning Light",
    "Sangoon":  "Land of the Morning Light",
}

BOSS_DROPS = {
    "Kzarka":   "Kzarka Main Weapon Box, Hunter Seals, Black Stones",
    "Karanda":  "Dandelion Awakening Weapon Box, Hunter Seals, Black Stones",
    "Kutum":    "Kutum Sub-weapon Box, Hunter Seals, Black Stones",
    "Nouver":   "Nouver Sub-weapon Box, Hunter Seals, Black Stones",
    "Garmoth":  "Garmoth's Heart (rare!), Garmoth Scales, Garmoth's Horn",
    "Offin":    "Offin Tett Weapon Box, Valtarra's Eclipsed Belt",
    "Vell":     "Vell's Heart, Gold Bars, Accessories",
    "Quint":    "Hunter Seals, Cron Stones, Silver",
    "Muraka":   "Hunter Seals, Cron Stones, Silver",
    "Bulgasal": "Primordial Weapon materials, Asadal Accessories",
    "Uturi":    "Primordial Weapon materials, Asadal Accessories",
    "Sangoon":  "Primordial Weapon materials, Asadal Accessories",
}

# ─────────────────────────────────────────────
#  SEA BOSS SCHEDULE  (times in UTC+8 / WITA)
#  Source: Garmoth.com / mmotimer.com SEA server
#  day: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
# ─────────────────────────────────────────────
SEA_SCHEDULE = [
    # Monday
    {"day": 0, "hour":  0, "min": 0,  "bosses": ["Kutum", "Nouver"]},
    {"day": 0, "hour":  1, "min": 30, "bosses": ["Kutum"]},
    {"day": 0, "hour": 11, "min": 0,  "bosses": ["Kzarka", "Nouver"]},
    {"day": 0, "hour": 15, "min": 0,  "bosses": ["Kutum", "Nouver"]},
    {"day": 0, "hour": 20, "min": 0,  "bosses": ["Kzarka", "Karanda"]},
    # Tuesday
    {"day": 1, "hour":  0, "min": 0,  "bosses": ["Offin"]},
    {"day": 1, "hour":  1, "min": 30, "bosses": ["Nouver"]},
    {"day": 1, "hour": 11, "min": 0,  "bosses": ["Kutum", "Karanda"]},
    {"day": 1, "hour": 15, "min": 0,  "bosses": ["Kutum", "Kzarka"]},
    {"day": 1, "hour": 20, "min": 0,  "bosses": ["Quint", "Muraka"]},
    # Wednesday
    {"day": 2, "hour":  0, "min": 0,  "bosses": ["Garmoth"]},
    {"day": 2, "hour":  1, "min": 30, "bosses": ["Kzarka", "Offin"]},
    {"day": 2, "hour": 11, "min": 0,  "bosses": ["Nouver", "Kutum"]},
    {"day": 2, "hour": 15, "min": 0,  "bosses": ["Karanda", "Kzarka"]},
    {"day": 2, "hour": 20, "min": 0,  "bosses": ["Kutum", "Nouver"]},
    # Thursday
    {"day": 3, "hour":  0, "min": 0,  "bosses": ["Vell"]},
    {"day": 3, "hour":  1, "min": 30, "bosses": ["Kutum"]},
    {"day": 3, "hour": 11, "min": 0,  "bosses": ["Karanda", "Kzarka"]},
    {"day": 3, "hour": 15, "min": 0,  "bosses": ["Kutum", "Nouver"]},
    {"day": 3, "hour": 20, "min": 0,  "bosses": ["Karanda", "Nouver"]},
    # Friday
    {"day": 4, "hour":  0, "min": 0,  "bosses": ["Garmoth"]},
    {"day": 4, "hour":  1, "min": 30, "bosses": ["Nouver"]},
    {"day": 4, "hour": 11, "min": 0,  "bosses": ["Kutum", "Kzarka"]},
    {"day": 4, "hour": 15, "min": 0,  "bosses": ["Karanda", "Kzarka"]},
    {"day": 4, "hour": 20, "min": 0,  "bosses": ["Nouver", "Kutum"]},
    # Saturday
    {"day": 5, "hour":  0, "min": 0,  "bosses": ["Offin"]},
    {"day": 5, "hour":  1, "min": 30, "bosses": ["Karanda"]},
    {"day": 5, "hour": 11, "min": 0,  "bosses": ["Kutum", "Kzarka"]},
    {"day": 5, "hour": 15, "min": 0,  "bosses": ["Karanda", "Nouver"]},
    {"day": 5, "hour": 16, "min": 0,  "bosses": ["Garmoth"]},
    {"day": 5, "hour": 20, "min": 0,  "bosses": ["Quint", "Muraka"]},
    # Sunday
    {"day": 6, "hour":  1, "min": 30, "bosses": ["Kzarka"]},
    {"day": 6, "hour": 11, "min": 0,  "bosses": ["Nouver", "Karanda"]},
    {"day": 6, "hour": 15, "min": 0,  "bosses": ["Kutum", "Karanda"]},
    {"day": 6, "hour": 16, "min": 0,  "bosses": ["Vell"]},
    {"day": 6, "hour": 20, "min": 0,  "bosses": ["Kzarka", "Karanda"]},
]

# UTC+8 timezone
UTC8 = timezone(timedelta(hours=8))


def get_next_spawns(limit=5):
    """Return the next N upcoming boss spawns from now (in UTC+8)."""
    now = datetime.now(UTC8)
    upcoming = []

    # Check the next 14 days to ensure we find enough entries
    for day_offset in range(14):
        check_date = now + timedelta(days=day_offset)
        weekday = check_date.weekday()  # 0=Mon ... 6=Sun

        for entry in SEA_SCHEDULE:
            if entry["day"] != weekday:
                continue
            spawn_dt = check_date.replace(
                hour=entry["hour"], minute=entry["min"], second=0, microsecond=0
            )
            if spawn_dt > now:
                upcoming.append({"dt": spawn_dt, "bosses": entry["bosses"]})

        if len(upcoming) >= limit * 2:
            break

    # Sort and deduplicate
    upcoming.sort(key=lambda x: x["dt"])
    return upcoming[:limit]


def build_embeds(spawns, alert_minutes):
    """Build Discord embed objects for each upcoming spawn."""
    embeds = []
    for spawn in spawns:
        bosses = spawn["bosses"]
        dt = spawn["dt"]
        now = datetime.now(UTC8)
        delta = dt - now
        mins_until = int(delta.total_seconds() // 60)

        for boss in bosses:
            color = BOSS_COLORS.get(boss, 0x95A5A6)
            icon  = BOSS_ICONS.get(boss, "")
            loc   = BOSS_LOCATIONS.get(boss, "Unknown Location")
            drops = BOSS_DROPS.get(boss, "Various items")

            if mins_until <= 0:
                time_str = "🔴 **SPAWNING NOW!**"
            elif mins_until < 60:
                time_str = f"⏰ in **{mins_until} min**"
            else:
                hours = mins_until // 60
                mins  = mins_until % 60
                time_str = f"⏰ in **{hours}h {mins}m**"

            spawn_time_str = dt.strftime("%A %d %b — %H:%M (UTC+8)")

            embed = {
                "title": f"⚔️  {boss}",
                "description": (
                    f"{time_str}\n"
                    f"🕐 **Spawn:** {spawn_time_str}\n"
                    f"📍 **Location:** {loc}\n"
                    f"🎁 **Notable Drops:** {drops}"
                ),
                "color": color,
                "thumbnail": {"url": icon},
                "footer": {
                    "text": "BDO SEA • Data via Garmoth.com  |  garmoth.com/boss-timer",
                    "icon_url": "https://garmoth.com/favicon.ico",
                },
                "timestamp": dt.isoformat(),
            }
            embeds.append(embed)

    return embeds


def send_webhook(embeds):
    """POST embeds to the Discord webhook. Discord allows max 10 embeds per call."""
    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("[WARN] No webhook URL set. Set DISCORD_WEBHOOK_URL env var or edit the script.")
        print("[INFO] Embed payload preview:")
        print(json.dumps(embeds, indent=2, default=str))
        return

    # Discord: max 10 embeds per message
    for i in range(0, len(embeds), 10):
        chunk = embeds[i:i+10]
        payload = {
            "username": "BDO SEA Boss Timer",
            "avatar_url": "https://garmoth.com/favicon.ico",
            "embeds": chunk,
        }
        resp = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code in (200, 204):
            print(f"[OK] Sent {len(chunk)} embed(s) to Discord.")
        else:
            print(f"[ERROR] Discord returned {resp.status_code}: {resp.text}")


def main():
    now = datetime.now(UTC8)
    print(f"[INFO] Current time (UTC+8): {now.strftime('%A %d %b %Y %H:%M:%S')}")

    # ── Mode 1: CRON / live alert
    #    Only fire if a boss is spawning within ALERT_MINUTES (±TRIGGER_WINDOW_SECONDS)
    # ── Mode 2: Manual / on-demand
    #    Always print the next 5 upcoming bosses
    spawns = get_next_spawns(limit=10)

    if not spawns:
        print("[INFO] No upcoming spawns found.")
        return

    # Filter to only those triggering RIGHT NOW (for cron mode)
    target_dt = now + timedelta(minutes=ALERT_MINUTES)
    trigger_spawns = [
        s for s in spawns
        if abs((s["dt"] - target_dt).total_seconds()) <= TRIGGER_WINDOW_SECONDS
    ]

    if trigger_spawns:
        print(f"[ALERT] {len(trigger_spawns)} spawn(s) in ~{ALERT_MINUTES} min. Sending alert...")
        embeds = build_embeds(trigger_spawns, ALERT_MINUTES)
        send_webhook(embeds)
    else:
        # On-demand run: show next 5 bosses as a schedule digest
        print("[INFO] No imminent spawns. Sending upcoming schedule digest...")
        digest_spawns = spawns[:5]
        embeds = build_embeds(digest_spawns, ALERT_MINUTES)

        # Add a header embed
        upcoming_lines = []
        for s in digest_spawns:
            boss_names = " & ".join(s["bosses"])
            upcoming_lines.append(
                f"• **{boss_names}** — {s['dt'].strftime('%a %H:%M')}"
            )

        header_embed = {
            "title": "🗓️  BDO SEA — Upcoming World Bosses",
            "description": "\n".join(upcoming_lines),
            "color": 0xFFD700,
            "footer": {
                "text": "All times UTC+8 (WITA) • garmoth.com/boss-timer",
                "icon_url": "https://garmoth.com/favicon.ico",
            },
            "timestamp": now.isoformat(),
        }
        send_webhook([header_embed] + embeds)


if __name__ == "__main__":
    main()
