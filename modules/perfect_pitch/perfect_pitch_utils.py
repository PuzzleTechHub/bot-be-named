import shutil

from modules.perfect_pitch import perfect_pitch_constants
import os
import string
import constants
import numpy as np

class Note:
    def __init__(self, letter, duration, octave, instrument):
        """Arguments:
            - letter: e.g. C, E, G, and R means rest
            - duration: e.g. quarter, whole, half, sixteenth
            - octave: e.g. 0, 1, .., 7
            - instrument: e.g. piano, trumpet, etc."""
        self.letter = letter
        self.duration = duration
        # Rest notes don't have octave, instrument, or files
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
    def __init__(self, channel_name):
        """Set default parameters"""
        # Speed of tune
        self.meter = 1
        # Time between notes
        self.default_interval = 500
        # Length of 1 note (1 is quarter, 4 is whole, etc.)
        self.default_duration = 1
        # octave to set each note to (unless otherwise specified)
        self.default_octave = 4
        self.instrument = "piano"
        self.notes = []
        # Used for creating output file
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
            elif arg.startswith('i=') or arg.startswith('instrument='):
                self.instrument = arg.split('=')[-1].lower()
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
        Notes can come in one of 8 formats (TODO: instrument?)
        A pure natural note, no octave e.g. C
        A note with flat or sharp e.g. Eb
        A natural note with octave e.g. C4
        A note with flat/sharp and octave, e.g. F#3
        Or at the end it can have a duration e.g. w, h, q, e, s for now with d to represent dotted notes
        Like C4s, Ab3ed
        Or, for noobs, you can do L<duration>, e.g. C4L2 to represent a half note, C4L0.5 to represent an eighth
        """
        # Get duration
        # "L" duration
        #print(note)
        #print(note.split('L'))
        if len(note.split('L')) > 1:
            split_note = note.split('L')
            duration = float(split_note[1])
            note = split_note[0]
        # Dotted duration
        elif note[-2:] in perfect_pitch_constants.DURATIONS:
            duration = perfect_pitch_constants.DURATIONS[note[-2:]]
            note = note[:-2]
        # Standard duration
        elif note[-1:] in perfect_pitch_constants.DURATIONS:
            duration = perfect_pitch_constants.DURATIONS[note[-1:]]
            note = note[:-1]
        else:
            duration = self.default_duration
        # Next, check if last character is an int for octave
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

        return Note(letter, duration, octave, instrument)

    # TODO: remove ctx
    async def create_tune(self, ctx) -> str:
        """Use FFMPEG to mix the notes, and return the path of the mixed audio"""
        # Store the tune here. NOTE: only one tune per channel, for scaling reasons and within arithmancy puzzling.
        # Maybe fix later?
        output_dir = os.path.join(os.getcwd(), constants.MODULES_DIR, constants.PERFECT_PITCH.lower().replace(' ', '_'),
                                  perfect_pitch_constants.MUSIC, perfect_pitch_constants.TUNES, self.channel_name)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            os.mkdir(output_dir)
        final_output_path = os.path.join(output_dir, "tune.mp3")
        # R represents a resting note, which we want for the timing but we do not want to use as an input since
        # it doesn't have a path.
        # Get all non-resting notes
        input_notes = list(filter(lambda x: x.letter != perfect_pitch_constants.REST, self.notes))
        inputs = ' '.join([f"-i {note.path}" for note in input_notes])
        # This adds an additional notes length for each rest.
        delay = 0

        time_indices = []
        for idx, note in enumerate(self.notes):
            if idx > 0:
                delay += self.default_interval * self.notes[idx-1].duration / self.meter
            else:
                delay = 0
            if not note.letter == perfect_pitch_constants.REST:
                time_indices.append(delay)
        time_indices = np.array(time_indices)
        # Collect all partition parts
        partition_paths = []
        partition_delays = [0]
        # This is the ffmpeg mixing part, where we add each note at the specified delay
        num_partitions = int(np.ceil(time_indices.shape[0]/perfect_pitch_constants.PARTITION_SIZE))
        for partition_idx in range(num_partitions):
            output_path = os.path.join(output_dir, f"partition{partition_idx}.mp3")
            partition_paths.append(output_path)

            # Get all notes for that partition
            partition_input_notes = input_notes[partition_idx*perfect_pitch_constants.PARTITION_SIZE:
                                                (partition_idx+1)*perfect_pitch_constants.PARTITION_SIZE]
            print(partition_input_notes)
            partition_inputs = ' '.join([f"-i {note.path}" for note in partition_input_notes])
            partition_time_indices = time_indices[partition_idx*perfect_pitch_constants.PARTITION_SIZE:
                                                  (partition_idx+1)*perfect_pitch_constants.PARTITION_SIZE]
            if partition_idx < num_partitions - 1:
                partition_delays.append(time_indices[(partition_idx+1)*perfect_pitch_constants.PARTITION_SIZE-1])
            time_indices = time_indices - partition_time_indices[-1]
            filter_complex = ''.join([f"[{idx}]adelay={partition_time_indices[idx]}|{partition_time_indices[idx]}[{letter}];"
                                      for idx, letter in zip(range(len(partition_input_notes)), list(string.ascii_lowercase))])
            mix = ''.join([f"[{letter}]" for _, letter in zip(partition_input_notes, list(string.ascii_lowercase))])
            os.system(
                f"ffmpeg -y {partition_inputs} -filter_complex '{filter_complex}{mix}amix=inputs={len(partition_input_notes)}' {output_path}"
            )
        print()
        print(partition_delays)
        print(partition_paths)
        if num_partitions == 1:
            return output_path
        filter_complex = ''.join([f"[{idx}]adelay={partition_delays[idx]}|{partition_delays[idx]}[{letter}];"
                                 for idx, letter in zip(range(len(partition_delays)), list(string.ascii_lowercase))])
        mix = ''.join([f"[{letter}]" for _, letter in zip(partition_delays, list(string.ascii_lowercase))])
        # Call ffmpeg from the command line
        os.system(
            f"ffmpeg -y -i {' -i '.join(partition_paths)} -filter_complex '{filter_complex}{mix}amix=inputs={len(partition_delays)},volume=13' {final_output_path}"
        )

        return final_output_path

# How to split longer songs into multiples....
# I think it gets up to 26?
# So maybe we should cut it at, say, 20 notes
# okay so we can do time indices like normal, but then if we have more than 20 notes we will subtract the ending time
# from the remaining time_indices (first one need not be 0). We need to keep track of whatever that final time was,
# because it'll be useful in the end.
# Programmatically how to do it
# - do everything up until line 154 (filter complex) the same
# - don't need 2 separate cases
# - some iterator like math.ceil(len(notes)/20)?
#   - So we grab the 20 notes, find the ending time of that segment.
#   - Subtract all remaining time indices by the ending time.
#   -
