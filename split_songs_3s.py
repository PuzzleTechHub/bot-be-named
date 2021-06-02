import os
from modules.music_race import music_race_constants


SPLIT_SONG_LENGTH = 3 # 3 seconds

for song in music_race_constants.ANSWERS:
    for letter_idx, letter in enumerate(song):
        os.system(
            f"ffmpeg -y -i {os.path.join(music_race_constants.PUZZLE_FULL_SONGS_DIR, song + music_race_constants.MP3_EXTENSION)} -ss {letter_idx * SPLIT_SONG_LENGTH} -to {(letter_idx + 1) * SPLIT_SONG_LENGTH} {os.path.join(music_race_constants.PUZZLE_PARTIAL_SONGS_DIR, song + '_part_' + str(letter_idx) + '.mp3')}")
