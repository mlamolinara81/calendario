"""Genera calendario.ics da eventi.json.
Ogni evento: {"titolo", "inizio": "2026-11-20T10:00", "fine": "2026-11-20T11:00" (opz.),
"luogo" (opz.), "note" (opz.), "tutto_il_giorno": false (opz.), "id" (opz.),
"promemoria_minuti": [30] (opz., minuti prima dell'inizio)}"""
import json, sys, hashlib, datetime as dt
from pathlib import Path
base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
eventi = json.loads((base / "eventi.json").read_text(encoding="utf-8"))
def esc(s): return str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
def fold(line):
    out, b = [], line.encode()
    while len(b) > 75:
        cut = 75
        while (b[cut] & 0xC0) == 0x80: cut -= 1
        out.append(b[:cut].decode()); b = b" " + b[cut:]
    out.append(b.decode()); return "\r\n".join(out)
now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Mose//Calendario//IT", "CALSCALE:GREGORIAN",
     "METHOD:PUBLISH", "X-WR-CALNAME:Appuntamenti", "X-WR-TIMEZONE:Europe/Rome",
     "REFRESH-INTERVAL;VALUE=DURATION:PT1H", "X-PUBLISHED-TTL:PT1H",
     "BEGIN:VTIMEZONE", "TZID:Europe/Rome",
     "BEGIN:DAYLIGHT", "TZOFFSETFROM:+0100", "TZOFFSETTO:+0200", "TZNAME:CEST", "DTSTART:19700329T020000", "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU", "END:DAYLIGHT",
     "BEGIN:STANDARD", "TZOFFSETFROM:+0200", "TZOFFSETTO:+0100", "TZNAME:CET", "DTSTART:19701025T030000", "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU", "END:STANDARD",
     "END:VTIMEZONE"]
for e in eventi:
    uid = e.get("id") or hashlib.sha1((e["titolo"] + e["inizio"]).encode()).hexdigest()[:16]
    L += ["BEGIN:VEVENT", f"UID:{uid}@calendario-mose", f"DTSTAMP:{now}", "SUMMARY:" + esc(e["titolo"])]
    if e.get("tutto_il_giorno"):
        d = dt.date.fromisoformat(e["inizio"][:10]); f = dt.date.fromisoformat(e.get("fine", e["inizio"])[:10]) + dt.timedelta(days=1)
        L += [f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{f:%Y%m%d}"]
    else:
        i = dt.datetime.fromisoformat(e["inizio"]); f = dt.datetime.fromisoformat(e["fine"]) if e.get("fine") else i + dt.timedelta(hours=1)
        L += [f"DTSTART;TZID=Europe/Rome:{i:%Y%m%dT%H%M%S}", f"DTEND;TZID=Europe/Rome:{f:%Y%m%dT%H%M%S}"]
    if e.get("luogo"): L.append("LOCATION:" + esc(e["luogo"]))
    if e.get("note"): L.append("DESCRIPTION:" + esc(e["note"]))
    prom = e.get("promemoria_minuti", [] if e.get("tutto_il_giorno") else [30])
    for m in prom:
        L += ["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + esc(e["titolo"] + (" - " + e["note"] if e.get("note") else "")), f"TRIGGER:-PT{int(m)}M", "END:VALARM"]
    L.append("END:VEVENT")
L.append("END:VCALENDAR")
(base / "calendario.ics").write_text("\r\n".join(fold(x) for x in L) + "\r\n", encoding="utf-8")
print(f"{len(eventi)} eventi scritti")
