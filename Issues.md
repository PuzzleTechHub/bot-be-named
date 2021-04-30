## Bugfixes
- Issue to fix - Insufficient perms should give a specific "No perms error code" (movechannel, createchannel?)
- Help module update to new ChannelManagementCog
- Handle error shoukd gib full stack trace

## Improvements

- Add a bunch of aliasing for different commands (createchannel/makechannel etc)
- Fix archive (create unique archive directory to store text/images in)
- Sheet management :  Deduplicaiton check, check if tethering exists, reordering
- Change name of code Cog, and bot itself.
- Better README to repro
- sample .env file
- ~archivechannel should name channel for search reasons.
- We need zips on even channels where text is only being sent

## Features

- Merge back into QQQ with submoduling
- Help module with buttons to navigate
- ~stats for keeping track on what channels server had/doesnt
- Write tests
- SHeetmanagement : Pinning, run all three commands, clean up
- ~renamechannel
- admin verifiedrole @Verified Puzzler
- Category management : ~clonecategory etc
- Role assign : ~assignrole @rolename @user1 @user2 @user3 
- Actually decent Help : With arrow keys and full things
- Simple lookup for all major encodings - ~lookupsheet morse/pigpen etc
~deleteallmessages : Admin only command
~archive channel #chan1 #chan2
