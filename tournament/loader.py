import types

def load_game_modules(game):
    """Loads game logic from a Game object and returns modules."""

    modules = {}

    for key in ["formatter_code", "gameplay_code", "termination_code", "utils_code"]:
        code = getattr(game, key)
        mod = types.ModuleType(key)
        exec(code, mod.__dict__)
        modules[key] = mod

    return modules
