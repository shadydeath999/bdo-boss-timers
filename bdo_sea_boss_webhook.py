#!/usr/bin/env python3
"""
BDO SEA World Boss Discord Webhook — Persistent Scheduler
===========================================================
- Runs 24/7 as a persistent process (Railway, VPS, etc.)
- Calculates the EXACT next alert time and sleeps until then
- No cron dependency — precise to the second
- Alerts 15 min AND 5 min before each boss spawns, plus spawn announcement
- Full SEA schedule including LOML bosses

SETUP:
  1. Set DISCORD_WEBHOOK_URL env var
  2. pip install requests
  3. python bdo_sea_boss_webhook.py   ← runs forever
"""

import os
import time
import logging
import requests
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "YOUR_DISCORD_WEBHOOK_URL_HERE")

# Alert windows in minutes before spawn
ALERT_WINDOWS = [15, 5, 0]   # 0 = spawning now

# UTC+8 (SEA / Philippine Time / WITA)
UTC8 = timezone(timedelta(hours=8))

# ─────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

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
        "location": "Nouver's Pit (Valencia Desert)",
        "drops":    "Nouver Sub-weapon Box, Hunter Seals, Black Stones",
        "tag":      "classic",
    },
    "Garmoth": {
        "color":    0xC0392B,
        "icon":     "https://mmotimer.com/img/garmoth_big.png",
        "location": "Garmoth's Nest (Drieghan)",
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
    "Bulgasal": {
        "color":    0xE67E22,
        "icon":     "https://mmotimer.com/img/bulgasal_big.png",
        "location": "Land of the Morning Light — Holbon",
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
        "location": "Land of the Morning Light — Tiger Palace",
        "drops":    "Flame of the Primordial ★, Primordial Crystal, Asadal Necklace, Caphras Bundle",
        "tag":      "loml",
    },
    "Golden Pig King": {
        "color":    0xFFD700,
        "icon":     "https://mmotimer.com/img/pig_big.png",
        "location": "Land of the Morning Light — Golden Pig Cave",
        "drops":    "Flame of the Primordial ★, Primordial Crystal, Asadal Belt, Gold Bars",
        "tag":      "loml",
    },
    "Quint": {
        "color":    0x7F8C8D,
        "icon":     "https://mmotimer.com/img/quint_big.png",
        "location": "Quint Hill (northern Mediah)",
        "drops":    "Hunter Seals, Black Stones, Ancient Relic Crystal Shards",
        "tag":      "classic",
    },
    "Muraka": {
        "color":    0x795548,
        "icon":     "https://mmotimer.com/img/muraka_big.png",
        "location": "Muraka's Lair (northern Balenos)",
        "drops":    "Hunter Seals, Black Stones, Ancient Relic Crystal Shards",
        "tag":      "classic",
    },
}

# ─────────────────────────────────────────────
#  SEA BOSS SCHEDULE  (UTC+8 / Philippine Time)
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


# ─────────────────────────────────────────────
#  SCHEDULE BUILDER
# ─────────────────────────────────────────────
def build_alert_queue(from_dt: datetime) -> list:
    """
    Returns a sorted list of all upcoming alert events:
      [(alert_dt, spawn_dt, bosses, alert_min), ...]
    Looks 8 days ahead to always have a full week buffered.
    """
    events = []
    for day_offset in range(9):  # 0..8 days ahead
        date    = from_dt + timedelta(days=day_offset)
        weekday = date.weekday()
        for entry in SEA_SCHEDULE:
            if entry["day"] != weekday:
                continue
            spawn_dt = date.replace(
                hour=entry["hour"], minute=entry["min"],
                second=0, microsecond=0
            )
            for alert_min in ALERT_WINDOWS:
                alert_dt = spawn_dt - timedelta(minutes=alert_min)
                if alert_dt > from_dt:  # only future alerts
                    events.append((alert_dt, spawn_dt, entry["bosses"], alert_min))

    events.sort(key=lambda x: x[0])
    return events


# ─────────────────────────────────────────────
#  DISCORD
# ─────────────────────────────────────────────
def build_embed(boss: str, spawn_dt: datetime, alert_min: int) -> dict:
    info    = BOSS_INFO.get(boss, {})
    is_loml = info.get("tag") == "loml"

    if alert_min == 0:
        title     = f"🔴  {boss} IS SPAWNING NOW!"
        time_line = "**BOSS IS LIVE — Get there NOW!**"
    elif alert_min == 5:
        title     = f"⚠️  {boss} — 5 Minutes!"
        time_line = "Spawning in **~5 minutes**"
    else:
        title     = f"⏰  {boss} — 15 Minutes"
        time_line = "Spawning in **~15 minutes**"

    loml_note = "\n> 🌅 *LOML boss — once-per-week loot*" if is_loml else ""

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


def send_alert(bosses: list, spawn_dt: datetime, alert_min: int):
    embeds = [build_embed(b, spawn_dt, alert_min) for b in bosses]
    names  = " & ".join(bosses)

    if alert_min == 0:
        content = f"🔴 **{names}** {'is' if len(bosses) == 1 else 'are'} spawning right now!"
    elif alert_min == 5:
        content = f"⚠️ **{names}** {'spawns' if len(bosses) == 1 else 'spawn'} in ~5 minutes!"
    else:
        content = f"⏰ **{names}** in ~15 minutes."

    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        log.warning("No webhook URL set — skipping send.")
        log.info(f"  Would send: {content}")
        return

    for i in range(0, len(embeds), 10):
        chunk   = embeds[i:i+10]
        payload = {
            "username":   "BDO SEA Boss Timer",
            "avatar_url": "https://garmoth.com/favicon.ico",
            "embeds":     chunk,
        }
        if content and i == 0:
            payload["content"] = content

        try:
            resp = requests.post(
                DISCORD_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if resp.status_code in (200, 204):
                log.info(f"[SENT] {alert_min}min alert — {names}")
            else:
                log.error(f"[ERR] Discord {resp.status_code}: {resp.text}")
        except requests.RequestException as e:
            log.error(f"[ERR] Request failed: {e}")


# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
def main():
    log.info("BDO SEA Boss Timer started (persistent scheduler)")
    log.info("Timezone: UTC+8 (Philippine Time / WITA)")

    while True:
        now   = datetime.now(UTC8)
        queue = build_alert_queue(from_dt=now)

        if not queue:
            log.warning("Queue empty — sleeping 60s and retrying.")
            time.sleep(60)
            continue

        # Grab the very next alert
        alert_dt, spawn_dt, bosses, alert_min = queue[0]
        sleep_secs = (alert_dt - now).total_seconds()

        label = f"{', '.join(bosses)} ({alert_min}min alert)"
        log.info(f"Next: {label} at {alert_dt.strftime('%a %d %b %H:%M:%S')} — sleeping {sleep_secs:.1f}s")

        # Sleep until exactly the right moment
        if sleep_secs > 0:
            time.sleep(sleep_secs)

        # Fire the alert
        now_check = datetime.now(UTC8)
        drift     = abs((now_check - alert_dt).total_seconds())
        log.info(f"Firing alert (drift: {drift:.2f}s) — {label}")
        send_alert(bosses, spawn_dt, alert_min)

        # Small buffer to avoid re-triggering the same event
        time.sleep(2)


if __name__ == "__main__":
    main()
