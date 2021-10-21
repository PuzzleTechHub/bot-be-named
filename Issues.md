## Bugfixes
- On archive server/archivechannel/wherever else the message size is dependant on a certain size of discord character limit... Learn how to split embeds into multople different embeds of <2K side
- If channel size is over 8MB, don't download more shit.
- move pin command to utils/fix error codes/convert all pins to util call
- if bot restarts and a channel /category is removed, kill its tethers
- the bot shouldn't be able to take commands until after it's loaded everything
- move cachereload to admin and make it every DB cache

## Improvements

- **Better README to postgres**
- **BBN readthedocs**
- **Look into the discord.py forks and figure out which one to commit to**
- env to constants.py
- reply to bot message be toggleable by command
- Sorted being instead groupings instead of a full sort
- add emoji on solved
- Archive channel having pins listed separately?
- Thought you'd added a CatFacts command to the bot
- provide a template postgres empty thingy. So any clone of bot knows what tables etc to work with
- Update commands that can accept e.g a discord Role/Emoji/Channel

## Features

- Write tests
- Category management : ~clonecategory etc
- Function to copy all GSheets scripts from template to another sheet
- MBot commands to consider adding - nutrimatic, solve with emoji,  dice
- On chancrab, make the channel just above highest solved channel
- **Help : arrow keys and menus**
- happy emoji on solved
- Bulk channel move
- sync all channels to the category as a function 
- nutri+qat in bot
- it would be fun to have a ~todo command with our like TODO.txt or whatever it's called
- Search can work on onelook, nutrimatic ...etc.?
- Member Convert https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.MemberConverter.convert
- Custom help commands - https://www.youtube.com/watch?v=xsA5QAkr-04&list=PL9YUC9AZJGFG6larkQJYio_f0V-O1NRjy&index=7
- on_guild_join
- during Chan crab, set it to replace PUZZLE-TITLE and PUZZLE-LINK in the tab
- **Chancrab with Overview integration during creation + solve**

### BBN Features
- BBN - sight read... music?
- BBN - Morse code by audio
- BBN - ~ cipher race for perfect pitch recognition
- BBN set board game


## QQQ Features

- discord bot WizCards
- integrate remindme with countdown
- Probably add remindme to BBN 
