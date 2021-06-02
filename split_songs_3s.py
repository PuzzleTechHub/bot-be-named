import os

BASE_DIR = os.path.join(os.getcwd(), 'modules/music_race/puzzle_songs/')
songs = ["JAMESBOND", "FROZEN", "HARRYPOTTER", "ROCKY", "XMEN", "INDIANAJONES", "STARWARS", "MOANA", "TITANIC", "AVENGERS"]

delays = [6, 3, 8, 3, 2, 3, 2, 2, 5, 3]

SPLIT_SONG_LENGTH = 3 # 3 seconds

for delay, song in zip(delays, songs):
    os.system(
        f"ffmpeg -y -i {BASE_DIR}{song}.mp3 -filter_complex 'adelay={delay*1000}|{delay*1000}' {os.path.join(BASE_DIR, song + '_final.mp3')}"
    )

    for letter_idx, letter in enumerate(song):
        os.system(
            f"ffmpeg -y -i {os.path.join(BASE_DIR, song + '.mp3')} -ss {letter_idx * SPLIT_SONG_LENGTH} -to {(letter_idx + 1) * SPLIT_SONG_LENGTH} {os.path.join(BASE_DIR, song + '_part_' + str(letter_idx) + '.mp3')}")
