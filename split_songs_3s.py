import os

BASE_DIR = '/home/kevin/Development/bot-be-named/modules/perfect_pitch/music/puzzle_songs/'
songs = ['frozen', 'starwars', 'rocky', 'xmen', 'titanic', 'harrypotter', 'jamesbond', 'lionking', 'avengers']

delays = [3, 2, 3, 2, 7, 1, 7, 2, 7]

for delay, song in zip(delays, songs):
    os.system(
        f"ffmpeg -y -i {BASE_DIR}{song}.mp3 -filter_complex 'adelay={delay*1000}|{delay*1000}' {BASE_DIR}{song}_final.mp3"
    )
    #letter_offset = 0
    #if delay > 2:  # Need to have entire parts just of silence
    for letter_idx, letter in enumerate(song):
        os.system(
            f"ffmpeg -y -i {BASE_DIR}{song}.mp3 -ss {letter_idx * 3} -to {(letter_idx + 1) * 3} {BASE_DIR}{song}_part_{letter_idx}.mp3")

        #if letter_idx == 0:
            #os.system(f"ffmpeg -y -i {BASE_DIR}{path} -ss 0 -to {(letter_idx+1)*3 - delay} -af 'adelay={delay*1000}|{delay*1000}' {BASE_DIR}{song}_part_{letter_idx}.mp3")
        #else:

