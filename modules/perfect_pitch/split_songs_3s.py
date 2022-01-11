# Previously worked when in bot-be-named main directory, might need to edit paths for it being in perfect_pitch module now
import os
from modules.music_race import music_race_constants

if not os.path.exists(
    os.path.join(
        os.getcwd(),
        "modules",
        music_race_constants.MUSIC_RACE_DIR,
        "puzzle_partial_songs",
    )
):
    os.mkdir(
        os.path.join(
            os.getcwd(),
            "modules",
            music_race_constants.MUSIC_RACE_DIR,
            "puzzle_partial_songs",
        )
    )


SPLIT_SONG_LENGTH = 3  # 3 seconds

os.system(
    f"ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t 5 -q:a 9 -acodec libmp3lame {os.path.join(music_race_constants.PUZZLE_PARTIAL_SONGS_DIR, 'silence.mp3')}"
)
for song in music_race_constants.ANSWERS:
    for letter_idx, letter in enumerate(song):
        os.system(
            f"ffmpeg -y -i {os.path.join(music_race_constants.PUZZLE_FULL_SONGS_DIR, song + music_race_constants.MP3_EXTENSION)} -ss {letter_idx * SPLIT_SONG_LENGTH} -to {(letter_idx + 1) * SPLIT_SONG_LENGTH} {os.path.join(music_race_constants.PUZZLE_PARTIAL_SONGS_DIR, song + '_part_' + str(letter_idx) + '.mp3')}"
        )
