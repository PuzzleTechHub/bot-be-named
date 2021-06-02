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
        TUNE: "~playtune R R R R R R B3h Ch C#h Ch B3h Ch C#h Ch Ee F#s F#s F#e F# Ee Ee Ee Ee Gs Gs Ge G F#e F#e F#e Ee F#s F#s F#e F# Ee Ee Ee Ee Gs Gs Ge G F#e F#e F#e Ee F#s F#s F#e F# Ee Ee Ee Ee Gs Gs Ge G F#e F#e Ee D#5e D5h Be Ae Bh Ee F#s F#s F#e F# Ee Ee Ee Ee Gs Gs Ge G",
    },
    "FROZEN": {
        DELAY: 3,
        TUNE: "~playtune R R R o=5 m=1.2 Re Ee F#e Ghd De Be Ahd Ge F#e Ee Ee E Ee F# Ghd Ee F#e Ghd De Be Ahd Ge Ae B B C6e B Ae Ge Ae Ghd Dqd B4qd A4hd G4 G4 Dqd B4qd G4w",
    },
    "HARRYPOTTER": {
        DELAY: 8,
        TUNE: "~playtune R R R R R R R R m=1.3 o=4 E Aqd C5e B Ah E5 D5hd Bhd Aqd C5e B Gh A Ew E Aqd C5e B Ah E5 G5h Gb5 F5h D5 F5qd E5e D#5 Ah C5 Aw C5 E5h C5 E5h C5 F5h E5 D#5h D#5 E5qd C5e A D#h E E5w C5 E5h C5 E5h C5 G5h Gb5 F5h Db5 F5qd E5e D#5 D#h C5 Aw",
    },
    "ROCKY": {
        DELAY: 3,
        TUNE: "~playtune R R R Ce Ce Cs Cs Ce Cs Cs Ee Cs Cs Ce Ee Ee Es Es Ee Es Es Ge Es Es E De Ds Ds De Ds Ds Ds Ds De Re De De Ds Ds Ds De Ds D Ds Ged Ahd As Bed Ehd Es Ged Ahd As Bed Ew",
    },
    "XMEN": {
        DELAY: 2,
        TUNE: "~playtune R R E2s E2s E2s E2s G2s G2s E2s E2s G2s G2s G2s G2s Es Bs E5s G5s F#5 E5e Bqd Es Bs E5s G5s F#5 E5e C5qd Es Bs E5s G5s F#5 E5e G5h F#5e E5e Bh Gs E5s G5s C6s B5 A5e E5qd Gs E5s G5s C6s B5 A5e F5qd Es Bs E5s G5s F#5 E5e G5h F#5e E5e Bhd",
    },
    "INDIANAJONES": {
        DELAY: 3,
        TUNE: "~playtune R R R Eed Fs Ge C5h Ded Es Fhd Ged As Be F5h Aed Bs C5 D5 E5 Eed Fs Ge C5h D5ed E5s F5hd Ged Gs E5 D5ed Gs E5 D5ed Gs E5 D5ed Gs E5e D5e E5ed F5s G5e C6h D5ed E5s F5hd G5ed A5s B5e F6h A5ed B5s C6 D6 E6 E5ed F5s G5e C6h D6ed E6s F6hd Ged Gs E5 D5ed Gs E5 D5ed Gs E5 D5ed Gs F5 E5ed Gs F5 E5ed D5s C5h",
    },
    "STARWARS": {
        DELAY: 1,
        TUNE: "~playtune R o=5 F4t F4t F4t Bb4h F5h Ebt Dt Ct Bbh F Ebt Dt Ct Bbh F Ebt Dt Ebt Ch F4t F4t F4t Bb4h Fh Ebt Dt Ct Bbh F Ebt Dt Ct Bbh F Ebt Dt Ebt Ch F4L0.67 F4t G4qd G4e Ebe De Ce Bb4e Bb4t Ct Dt CL0.67 G4t A4 F4ed F4e G4qd G4e Ebe De Ce Bb4e Feq Cs Ch",
    },
    "MOANA": {
        DELAY: 2,
        TUNE: "~playtune R R o=5 m=0.8 Es F#s G#e Es F#s G#e Es F#s G#e Ee Ee B F#h Ee Bs C#6ed G#qd F# R F#s G#s Ae Ee Ee C#e C#s B4s B4e B4e Ee Eed B4ed Eed B4s Es B4s Ee Es C#s F#ed C#ed F#ed C#ed F#e Es F#s G#ed G#",
    },
    "TITANIC": {
        DELAY: 5,
        TUNE: "~playtune R R R R R Fe Ge Ge Ah Ge Fe Ge C5h Bbe Ae Fhd R Fe Ge Ahd Bbs As Gs Fs Ge C5h Ae C5e D5h C5h Gh Rh Fqd Fe F F E Fh F E Fh G Ah Gh Fqd Fe F F E Fh F Cw",
    },
    "AVENGERS": {
        DELAY: 5,
        TUNE: "~playtune R R R R R Ds Ds D Ds Ds D Ds Ds Ds Ds Ebs Ebs Eb Ebs Ebs E Es Es Es Es Fs Fs F Fs Fs E Es Es Es Es Ebs Ebs Eb Ebs Ebs Bb3 C Ds Ds D Ds Ds D Ds Ds Ds Ds DS Ebs Ebs Eb Ebs Ebs E Es Es Es Es Fs Fs F Fs Fs E Es Es Es Es Ebs Ebs Eb Ebs Ebs Bb3 C G3w D Ced Bb3s Bb3 Ced Ds D G3hd D Ced Bb3s Bb3 A3 G3w D Ced Bb3s Bb3 Ced Ds D G3hd D Ced Bb3s Bb3 A3 G3w",
    }
}
