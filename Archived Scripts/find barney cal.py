def list_venue_subcalendars(BASE_URL, CALENDAR_KEY, HEADERS):
    url = f"{BASE_URL}/{CALENDAR_KEY}/subcalendars"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    subs = resp.json().get("subcalendars", [])
    result = []
    for sc in subs:
        name = sc.get("name", "")
        # your naming convention: e.g. "Venue > Gym A"
        if name.startswith("Venue >"):
            tg = name.rsplit(">", 1)[1].strip()
        else:
            tg = None
        result.append({
            "id": sc["id"],
            "Venue": tg
        })
    return result

    