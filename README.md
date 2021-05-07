# BOT (Bot Be Named)
[![Build Status](https://travis-ci.com/kevslinger/bot-be-named.svg?branch=main)](https://travis-ci.com/kevslinger/bot-be-named)

## How to install

```bash
virtualenv venv -p=3.7
pip install -r requirements.txt
source venv/bin/activate
python bot.py
```

To run locally, you will need a `.env` file which is used by `python-dotenv`. 
Copy `.sample-env` into `.env` with
```bash
cp .sample-env .env
```
and fill in the values in order to get the bot running.

## Modules

- [Admin](./modules/admin) for administrator commands (currently, only changing the prefix)
- [Archive Channel](./modules/archive_channel) for downloading channel contents into a Zip
- [Channel Management](./modules/channel_management) for cloning, creating, and moving channels  
- [Cipher Race](modules/cipher_race) a fun cipher race!
- [Discord](modules/discord) for discord utility commands
- [Error Logging](./modules/error_logging) for Getting Error Logs
- [Help](./modules/help) for getting info about all the modules  
- [Lookup](./modules/lookup) for Searching the internet
- [Solved](./modules/solved) for marking Discord Channels as solved, backsolved, etc.
- [Time](./modules/time) for finding the time anywhere in the world


## Acknowledgements

Big thanks to [Jonah Lawrence](https://github.com/DenverCoder1) and his [Professor Vector](https://github.com/DenverCoder1/professor-vector-discord-bot)
repo for much inspiration and code, specifically on the [Create Channel](./modules/create_channel),
[Move Channel](./modules/move_channel), [Solved](./modules/solved), and [Error Logging](./modules/error_logging) modules. 

## Issues

If you find any issues, bugs, or improvements, please feel free to open an issue and/or pull request! Thank you!

Feel free to find me on discord, `@kevslinger` with any questions you may have!
