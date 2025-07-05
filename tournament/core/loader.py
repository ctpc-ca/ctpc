from models import BotSubmission

def load_bots():
    print("[loader] loading bots from DB...")
    bots = {}
    for sub in BotSubmission.query.all():
        print(f"[loader] found bot: {sub.name}")
        bots[sub.name] = sub.code
    return bots
