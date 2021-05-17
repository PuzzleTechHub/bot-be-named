# Discord Commands

## Discord Utility commands

- `~stats` prints out server stats (e.g. number of members, number of emoji)
- `~pin` pins the previous message. Alternatively, you can reply to a message with `~pin`,
which will pin the message you replied to (this is especially useful for fast-moving chats, since
  the order may get mixed up)
- `~pinme` will pin that message  
- `~unpin` unpins the previous message. You can optionally supply a number of messages to unpin
  (e.g. `~unpin 4`) and that many messages will be unpinned (up to the number of pins in the channel)
- `~addrole rolename <optional: hex color> <optional: pingable>` creates a new role with name `rolename`.
  Color can be added (otherwise default discord role color) and whether or not the role is pingable (default True).
  Note: for admins and bot owners only.
- `~assignrole rolename <user1> <user2> ...` gives the list of users the role rolename. If the role does not exist,
  the bot will create it first.
- `~deleterole rolename` will delete the role if it exists. Can either use the name of the role, or by pinging the role.
  e.g. `~deleterole myrole`, `~deleterole @myrole`. Note: for admins and bot owners only
- `~listroles` lists all the roles in the server  

## Issues

If you find any issues, bugs, or improvements, please feel free to open an issue and/or pull request! Thank you!

Feel free to find me on discord, `@kevslinger` with any questions you may have!