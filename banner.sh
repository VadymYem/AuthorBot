#!/bin/bash

echo -ne "\\033[2J\033[3;1f"
cat ~/AuthorBot/assets/download.txt 2>/dev/null
printf "\n\033[1;32mAuthorBot is running!\033[0m\n"
