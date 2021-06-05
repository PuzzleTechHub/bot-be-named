
# We need our notes to be either natural or flat to match the dataset.
CLEANED_NOTES = {
    'R': 'R',  # REST
    'Cb': 'B',
    'C': 'C',
    'C#': 'Db',
    'Db': 'Db',
    'D': 'D',
    'D#': 'Eb',
    'Eb': 'Eb',
    'E': 'E',
    'E#': 'F',
    'Fb': 'E',
    'F': 'F',
    'F#': 'Gb',
    'Gb': 'Gb',
    'G': 'G',
    'G#': 'Ab',
    'Ab': 'Ab',
    'A': 'A',
    'A#': 'Bb',
    'Bb': 'Bb',
    'B': 'B',
    'B#': 'C'
}

DURATIONS = {
    'wd': 6,
    'w': 4,
    'hd': 3,
    'h': 2,
    'qd': 1.5,
    'q': 1,
    'ed': 0.75,
    'e': 0.5,
    'sd': 0.375,
    's': 0.25,
    't': 0.33
}

REST = "R"

# DIRECTORIES
MUSIC = "music"
NOTES = "notes"
CHORDS = "chords"
TUNES = "tunes"
PUZZLE_SONGS = "puzzle_partial_songs"
PUZZLE_OUTPUTS = "puzzle_outputs"
PERFECT_PITCH_DIR = "perfect_pitch"

# INSTRUMENTS
PIANO = "piano"
XYLOPHONE = "xylophone"
MARIMBA = "marimba"

# FFMPEG formatting
MAX_PARTITION_SIZE = 25  # Absolute max is 26
VOLUME = 11
