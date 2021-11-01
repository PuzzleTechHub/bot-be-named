# BBN (Bot-Be-Named)
[![Build Status](https://travis-ci.com/kevslinger/bot-be-named.svg?branch=main)](https://travis-ci.com/kevslinger/bot-be-named)

- [BBN (Bot-Be-Named)](#bbn-bot-be-named)
  - [What is Bot-Be-Named](#what-is-bot-be-named)
  - [How to install](#how-to-install)
  - [Current Modules](#current-modules)
  - [Acknowledgements](#acknowledgements)
  - [Contributing/Issues](#contributingissues)

## What is Bot-Be-Named

A discord bot that interoperates with google sheets to facilitate puzzle hunts. 
If you would like to add Bot-Be-Named to your server, please contact `@kevslinger#9711` or `@Soni#3662` on discord. 
Please do **not** self-host Bot-Be-Named as it is set up for our own configurations and environment variables, and may not work for yours.


## How to install

We recommend using [virtual environments](https://docs.python.org/3/tutorial/venv.html) to manage python packages for our repo. To clone the repo and install dependencies, run the following

```bash
git clone https://github.com/kevslinger/bot-be-named.git
cd bot-be-named
virtualenv venv -p=3.7
pip install -r requirements.txt
```

The bot uses [Heroku Postgres](https://www.heroku.com/postgres) for storing data. You'll need to install postgres on your 
computer by going to https://www.postgresql.org/download/ and following the instructions for your operating system.

To run the bot locally, you will need a `.env` file which is used by [python-dotenv](https://github.com/theskumar/python-dotenv) to load `ENV` variables. Copy `.env.template` into `.env` with  

```bash
cp .sample-env .env
```

and fill in the blanks in order to get the bot running. Once you do, run


```bash
source venv/bin/activate
python bot.py
```

and the bot will run on the supplied discord token's account.


## Current Modules

- [Admin](./modules/admin) for administrator commands (currently, only changing the prefix)
- [Archive](./modules/archive) for downloading channel/category/server contents into a Zip file
- [Channel Management](./modules/channel_management) for cloning, creating, and moving channels  
- [Cipher Race](modules/cipher_race) Race against the clock decoding ciphers!
- [Discord](modules/discord) for discord utility commands (e.g. roles, stats)
- [Error Logging](./modules/error_logging) for printing error logs
- [Help](./modules/help) (Deprecated) for getting info about all the modules  
- [Lookup](./modules/lookup) for Searching the internet via google and wikipedia
- [Music Race](./modules/music_race/) Help! Our tunes have been sawed apart and put back incorrectly!
- [Help](./modules/help) is an updated help command which automatically pulls docstrings for `~help`
- [Perfect Pitch](./modules/perfect_pitch) Become a composer and write tunes in mp4
- [Sheets](./modules/sheets) for working with Google Sheets during puzzlehunts
- [Solved](./modules/solved) for marking Discord Channels as solved, backsolved, solvedish etc.
- [Time](./modules/time) for finding the time anywhere in the world
- [Misc](./modules/misc) for misc. random (fun) commands

## Acknowledgements

Big thanks to [Jonah Lawrence](https://github.com/DenverCoder1) and his [Professor Vector](https://github.com/DenverCoder1/professor-vector-discord-bot)
repo for much inspiration and code, specifically on the [Channel Management](./modules/channel_management), [Error Logging](./modules/error_logging), [Help](./modules/help), and [Solved](./modules/solved) modules. 

## Contributing/Issues

If you find any issues, bugs, or improvements, please feel free to open an issue and/or pull request! Thank you!

Feel free to find me on discord, `@kevslinger#9711` with any questions you may have!
