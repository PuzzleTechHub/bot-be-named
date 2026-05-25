# SHEET MANAGEMENT Commands - Hydra

Does Google Sheets annoy you? Don't worry, it annoys us, too! With this module, though,
you'll be able to save many clicks.

Hydra is the active replacement for new Google Sheets-Discord workflows. Lion
remains available for existing hunt workflows, but new sheet-management work
should generally live here.

Use `~help Hydra` on the bot to know the commands in this module.

### Current status

Hydra now has native commands for the main puzzle lifecycle:

| Command | What it does |
| --- | --- |
| `~chanhydra` | Creates one or more feeder puzzle channels and matching sheet tabs. |
| `~anychanhydra` / `~anyhydra` | Creates a puzzle channel from a named template. |
| `~mtahydra` | Archives a puzzle channel or thread and moves its sheet tab. |
| `~unmtahydra` | Moves an archived puzzle back to the active category and sheet section. |
| `~deletehydra` | Deletes a puzzle channel, its sheet tab, and the matching overview row. |
| `~roundhydra` | Gets or updates the round value on the Overview sheet. |
| `~noteshydra` | Gets or updates the notes value on the Overview sheet. |
| `~catsummaryhydra` | Summarizes notes for puzzle channels in the current category. |
| `~watchcategoryhydra` | Summarizes recent human messages across one or more categories. |
| `~slainhydra` / `~donehydra` | Runs `~solvedhydra` and then `~mtahydra`. |
| `~backslainhydra` | Runs `~backsolvedhydra` and then `~mtahydra`. |

Some `*hydra` aliases, such as `~solvedhydra`, `~statushydra`, and
`~tetherhydra`, are still served by the stable Lion implementation while the
migration continues.

### But why Hydra?

- As anyone who knows Greek mythology knows, the second labour after the (Nemean) **Lion** was.. the (Lernaean) **Hydra**. So... it's the next obvious module after Lion. 
- And why was the previous module named Lion? Because the **Lion** constellation (Leo) directly comes after the **Crab** one (Cancer). So Lion was the next obvious module after Crab.
- And why was the first module called Crab? Because.. well it was actually short of create-tab. Like chancrab was channel-create-tab.

More honestly though, we find it much easier for everyone to understand and remember our functions if every "bundle" of them is memorably named. So we accidentally found a theme and stuck with it. 

### What did each module have?

The modules up to Hydra have been -
- **Crab** : OG module, 2021-22, now removed ([1](https://github.com/kevslinger/bot-be-named/commit/b6d6a49) and [2](https://github.com/kevslinger/bot-be-named/commit/2017c2e)). Contained "Tab cloning" on GSheet.
- **Lion** : 2022-24, stable legacy module. Contains "Tab cloning", "Overview sheet update" and "Moving tabs around" on GSheet. Contains "Update solved status and answers from discord" on GSheets-Discord.
- **Hydra** (you are here) : 2024-present, active module for new Google Sheets-Discord workflows.

