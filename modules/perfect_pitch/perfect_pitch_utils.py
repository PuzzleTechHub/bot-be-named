import shutil

from modules.perfect_pitch import perfect_pitch_constants
import os
import string
import constants

class Note:
    def __init__(self, letter, octave, instrument):
        self.letter = letter
        if letter == "R":
            self.octave = None
            self.instrument = None
            self.path = None
        else:
            self.octave = octave
            self.instrument = instrument
            self.path = os.path.join(os.getcwd(), constants.MODULES_DIR,
                                     constants.PERFECT_PITCH.lower().replace(' ', '_'), perfect_pitch_constants.MUSIC,
                                     self.instrument, perfect_pitch_constants.NOTES, f"{self.letter}{self.octave}.mp3")

class Tune:
    """A tune to be combined by FFMPEG as audio"""
    def __init__(self, channel_name=None):
        """Set default parameters"""
        self.meter = 1
        self.default_octave = 4
        self.instrument = "piano"
        self.notes = []
        self.channel_name = channel_name

    def process_args(self, args) -> None:
        """Handle input arguments into meter, octave, instrument, and notes
            - meter: {m, meter}={float>0}
            - octave: {o, octave}={int\in[0,...,7]}
            - instrument: {piano}
        """
        for arg in args:
            # Check if arg is meter
            # NOTE: we will only accept one meter, and so first one wins
            if arg.startswith('m=') or arg.startswith('meter='):
                try:
                    self.meter = float(arg.split('=')[-1])
                except ValueError:
                    print(f"{arg} is not a meter")
                    # If they do not properly supply the meter, just ignore it and keep the default
                    pass
            elif arg.startswith('o=') or arg.startswith('octave='):
                try:
                    self.default_octave = int(arg.split('=')[-1])
                except ValueError:
                    print(f"{arg} is not an octave")
                    # If they do not properly supply the octave, just ignore it and keep the default
                    pass
            # TODO: add instrument handling here
            # Right now there is only piano so
            # if the arg is not a meter or an octave then it must be a note
            else:
                try:
                    self.notes.append(self.get_note(arg))
                except KeyError:
                    print(f"{arg} is not a note")
                    # If it's not in the note dict, then it must be some random dead argument
                    pass

    def get_note(self, note) -> Note:
        """Process one note str
        Notes can come in one of 4 formats (TODO: instrument?)
        A pure natural note, no octave e.g. C
        A note with flat or sharp e.g. Eb
        A natural note with octave e.g. C4
        A note with flat/sharp and octave, e.g. F#3
        """
        # First, check if last character is an int for octave
        try:
            octave = int(note[-1])
            # Remove octave from note
            note = note[:-1]
        except ValueError:
            octave = self.default_octave
        # TODO: instrument?
        instrument = self.instrument
        # Get the letter (handle sharps and flats in a lookup table)
        letter = perfect_pitch_constants.CLEANED_NOTES[note]

        return Note(letter, octave, instrument)

    def create_tune(self) -> str:
        """Use FFMPEG to mix the notes, and return the path of the mixed audio"""
        # Store the tune here. NOTE: only one tune per channel, for scaling reasons and within arithmancy puzzling.
        # Maybe fix later?
        output_dir = os.path.join(os.getcwd(), constants.MODULES_DIR, constants.PERFECT_PITCH.lower().replace(' ', '_'),
                                  perfect_pitch_constants.MUSIC, perfect_pitch_constants.TUNES, self.channel_name)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            os.mkdir(output_dir)
        output_path = os.path.join(output_dir, "tune.mp3")
        # R represents a resting note, which we want for the timing but we do not want to use as an input since
        # it doesn't have a path.
        # Get all non-resting notes
        input_notes = list(filter(lambda x: x.letter != perfect_pitch_constants.REST, self.notes))
        inputs = ' '.join([f"-i {note.path}" for note in input_notes])
        # This adds an additional notes length for each rest.
        time_indices = [f"{500*idx / self.meter}" for idx, note in enumerate(self.notes) if note.letter != perfect_pitch_constants.REST]
        # This is the ffmpeg mixing part, where we add each note at the specified delay
        filter_complex = ''.join([f"[{idx}]adelay={time_indices[idx]}|{time_indices[idx]}[{letter}];"
                                  for idx, letter in zip(range(len(input_notes)), list(string.ascii_lowercase))])
        mix = ''.join([f"[{letter}]" for note, letter in zip(input_notes, list(string.ascii_lowercase))])
        # Call ffmpeg from the command line
        os.system(f"ffmpeg -y {inputs} -filter_complex '{filter_complex}{mix}amix=inputs={len(input_notes)},volume=13' {output_path}")

        return output_path
