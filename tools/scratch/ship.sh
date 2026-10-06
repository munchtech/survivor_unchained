#!/bin/bash
# ship.sh "message" paths... : runs every test; commits and pushes only if all pass.
set -e
msg=$1; shift
cd /c/Users/munch/Desktop/survivorsunchained/godot/tests
out=$(dotnet test --nologo 2>&1) || { echo "$out" | grep -E "\[FAIL\]|Failed!|error" | head -20; echo "NOT COMMITTED"; exit 1; }
echo "$out" | grep -E "Passed!"
cd /c/Users/munch/Desktop/survivorsunchained
git add "$@"
git commit -q -m "$msg

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -q origin HEAD
git log --oneline -1
