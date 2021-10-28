

def log_command(command: str, channel, author: str) -> None:
    """Log the command used, what channel it's in, and who used it"""
    print(f"Received {command} from {author} in {channel.name if hasattr(channel, 'name') else 'DM'}")

def log_command2(command: str, guild, channel, author: str) -> None:
    """Log the command used, what channel it's in, and who used it"""
    print(f"Received {command} from {author} in {guild.name if hasattr(guild,'name') else ''} : #{channel.name if hasattr(channel, 'name') else 'DM'}")