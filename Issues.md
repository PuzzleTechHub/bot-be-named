## Bugfixes
- On archive server/archivechannel/wherever else the message size is dependant on a certain size of discord character limit... Learn how to split embeds into multople different embeds of <2K side
- Finish has_any_role and addverifieds and migrating all bot commands to use them
- Errorlog will fail if there are no errors yet since the bot started up

## Improvements

- Better README to repro
- Help : arrow keys for navigation?
- Allow minimal bot to run without .env file
- env to constants.py
- reply to bot message be toggleable by command


## Features

- Write tests
- Category management : ~clonecategory etc
- Role assign : ~assignrole @rolename @user1 @user2 @user3
- Simple lookup for all major encodings - ~lookupsheet morse/pigpen etc
- ~reorder to reorder channels by solved status
- On chancrab, make the channel just above highest solved channel
- command named ~aboutthebot. A simple "bot tutorial" to shortly mention our 3-4 most used commands (~chancrab and ~sheetcrab, along with ~tether.... ~createchannel and ~movechannel... And ~pin ~unpin). Basically the command I'll run at the start of any hunt. "Hey this is what you can do with our bot, haffun now"
- Fix addverifieds and removeverifieds to swap all commands to it
- Help overhaul to just pull docstrings
- happy emoji on solved

- BBN - sight read... music?
- BBN - Morse code by audio
- BBN - ~ cipher race for perfect pitch recognition
- BBN set board game

## QQQ Features

- QQQ: ~housepoints 2021 and ~housecup 2021
- QQQ - Command where you can go "~newassignment [Link] [Date]"
- QQQ - And command where you go "~allassignments" to display them all in a single embed
- discord bot Duelling 
- discord bot WizCards
