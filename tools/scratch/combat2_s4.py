W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "data/content/items.json": [
        ("""  "health_draught": {
""", """  "wayfinder_chart": {
   "id": "wayfinder_chart",
   "name": "Wayfinder's Chart",
   "kind": "tool",
   "rarity": 0,
   "icon": "map",
   "value": 25,
   "stack": 1,
   "description": "A way through somewhere bad, inked on hide. Take it to the Wayfinder's table to walk it; it is used up when you do.",
   "lore": "The Wayfinder's hand, or a copy of it. The marks in the margin are what the last one to walk it met."
  },
  "health_draught": {
"""),
    ],
    W + "logic/Maps/Charts.cs": [
        ("""public static class Charts
{""", """public static class Charts
{
    /// <summary>The item a chart is carried as (its map in ItemInstance.Chart).</summary>
    public const string Item = "wayfinder_chart";
"""),
    ],
}
