# ARCHIVE CHANNEL Command

Too many channels in your server? Need to delete some? Save the contents 
with the archive channel command!

`~archivechannel <channel_id_or_name>` will save the text history as a txt file, and will 
zip up any images/attachments. If the total contents of the zip file are greater than 
8MB (discord file size limit), only the text log will be returned.

If you are using the command in the same server as the channel you want to archive, you 
can use the channel name or hashtag locator (e.g. `~archivechannel #puzzle-one`). Otherwise,
you need to use the channel ID number.

`~archivecategory <category_id_or_name>` will do the same thing, except it will iteratively 
archive every text channel in the given category. Beware of spam! If the category
has many text channels, the bot will send you lots and lots of zip files. .

## Issues

If you find any issues, bugs, or improvements, please feel free to open an issue and/or pull request! Thank you!

Feel free to find me on discord, `@kevslinger` with any questions you may have!