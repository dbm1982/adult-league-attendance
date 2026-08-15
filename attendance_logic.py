import datetime
from zoneinfo import ZoneInfo

eastern = ZoneInfo("America/New_York")

def save_attendance(sheet, updates):

    attendance_sheet = sheet.worksheet("Attendance")
    rows = attendance_sheet.get_all_records()

    lookup = {(row["player_id"], row["game_id"]): i for i, row in enumerate(rows)}

    for update in updates:
        key = (update["player_id"], update["game_id"])
        if key in lookup:
            idx = lookup[key]
            rows[idx]["status"] = update["status"]
            rows[idx]["updated_at"] = datetime.datetime.now(eastern).isoformat()
        else:
            rows.append({
                "player_id": update["player_id"],
                "game_id": update["game_id"],
                "status": update["status"],
                "updated_at": datetime.datetime.now(eastern).isoformat()
            })

    headers = ["player_id", "game_id", "status", "updated_at"]
    output = [headers] + [[row[h] for h in headers] for row in rows]

    attendance_sheet.update(output)

    return True
