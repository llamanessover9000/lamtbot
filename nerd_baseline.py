import csv
from database import db

def load_nerd_baseline():
    with open("nerd_baseline.csv", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_type = row["type"].strip().lower()
            guild_id = int(row["guild_id"])
            count = int(row["count"])

            if row_type == "server":
                db.execute("""
                    INSERT INTO nerd_baseline_server (guild_id, baseline)
                    VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET baseline = ?
                """, (guild_id, count, count))
            
            elif row_type == "channel":
                db.execute("""
                    INSERT INTO nerd_baseline_channel (guild_id, channel_name, baseline)
                    VALUES (?, ?, ?)
                    ON CONFLICT(guild_id, channel_name) DO UPDATE SET baseline = ?
                """, (guild_id, row["identifier"], count, count))
            
            elif row_type == "user":
                db.execute("""
                    INSERT INTO nerd_baseline_user (guild_id, user_id, baseline)
                    VALUES (?, ?, ?)
                    ON CONFLICT(guild_id, user_id) DO UPDATE SET baseline = ?
                """, (guild_id, int(row["identifier"]), count, count))
                
    db.commit()