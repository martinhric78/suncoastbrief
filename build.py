#!/usr/bin/env python3
"""The Suncoast Brief — nightly assembly robot.
Fetches tomorrow's real weather (National Weather Service), real tide times (NOAA),
and fresh local headlines (Google News RSS), then patches them into index.html
between HTML comment markers. Run with --weather-only for the 4:30 AM refresh.

All data sources are free and require no API keys.
"""
import re, sys, json, datetime, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ET_TZ = ZoneInfo("America/New_York")
UA = {"User-Agent": "SuncoastBrief/1.0 (suncoastbrief.com; contact: tampasarasotahandyman@gmail.com)"}

COAST = (27.771, -82.407)   # Apollo Beach
INLAND = (27.937, -82.286)  # Brandon
NOAA_STATION = "8726520"     # St. Petersburg, Tampa Bay

def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def patch(html, tag, new_inner):
    pat = re.compile(r"(<!--%s-->).*?(<!--/%s-->)" % (tag, tag), re.DOTALL)
    if not pat.search(html):
        print(f"  ! marker {tag} not found — skipped"); return html
    return pat.sub(lambda m: m.group(1) + new_inner + m.group(2), html, count=1)

def pick_emoji(short, pop):
    s = short.lower()
    if "thunder" in s or "storm" in s: return "⛈️"
    if "rain" in s or "shower" in s: return "🌧️"
    if "partly" in s or "mostly sunny" in s: return "⛅"
    if "cloud" in s: return "☁️"
    if pop and pop >= 50: return "🌦️"
    return "☀️"

def nws_tomorrow(lat, lon):
    """Return (high_temp, short_forecast, pop%) for tomorrow's daytime period."""
    meta = json.loads(get(f"https://api.weather.gov/points/{lat},{lon}"))
    fc = json.loads(get(meta["properties"]["forecast"]))
    tomorrow = (datetime.datetime.now(ET_TZ) + datetime.timedelta(days=1)).date()
    for p in fc["properties"]["periods"]:
        start = datetime.datetime.fromisoformat(p["startTime"]).astimezone(ET_TZ)
        if p["isDaytime"] and start.date() == tomorrow:
            pop = (p.get("probabilityOfPrecipitation") or {}).get("value") or 0
            return p["temperature"], p["shortForecast"], pop
    p = fc["properties"]["periods"][0]
    pop = (p.get("probabilityOfPrecipitation") or {}).get("value") or 0
    return p["temperature"], p["shortForecast"], pop

def sun_times(lat, lon, date):
    data = json.loads(get(
        f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date={date.isoformat()}&formatted=0"))
    def loc(iso):
        t = datetime.datetime.fromisoformat(iso).astimezone(ET_TZ)
        return t.strftime("%-I:%M") + ("a" if t.hour < 12 else "p")
    return loc(data["results"]["sunrise"]), loc(data["results"]["sunset"])

def noaa_tides(date):
    d = date.strftime("%Y%m%d")
    url = ("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
           f"product=predictions&datum=MLLW&station={NOAA_STATION}"
           f"&time_zone=lst_ldt&units=english&interval=hilo&format=json"
           f"&begin_date={d}&end_date={d}")
    data = json.loads(get(url))
    parts = []
    for p in data.get("predictions", []):
        t = datetime.datetime.strptime(p["t"], "%Y-%m-%d %H:%M")
        label = "High" if p["type"] == "H" else "Low"
        parts.append(f"{label} {t.strftime('%-I:%M %p').lower()}")
    return " · ".join(parts)

def news_items(max_items=4):
    q = urllib.parse.quote('"Riverview FL" OR "Brandon FL" OR "Apollo Beach" OR "Ruskin FL" OR "Hillsborough County"')
    xml = get(f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en")
    root = ET.fromstring(xml)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if not title or not link: continue
        title = re.sub(r"\s+-\s+[^-]+$", "", title)  # strip trailing "- Source"
        if len(title) > 110: title = title[:107] + "…"
        items.append((title, link))
        if len(items) >= max_items: break
    return items

def main():
    weather_only = "--weather-only" in sys.argv
    tomorrow = (datetime.datetime.now(ET_TZ) + datetime.timedelta(days=1)).date()
    target = datetime.datetime.now(ET_TZ).date() if weather_only else tomorrow

    with open("index.html") as f:
        html = f.read()

    # ---- Weather (both zones) ----
    try:
        c_t, c_s, c_p = nws_tomorrow(*COAST)
        i_t, i_s, i_p = nws_tomorrow(*INLAND)
        html = patch(html, "CTMP", f"{c_t}°")
        html = patch(html, "CDESC", c_s + ".")
        html = patch(html, "CEMO", pick_emoji(c_s, c_p))
        html = patch(html, "ITMP", f"{i_t}°")
        html = patch(html, "IDESC", i_s + ".")
        html = patch(html, "IEMO", pick_emoji(i_s, i_p))
        rain = max(c_p or 0, i_p or 0)
        html = patch(html, "RAIN", f"{rain}%")
        hot = max(c_t, i_t)
        if rain >= 60:
            note = f"<b>The take:</b> Storms are likely — get outdoor plans done early, then let the rain cool things off. Highs near {hot}°."
        elif hot >= 92:
            note = f"<b>The take:</b> A hot one — {hot}° inland. Morning is your window; hydrate and check the back seat every single time you park."
        else:
            note = f"<b>The take:</b> A pleasant Suncoast day, highs around {hot}°. Get outside and enjoy it."
        html = patch(html, "WXNOTE", note)
        if hot >= 95 or rain >= 80:
            alert = ("Heat advisory conditions — hydrate and check on older neighbors." if hot >= 95
                     else "Strong storms likely today — secure loose patio items and drive with care.")
        else:
            alert = "Good morning! No weather alerts today — it's a beautiful day on the Suncoast. ☀️"
        html = patch(html, "ALERT", alert)
        print(f"  weather ok: coast {c_t}° / inland {i_t}° / rain {rain}%")
    except Exception as e:
        print("  ! weather fetch failed, keeping previous:", e)

    # ---- Sunrise / sunset ----
    try:
        sr, ss = sun_times(*COAST, target)
        html = patch(html, "SUNRISE", sr)
        html = patch(html, "SUNSET", ss)
        print(f"  sun ok: {sr} / {ss}")
    except Exception as e:
        print("  ! sun fetch failed:", e)

    # ---- Tides ----
    try:
        tides = noaa_tides(target)
        if tides:
            html = patch(html, "TIDES",
                f"<span class='cl'>Today's tides (St. Pete station):</span> {tides}. "
                "Fish the moving water around the changes — dawn and dusk beat the heat.")
            print("  tides ok:", tides)
    except Exception as e:
        print("  ! tides fetch failed:", e)

    # ---- Headlines (nightly build only) ----
    if not weather_only:
        try:
            items = news_items()
            if items:
                lis = "\n".join(
                    f'        <li>{t} <a href="{l}" style="color:#1a7fa8">source</a></li>'
                    for t, l in items)
                html = patch(html, "HEADLINES", "\n" + lis + "\n")
                print(f"  headlines ok: {len(items)} items")
        except Exception as e:
            print("  ! headlines fetch failed, keeping previous:", e)

    with open("index.html", "w") as f:
        f.write(html)
    print("build complete for", target.isoformat())

if __name__ == "__main__":
    main()
