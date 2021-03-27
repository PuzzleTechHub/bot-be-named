# ARCHIVE CHANNEL Command

Too many channels in your server? Need to delete some? Save the contents 
with the archive channel command!

`~archivechannel <channel_id>` will save the text history as a txt file, and will 
zip up any images/attachments. If the total contents of the zip file are greater than 
8MB (discord file size limit), only the text log will be returned.

If you are using the command in the same server as the channel you want to archive, you 
can use the hashtag locator (e.g. `~archivechannel #puzzle-one`)

`~archivecategory <category_id>` will do the same thing, except it will iteratively 
archive every text channel in the given category. Beware of spam! If the category
has many text channels, the bot will send you lots and lots of zip files.
Note: `archivecategory` will only accept an integer `category_id`.

## Issues

If you find any issues, bugs, or improvements, please feel free to open an issue and/or pull request! Thank you!

Feel free to find me on discord, `@kevslinger` with any questions you may have!