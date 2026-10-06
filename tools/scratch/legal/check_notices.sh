#!/usr/bin/env bash
# Checks that the notice files the licences folder needs exist at their sources.
for u in \
  https://raw.githubusercontent.com/dotnet/runtime/release/8.0/LICENSE.TXT \
  https://raw.githubusercontent.com/dotnet/runtime/release/8.0/THIRD-PARTY-NOTICES.TXT \
  https://raw.githubusercontent.com/godotengine/godot/4.5.1-stable/LICENSE.txt \
  https://raw.githubusercontent.com/godotengine/godot/4.5.1-stable/COPYRIGHT.txt ; do
  printf "%s " "$u"
  curl -s -o /dev/null -w "%{http_code} %{size_download}\n" "$u"
done
curl -s https://raw.githubusercontent.com/dotnet/runtime/release/8.0/LICENSE.TXT | head -4
