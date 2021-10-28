
def log_command(command: str, guild, channel, author: str) -> None:
    """Log the command used, what channel it's in, and who used it"""
    if not hasattr(guild,'name'):
        print(f"Received {command} from {author} in DM")
    else:
        print(f"Received {command} from {author} in {guild.name} : #{channel.name}")