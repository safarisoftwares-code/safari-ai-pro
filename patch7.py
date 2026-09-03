path = 'app/services/ai_service.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old = '        "CHEMISTRY FORMATTING (CRITICAL):\\n"'
new = '        "RESPONSE MODE SELECTOR (CRITICAL):\\n"\n        "- If CALCULATION question: direct steps only.\\n"\n        "- If EXPLANATION/WHY/WHAT IS: use PART 1 simple + PART 2 deep dive.\\n"\n        "- PART 1: analogies, emojis, simple words.\\n"\n        "- PART 2: equations, derivations, tables, timeline.\\n"\n        "CHEMISTRY FORMATTING (CRITICAL):\\n"'

if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('FIXED')
else:
    print('STILL NOT FOUND')
    # Show what's actually there
    idx = c.find('CHEMISTRY FORMATTING')
    print(repr(c[idx-20:idx+30]))
