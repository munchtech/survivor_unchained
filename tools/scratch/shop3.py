p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Pack.cs'
s = open(p, encoding='utf-8').read()
old = '''        var price = G.Journey.PriceOf(shop, chosen.Uid, buying);
        Control act;
        if (buying)
        {
            var b = Style.Button($"Buy  ·  {price} gold", () => Buy(chosen.Uid), true, true);
            b.Disabled = price == null || ch.Gold < price;
            act = price is int pp && ch.Gold < pp ? Style.H(10, b, Style.Label($"You have {Math.Floor(ch.Gold)}.", Style.UiBold, Style.Caption, Style.Bad)) : b;
        }
        else if (price != null) act = Style.Button($"Sell  ·  {price} gold", () => Sell(chosen.Uid), true, true);
        else act = Style.Label("They will not buy this.", Style.TextItalic, Style.Caption, Style.InkDim);
        if (Controls.Instance.UsingPad && act is Button) act = Style.Hint(Act.Confirm, buying ? $"Buy for {price} gold" : $"Sell for {price} gold");'''
new = '''        var price = G.Journey.PriceOf(shop, chosen.Uid, buying);
        bool pad = Controls.Instance.UsingPad, short_ = buying && price is int pp && ch.Gold < pp;
        // Only what is shown is made: a pad reads a prompt, a mouse presses a button.
        Control act;
        if (price == null) act = Style.Label(buying ? "Not for sale." : "They will not buy this.", Style.TextItalic, Style.Caption, Style.InkDim);
        else if (short_) act = Style.Label($"{price} gold: you have {Math.Floor(ch.Gold)}.", Style.UiBold, Style.Caption, Style.Bad);
        else if (pad) act = Style.Hint(Act.Confirm, buying ? $"Buy for {price} gold" : $"Sell for {price} gold");
        else act = buying ? Style.Button($"Buy  ·  {price} gold", () => Buy(chosen.Uid), true, true) : Style.Button($"Sell  ·  {price} gold", () => Sell(chosen.Uid), true, true);'''
assert old in s
s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
