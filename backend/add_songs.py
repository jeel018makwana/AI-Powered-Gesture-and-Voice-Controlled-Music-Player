import sys
import os

# Project root ko Python path me add karo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import app, db
from backend.models import Song

# ✅ YAHI MAIN CHANGE
SONG_FOLDER = os.path.join(os.path.dirname(__file__), "music")

with app.app_context():

    if not os.path.exists(SONG_FOLDER):
        print("❌ music folder exist hi nahi karta:", SONG_FOLDER)
        exit()

    files = os.listdir(SONG_FOLDER)

    count = 0

    for file in files:
        if file.endswith(".mp3"):

            already = Song.query.filter_by(title=file).first()
            if already:
                print("⏩ Already in DB:", file)
                continue

            song = Song(
                title=file,
                file_path=f"music/{file}"   # ✅ yaha bhi change
            )

            db.session.add(song)
            count += 1

    db.session.commit()

    print(f"✅ {count} new songs added to database")
