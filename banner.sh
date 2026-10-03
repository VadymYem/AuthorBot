#!/data/data/com.termux/files/usr/bin/bash
set -u
clear 2>/dev/null || true
frames=('AuthorBot' 'AuthorBot •' 'AuthorBot • by AuthorChe')
for frame in "${frames[@]}"; do
  printf '\r\033[1;35m%-40s\033[0m' "$frame"
  sleep 0.10
done
printf '\n'
if [ -f "$HOME/AuthorBot/assets/download.txt" ]; then
  while IFS= read -r line; do printf '%b\n' "$line"; done < "$HOME/AuthorBot/assets/download.txt"
else
  printf '\033[0;36mGitHub:\033[0m https://github.com/VadymYem/AuthorBot\n'
  printf '\033[0;36mWeb:\033[0m    https://authorche.top\n'
fi
printf '\n\033[1;32mAuthorBot is running.\033[0m\n'
