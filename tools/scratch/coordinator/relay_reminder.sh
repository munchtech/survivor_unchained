#!/bin/sh
# UserPromptSubmit hook (coordinator): on a lead message or task notification, remind the quiet-relay rule.
input=$(cat)
case "$input" in
  *'<agent-message'*|*'<task-notification'*)
    printf '%s' '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"RELAY TURN (owner rule, memory coordinator-quiet-relays): act with tools (reply to the lead), then end with NO text unless the owner must choose, look at a picture, or hear of a merge/area done/restart."}}'
    ;;
esac
exit 0
