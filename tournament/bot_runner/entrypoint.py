import sys
import json

import importlib.util

data = json.load(sys.stdin)

bot_code = data["bot_code"]
game_state = data["game_state"]

with open("/bot/player_bot.py", "w") as f:
    f.write(bot_code)

spec = importlib.util.spec_from_file_location("bot", "/bot/player_bot.py")
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)

move_result = bot.move(game_state)
print(json.dumps({"result": move_result}))
