import os
import constants

MUSIC_RACE_DIR = "music_race"
PUZZLE_OUTPUTS_DIR = os.path.join(os.getcwd(), constants.MODULES_DIR, MUSIC_RACE_DIR, "puzzle_outputs")
PUZZLE_PARTIAL_SONGS_DIR = os.path.join(os.getcwd(), constants.MODULES_DIR, MUSIC_RACE_DIR, "puzzle_partial_songs")
PUZZLE_FULL_SONGS_DIR = os.path.join(os.getcwd(), constants.MODULES_DIR, MUSIC_RACE_DIR, "puzzle_full_songs")
MP3_EXTENSION = ".mp3"

SONG_SNIPPET_LENGTH = 3
VOLUME = 11

DELAY = "delay"
TUNE = "tune"
ANSWERS = {
    "JAMESBOND": {
        DELAY: 6,
        TUNE: "~playtune R R R R R R m=1 o=4 B3h Ch C#h Ch B3h Ch C#h Ch Ee F#s F#s F#e F# Ee Ee Ee Ee Gs Gs Ge G F#e F#e F#e Ee F#s F#s F#e F# Ee Ee Ee Ee Gs Gs Ge G F#e F#e F#e Ee F#s F#s F#e F# Ee Ee Ee Ee Gs Gs Ge G F#e F#e Ee D#5e D5h Be Ae Bh Ee F#s F#s F#e F# Ee Ee Ee Ee Gs Gs Ge G",
    },
    "WIZARDOFOZ": {
        DELAY: 7,
        TUNE: "~playtune R R R R R R R m=1 o=4 Ebh Eb5h D5 Bbe C5e D5 Eb5 Ebh C5h Bbw Ch Abh G Ebe Fe G Ab F De Ebe F G Ebh Re Bbe Ge Bbe Ge Bbe Ge Bbe Ge Bbe Abe Bbe Abe Bbe Abe Bbe Abe Bbe C5h C5w Re Bbe Ge Bbe Ge Bbe Ge Bbe Ge Bbe Ae C5e Ae C5e Ae C5e Ae C5e D5h D5h F5h C5h Ebh Eb5h D5 Bbe C5e D5 Eb5 Ebh C5h Bbw Ch Abh G Ebe Fe G Ab F De Ebe F G Ebw",
    },
    "HARRYPOTTER": {
        DELAY: 8,
        TUNE: "~playtune R R R R R R R R i=marimba m=1.3 o=4 E Aqd C5e B Ah E5 D5hd Bhd Aqd C5e B Gh A Ew E Aqd C5e B Ah E5 G5h Gb5 F5h D5 F5qd E5e D#5 Eh C5 Aw C5 E5h C5 E5h C5 F5h E5 D#5h D#5 E5qd C5e A D#h E E5w C5 E5h C5 E5h C5 G5h Gb5 F5h Db5 F5qd E5e D#5 D#h C5 Aw",
    },
    "TITANIC": {
        DELAY: 7,
        TUNE: "~playtune R R R R R R R m=1 o=4 Fe Ge Ge Ah Ge Fe Ge C5h Bbe Ae Fhd R Fe Ge Ahd Bbs As Gs Fs Ge C5h Ae C5e D5h C5h Gh Rh Fqd Fe F F E Fh F E Fh G Ah Gh Fqd Fe F F E Fh F Cw",
    },
    "MOANA": {
        DELAY: 2,
        TUNE: "~playtune R i=xylophone m=0.8 o=5 Es F#s G#e Es F#s G#e Es F#s G#e Ee Ee B F#h Ee Bs C#6ed G#qd F# R F#s G#s Ae Ee Ee C#e C#s B4s B4e B4e Ee Eed B4ed Eed B4s Es B4s Ee Es C#s F#ed C#ed F#ed C#ed F#e Es F#s G#ed G#",
    },
    "INDIANAJONES": {
        DELAY: 3,
        TUNE: "~playtune R R R i=marimba Eed Fs Ge C5h Ded Es Fhd Ged As Be F5h Aed Bs C5 D5 E5 Eed Fs Ge C5h D5ed E5s F5hd Ged Gs E5 D5ed Gs E5 D5ed Gs E5 D5ed Gs E5e D5e E5ed F5s G5e C6h D5ed E5s F5hd G5ed A5s B5e F6h A5ed B5s C6 D6 E6 E5ed F5s G5e C6h D6ed E6s F6hd Ged Gs E5 D5ed Gs E5 D5ed Gs E5 D5ed Gs F5 E5ed Gs F5 E5ed D5s C5h",
    },
    "POKEMON": {
        DELAY: 7,
        TUNE: "~playtune R R R R R R R m=1.3 o=4 D2e F2e G2e G2e Rs De De De Dqd De C A3e F3h F3e D D Ce Bb3e Ch C Dqd Ebe Ebe Eb Eb Ebe De C Bb3h Bb3e D De C Bb3e Dh R D D5e F5e G5 Re Gh Re Ge Fe De Ce Ce Bb3 Bb3e Ce D De C Bb3e Dh D D5e F5e G5 Re De De Fe G Ge Fe G Ged As Gs F Rqd Ge Ge Ae Bbe A Ge Fe Fh Ebe Bb Bb Bb F Bb Bbh Bbqd Bbqd Bbe A De De Fe G Gqd De De Fe G Bbe G De Fe G",
    },
    "GAMEOFTHRONES": {
        DELAY: 5,
        TUNE: "~playtune R R R R R m=0.8 o=4 Ge Ce Ebs Fs Ge Ce Ebs Fs Ge Ce Ebs Fs Ge Ce Ebs Fs Ge Ce Es Fs Ge Ce Es Fs Ge Ce Es Fs Ge Ce Es Fs G3qd C3qd Eb3s F3s G3 C3 Eb3s F3s De G3e Bb3s Cs De G3e Bb3s Cs De G3e Bb3s Cs De G3e Bb3e F3qd Bb2qd Eb3s D3s F3 Bb2qd Eb3s D3s C3 Ab3s Bb3s Ce F3e Ab3s Bb3s Ce F3e Ab3s Bb3s Ce F3e Ab3e Gqd Cqd Ebs Fs G C Ebs Fs De G3e Bb3s Cs De G3e Bb3s Cs De G3e Bb3s Cs De G3e Bb3e Fqd Bb3qd Ebs Ds F Bb3qd Ebs Ds C Ab3s Bb3s Ce G3e Ab3s Bb3s Ce G3e Ab3s Bb3s Ce G3e Ab3e Bb3qd Eb3qd",
    },
    "ALADDIN": {
        DELAY: 6,
        TUNE: "~playtune R R R R R R m=1 o=4 F# Ee G F#e D A3w F# Ee G F#e D F#h Eh E D#e F# Ee C# E D C# D B3e C# E D A3w F# Ee G F#e D A3w F# E Ge F#e D F#h Eh E D#e F# Ee C# E D C# D B3e C# E D F#h F#e G B Aqd F#5e G5 B5 A5qd F#e G B Ae E G F#e Re F#h F#L0.67 GL0.67 AL0.67 C#5 D5 Aqd De C#5 D5 Aqd De F# E D E G F# D C# De E G F# B A E5qd D5h",
    },
    "STARWARS": {
        DELAY: 1,
        TUNE: "~playtune R m=1 o=5 F4t F4t F4t Bb4h F5h Ebt Dt Ct Bbh F Ebt Dt Ct Bbh F Ebt Dt Ebt Ch F4t F4t F4t Bb4h Fh Ebt Dt Ct Bbh F Ebt Dt Ct Bbh F Ebt Dt Ebt Ch F4L0.67 F4t G4qd G4e Ebe De Ce Bb4e Bb4t Ct Dt CL0.67 G4t A4 F4ed F4e G4qd G4e Ebe De Ce Bb4e Feq Cs Ch",
    },
    "FROZEN": {
        DELAY: 5,
        TUNE: "~playtune R R R R R m=1.2 o=5 Re Ee F#e Ghd De Be Ahd Ge F#e Ee Ee E Ee F# Ghd Ee F#e Ghd De Be Ahd Ge Ae B B C6e B Ae Ge Ae Ghd Dqd B4qd A4hd G4 G4 Dqd B4qd G4w",
    }
}
