from models import BotSubmission

def load_bots(verbose=False):
    if verbose: print("[loader] loading bots from DB...")
    bots = {}
    for sub in BotSubmission.query.all():
        if verbose: print(f"[loader] found bot: {sub.name}")
        bots[sub.name] = sub.code
    return bots
