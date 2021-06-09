# Music Race

## We give you tunes, you identify them!

The Music Race module was used for a community puzzle in [r/Arithmancy](https://reddit.com/r/Arithmancy). It will be
subject to change immediately following the conclusion of the puzzle.

Anyways, the name of the game is simple. We give you tunes, and you identify them. Actually, you *command* us to give
you tunes, and then you identify them. Use `~notesaw` to get info on the puzzle, and `~guesstune` to get some tune
snippets (e.g. `~guesstune PIANO`).

This puzzle was inspired by Yar Woo's [hackin' the beanstalk](https://www.mit.edu/~puzzle/2020/puzzle/hackin_the_beanstalk/), 
who also served as a testsolver on the initial implementation. Thanks, Yar Woo!

Full list of commands:
- `~notesaw` (also `~musicpuzzleinfo`) gives intro information about the puzzle
- `~guesstune` used to guess any of the tunes in the puzzle
- `~hint` a fake hint command
- `~noise` the answer to the puzzle, which encourages you to use `~playtune` over in [perfect pitch!](../perfect_pitch)

## How does this work

The bot is pre-loaded with 11 songs. Each song has also been cut into 3 second segments, where the *i-th* segment
corresponds to the *i-th* letter of the song's (movie's) name. For instance, in `HARRY POTTER`, the letter `A` 
corresponds to the 2nd song segment, the letter `R` corresponds to the 3rd, 4th, and 11th segment, and so on.

Each time the team uses `~guesstune <word>`, the bot will check `<word>` letter-by-letter against the 11 songs. 
It will then grab the largest starting substring of `word` in one of the answers (for instance, if I use 
`~guesstune HARDY` the largest substring is `HAR` from `HARRYPOTTER`. For each letter in the substring, 
it will append 3 seconds of that song to the output tune (if the team gets the entire
song correct, it will just output the fully song). For the remaining letters, the bot will select 3 second clips 
randomly from that letter's pool. Going back to my previous example, `~guesstune HARDY` will output a tune with timestamps:
- 0-3 seconds: Harry Potter
- 3-6 seconds: Harry Potter
- 6-9 seconds: Harry Potter
- 9-12 seconds: random clip corresponding to `D`
- 12-15 seconds: random clip corresponding to `Y`

(in the implementation, we add 0.5s breaks between each song to make them more easily distinguishable)

### The Extraction
So you've gotten all 11 tunes, now what? You'll notice on the output of the correct `~guesstune` we also include the 
`~playtune` command used to create the tune (if you can't see it, you'll be able to hear it). Each song has a different 
number of `R`s at the start of the command (each R is approximately `0.5s` of silence). The number of `R` corresponds to
the *i-th* letter of the song. For `HARRYPOTTER`, there are 8 `R`, so the letter to extract it `T`. After extraction, 
you come to `BOTCMDNOISE`, so you should figure out to use `~noise`. That will instruct you to use `~playtune` to create
your own tune! After doing so (and we aren't picky!) we will give you the answer, which is (well, it doesn't matter).

## Knicks, Knacks, Tricks, Tracks

Each song has a unique first letter. If you were to spam `~guesstune <letter>`, the clip you would get will not change.
That is not true of other letters, however (e.g. `R`). This can be useful for identifying which letters are song starters.

There are a couple suggested solving approaches, namely:
- Brute Force: start with `~guesstune A` and see if you can recognize the beginning of a song. If not, `~guesstune B`. 
Anytime the clip sounds like a song opener, dig one letter deeper `~guesstune AA`. Repeat this until all letters have
  been exhausted.
- The Movie Go-Er: Send the longest words possible (20 characters) and listen to as much as possible. Eventually you 
will hear clips from each movie, and should be able to identify each one.