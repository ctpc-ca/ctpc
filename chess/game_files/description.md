<h2>Rules</h2>
This game is very simple and is not difficult to completely solve just through raw problem solving - it is meant as simply a test game.
<br><br>
You arrive on an island with 36 identical flags. You and your opponent alternate turns, and each turn a player can remove either 1, 3, or 6 flags. Whoever removes the last flag is the winner!
<br><br>
A move that does not take exactly 1, 3, or 6 flags or that takes more flags than the amount that currently remains results in immediate forfeit.

<h2>Submission guide</h2>
Your submission must be a python file that contains a function, <code>move</code>, that takes in two arguments, <code>state</code> and <code>player</code>. This function will ultimately be the one used in battle and should return a move indicating what move to play before handing the board to the opponent.
<br><br>
Furthermore,
<ul>
<li>Playing an illegal move forfeits the match immediately.</li>
<li>Any error or crash on your move forfeits the match immediately.</li>
<li>You are not allowed to skip a move.</li>
</ul>

<h2>Tournament details</h2>
The tournament will have two stages. The first stage is a 5-round swiss qualifier, where we pair up bots based on their accumulated points. The top 5 bots qualify to play the finals, which is a full double round-robin against every other bot. The highest scoring bot in the finals is crowned the winner.

<h2>Scoring details</h2>
<ul>
<li>A win is worth 1 point</li>
<li>A draw is worth 42069 points</li>
<li>A loss is worth 0 points</li>
<li>Tiebreakers in the swiss qualifier are determined through the SB-score, which rewards bots that face stronger opposition.</li>
</ul>

<style>
.code-block {
  background-color: #111222;
  color: #dcdcdc;
  padding: 1em;
  border-radius: 6px;
  font-family: monospace;
  font-size: 14px;
  white-space: pre;
  overflow-x: auto;
}
</style>

<h2>Examples</h2>
A bot that only ever plays 3 may look like this:
<pre class="code-block">def move(state, player):
    return 3</pre>

A bot that plays a random legal move every time may look like this:
<pre class="code-block">import random
def move(state, player):
    CHOICES = [1, 3, 6]
    legal = []
    for c in CHOICES:
        if c in CHOICES:
            legal.append(c)
    return random.choice(legal)</pre>

========

<h2>Formatting</h2>

Moves that your function should return are not in standard chess notation - they are slightly different in order to minimize how annoying it is to parse. Most normal moves are given in the 5-character string <code>TxyXY</code>, where

<ul>
<li><code>T</code> represents the piece type (uppercase)</li>
<li><code>xy</code> represents the start coordinate of the piece where <code>x</code> is the file and <code>y</code> is the rank</li>
<li><code>XY</code> represents the end coordinate of the piece where <code>X</code> is the file and <code>Y</code> is the rank</li>
</ul>

For example, if you were to move the <code>e2</code> pawn to <code>e4</code> in the starting position, the move would be represented by the string <code>Pe2e4</code>. If the black queen starts on her home square and captures a piece on <code>d5</code>, the move would be represented by the string <code>Qd8d5</code>.

Captures, check, checkmate, and en passant will not have any special notation.

There are two notable exceptions to this formatting rule:
<ul>
<li>Pawn promotion will be represented by the standard 5-character string with <code>=t</code> at the end, where t is the type of piece you promote to. For example, <code>Pa7a8=Q</code></li>
<li>Short castle is represented by <code>O-O</code> and long castle is represented by <code>O-O-O</code></li>
</ul>

<code>state</code> will be given as a dictionary with the following construction:
<pre class="code-block">state = {
    "board": list[list[char]],
    "E1K": bool,
    "E8K": bool,
    "A1R": bool,
    "A8R": bool,
    "H1R": bool,
    "H8R": bool,
    "prev_move": str
}</pre>
where <code>E1K</code> depicts whether or not the king on <code>e1</code> has moved, <code>A1R</code> depicts whether or not the rook on <code>a1</code> has moved, etc. This will be the ruleset used for castling.
<br>
<code>board</code> will be formatted as a standard chess board with the regular letters for pieces, white pieces being lowercase and black pieces being uppercase and in white's perspective. Empty squares will be represented by a <code>.</code>. That is, <code>a1</code> is at the bottom left and <code>h8</code> is at the top right. The starting position would look like this:
<pre class="code-block">board = [
    ["R", "N", "B", "Q", "K", "B", "N", "R"],
    ["P", "P", "P", "P", "P", "P", "P", "P"],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    [".", ".", ".", ".", ".", ".", ".", "."],
    ["p", "p", "p", "p", "p", "p", "p", "p"],
    ["r", "n", "b", "q", "k", "b", "n", "r"]
]</pre>
<br>
Finally, <code>prev_move</code> is the opponent's previous move given in the notation above.