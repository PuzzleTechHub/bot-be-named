
## Bugfixes
- On archive server/archivechannel/etc... split embeds into multople different embeds of <6K size
- move pin command to utils/fix error codes/convert all pins to util call
- the bot shouldn't be able to take commands until after it's loaded everything
- move cachereload to admin and make it every DB cache
- Bot crashing due to HTTPError or APIError

### Low Priority : 
- If channel size is over 8MB, don't download more shit.
- if bot restarts and a channel /category is removed, kill its tethers
- sortchan is so slow because it tries to place everything, regardless of correct position or not

## Improvements
- **Better README to postgres**
- **BBN readthedocs**
- **Look into the discord.py forks and figure out which one to commit to**
- provide a template postgres empty thingy. So any clone of bot knows what tables etc to work with
- Update commands that can accept e.g a discord Role/Emoji/Channel
- more robust “find category” function
- A more elegant way to abstract away gspread calls so we don’t need like 4 try except blocks on every single sheets command

### Low Priority : 
- Archive channel having pinned messagess listed separately?
- CatFacts command to the bot
- Help should display module name as well? Probably aliases? (maybe not)
- make steal work with images or gifs
- add archive 1, archive 2, archive 3, archive 4 as acceptable archive suffixes for mta (automated?)

## Features
- Write tests
- Function to copy all GSheets scripts from template to another sheet
- **Help : arrow keys and menus**
- **~addalias** on all commands (or custom commands only)
- Bulk channel move
- Search can work on onelook, nutrimatic ...etc.?
- Member Convert https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.MemberConverter.convert
- Custom help commands - https://www.youtube.com/watch?v=xsA5QAkr-04&list=PL9YUC9AZJGFG6larkQJYio_f0V-O1NRjy&index=7
- on_guild_join
- during Chan crab, set it to replace PUZZLE-TITLE and PUZZLE-LINK in the tab
- **Chancrab with Overview integration during creation + solve**
- make sheets in constants py optional and therefore make modules optional?

### Low Priority : 
- happy emoji on solved, dice command?
- nutri+qat commands in bot
- it would be fun to have a ~todo command with our like TODO.txt or whatever it's called
- chancrabsorted etc

### BBN Features
- BBN - sight read... music?
- BBN - Morse code by audio
- BBN - ~ cipher race for perfect pitch recognition
- BBN set board game


## QQQ Features
- discord bot WizCards
- integrate remindme with countdown
- Probably add remindme to BBN 
