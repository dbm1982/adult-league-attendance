import datetime

# ---------------------------------------------------------
# SAVE ATTENDANCE (batch update)
# ---------------------------------------------------------

def save_attendance(sheet, updates):
    """
    Saves attendance updates in a single batch.
    'updates' is a list of dictionaries:
    [
        {
            "player_id": "...",
            "game_id": "...",
            "status": "...",
        },
        ...
    ]
    """

    attendance_sheet = sheet.worksheet("Attendance")
    rows = attendance_sheet.get_all_records()

    # Convert rows into a lookup dictionary for fast updates
    lookup = {(row["player_id"], row["game_id"]): i for i, row in enumerate(rows)}

    # Apply updates
    for update in updates:
        key = (update["player_id"], update["game_id"])
        if key in lookup:
            idx = lookup[key]
            rows[idx]["status"] = update["status"]
            rows[idx]["updated_at"] = datetime.datetime.now().isoformat()
        else:
            # New row (if needed)
            rows.append({
                "player_id": update["player_id"],
                "game_id": update["game_id"],
                "status": update["status"],
                "updated_at": datetime.datetime.now().isoformat()
            })

    # Write back to sheet
    headers = ["player_id", "game_id", "status", "updated_at"]
    output = [headers] + [[row[h] for h in headers] for row in rows]

    attendance_sheet.update(output)

    return True
