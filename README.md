# BBN (Bot-Be-Named)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

- [BBN (Bot-Be-Named)](#bbn-bot-be-named)
  - [What is Bot-Be-Named](#what-is-bot-be-named)
  - [How to install](#how-to-install)
  - [Current Modules](#current-modules)
  - [Acknowledgements](#acknowledgements)
  - [Contributing/Issues](#contributingissues)

## What is Bot-Be-Named

A Discord bot that interoperates with Google Sheets to smoothen solving puzzle hunts. 
If you would like to add Bot-Be-Named to your server, please contact `@kevslinger#9711` or `@Soni#3662` on discord. 

Please note that Bot-Be-Named is set up for our own configurations and environment variables, and may not work for yours. Please contact us if you need help setting up an instance of the bot, but we **highly recommend asking us for a Bot invite link**.

## Inviting the Bot to your server

- Message `@kevslinger#9711` or `@Soni#3662` on discord to get Bot invite link.

- Use the Link and add the Bot to your discord server. Note that you need "Manage Server" permission to do that.

- Use `~about` to get a quick guide to the bot, and `~startup` for all the commands that will come in very handy for you.

- In case of any problems, message us on discord or [open a new issue on Github](https://github.com/kevslinger/bot-be-named/issues/new)

## How to install your own instance

### Prerequisites - 

- [python3.7 or newer](https://realpython.com/installing-python/)

- [Git](https://github.com/git-guides/install-git)

- [Postgresql for storing data](https://www.postgresql.org/download/)

- [Heroku CLI client for hosting](https://medium.com/analytics-vidhya/how-to-install-heroku-cli-in-windows-pc-e3cf9750b4ae)

- [Pip package installer for Python](https://phoenixnap.com/kb/install-pip-windows)

Note that you may use another Python installer (instead of Pip), Host (instead of Heroku) or Database (instead of Postgresql) but that will require you figuring out the required setup and configuation changes yourself.

### Installation

We recommend using [virtual environments](https://docs.python.org/3/tutorial/venv.html) to manage python packages for our repo. To clone the repo and install dependencies, run the following on the Command Line

```bash
#Clone the bot locally
git clone https://github.com/kevslinger/bot-be-named.git
cd bot-be-named
virtualenv venv -p=3.7
#This installs all the python dependancies the bot needs
pip install -r requirements.txt && pre-commit install
```

The bot uses [Heroku Postgres](https://www.heroku.com/postgres) for storing data.

To run the bot locally, you will need a `.env` file which is used by [python-dotenv](https://github.com/theskumar/python-dotenv) to load `ENV` variables. Copy `.env.template` into `.env` with  

```bash
cp .env.template .env
```

and fill in the blanks in order to get the bot running. You also need to set up the Postgresql database for the bot using (To be finished).

Once you do all that, run


```bash
source venv/bin/activate
python bot.py
```

and the bot will run on the supplied discord token's account.

### Hosting

Once you have the bot running and basic commands (like `~help`) run properly, you can host it externally. Our instance of the bot is [hosted on Heroku](https://medium.com/@linda0511ny/create-host-a-discord-bot-with-heroku-in-5-min-5cb0830d0ff2)


## Current Modules

- [Admin](./modules/admin) for administrator commands (currently, only changing the prefix)
- [Archive](./modules/archive) for downloading channel/category/server contents into a Zip file
- [Channel Management](./modules/channel_management) for cloning, creating, and moving channels  
- [Cipher Race](modules/cipher_race) Race against the clock decoding ciphers!
- [Discord](modules/discord) for discord utility commands (e.g. roles, stats)
- [Error Logging](./modules/error_logging) for printing error logs
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
