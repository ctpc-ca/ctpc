# print results for one player
def print_sandbox(results):
    print(f"{'Score':<7} {'Wins':<7} {'Draws':<7} {'Losses':<7}")
    print("-" * 31)
    print(f"{results['score']:<7} {len(results['win']):<7} {len(results['draw']):<7} {len(results['loss']):<7}")

# print full tournament results
def print_lb(results):
    print(f"{'Place':<7} {'Name':<21} {'Score':<7} {'Wins':<7} {'Draws':<7} {'Losses':<7}")
    print("-" * 60)
    place = 0
    for name, stats in results.items():
        place += 1
        print(f"{place:<7} {name:<21} {stats['score']:<7} {len(stats['win']):<7} {len(stats['draw']):<7} {len(stats['loss']):<7}")