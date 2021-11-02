# WIP MUSIC RACE

Want to have perfect pitch? Now you can! Play with our music race
and you'll be identifying every note you ever hear (whether that's good or not hehe)

- `~note <octave> <flat_or_nat>` will output a random 5-second note from a piano.
  Adding `flat` will ensure you get a flat/sharp note, `nat` will ensure you get a natural note,
  and the `octave` (integer) will ensure you get a note in that octave.
- `~chord <chord>` will give you three notes in sequence followed by all three
at the same time. We only have some chords available, but uh, try it out.
- `~playtune` is one heck of a big command with lots of options. It uses [FFMPEG](https://www.ffmpeg.org/)
to splice notes together. You can use notes with flats or sharps, in different octaves, 
  at different speeds, with different instruments, and has rests. 
  
The full documentation on `~playtune` is coming shortly. For now, please check out
`~playtunehelp`, `~playtunecustom`, `~playtuneinstrument`, and `~playtunelength` for 
any info you may need. Also, to see a sample of real songs, use `~playtunesample`.

Use `~help Perfect Pitch` on the bot to know the commands in this module.