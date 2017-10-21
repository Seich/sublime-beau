# Sublime Beau

![Usage Example](/images/demo.gif?raw=true)

## Description
This plugin allows you to use beau on your beau files without having to leave sublime.

## Usage
To trigger a beau request open your command palette (ctrl+shift+t or cmd+shift+p) and type `Beau Request`.
Pressing enter will open a secondary menu that'll allow you to trigger a particular request in that file.
A new Tab will open once the request is complete showing the result for that particular request.

## Setup
Before usage you'll need to let sublime know where to find your beau executable.
To do this, open the settings file by going to `Preferences > Package Settings > Beau > Settings - User`.
In the open file specify the correct cli path in for the `cli_path` setting.

If you haven't installed beau yet, you can do it by using `npm install -g beau`
