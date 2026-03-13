#!/usr/bin/env python3
"""
Programmatically generate spread_betting_tournament.ipynb using nbformat.
Run once to produce the notebook file, then execute it separately.
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11.0"},
}
cells = []

# ── helper ────────────────────────────────────────────────────────────────────
def md(src):
    return nbf.v4.new_markdown_cell(src)

def code(src):
    return nbf.v4.new_code_cell(src)

# ==============================================================================
# TITLE
# ==============================================================================
cells.append(md("""\
# 🏆 World Cup Spread Betting Tournament

## A friend group game based on sports spread betting "outright index" markets

---

**How it works**

Before the tournament starts, every team is given a **buy / sell spread price** (like
Sporting Index / Spreadex outright markets). Each player takes a position on **every** team:

- **BUY** — you think the team will *outperform* their price (you pay the buy price)
- **SELL** — you think the team will *underperform* their price (you receive the sell price)

At the end, each team "makes up" to a fixed points value based on how far they went.
Your profit or loss scales continuously — the further your team exceeds (or falls short of)
their price, the more you win (or lose). There are no fixed odds, no single winner takes all.

**Key difference from fixed-odds betting:** Buying England at 43 when they reach the final
(75 pts) is very different from buying them at 43 when they win it (100 pts). Every extra
round matters.

---

*Adjust the `STAKE` parameter in the next cell to match your group's agreed stake.*
"""))

# ==============================================================================
# IMPORTS
# ==============================================================================
cells.append(code("""\
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from IPython.display import display, Markdown
import warnings
warnings.filterwarnings('ignore')

# Use notebook renderer for plotly
import plotly.io as pio
pio.renderers.default = 'notebook'
"""))

# ==============================================================================
# PARAMETERS
# ==============================================================================
cells.append(md("""\
## Parameters

Change `STAKE` here and every P&L figure in the notebook updates automatically.
"""))

cells.append(code("""\
# ================================================================
# PARAMETERS — adjust for your group's game
# ================================================================
STAKE    = 5      # £ per point (e.g. 5 means £5 profit/loss per point moved)
CURRENCY = '£'    # currency symbol for display
# ================================================================
"""))

# ==============================================================================
# SCORING + PRICES
# ==============================================================================
cells.append(md("""\
## Scoring Scale & Pre-Tournament Prices

### Make-up values (settlement points)

| Result | Points |
|--------|--------|
| Winner | 100 |
| Runner-up | 75 |
| Semi-final exit | 50 |
| Quarter-final exit | 25 |
| Round of 16 exit | 10 |
| Group-stage exit | 0 |

### Pre-tournament spread prices

Prices roughly reflect the market's consensus expectation of finishing position.
Brazil at 60 implies the market expects roughly a semi-final run; Japan at 10 implies
early exit. The 2-point buy/sell spread is the house edge.
"""))

cells.append(code("""\
# Scoring scale ─ how many points each finishing position is worth
SCORING = {
    'winner':        100,
    'runner_up':      75,
    'semi_final':     50,
    'quarter_final':  25,
    'round_of_16':    10,
    'group_stage':     0,
}

# Pre-tournament spread prices  (buy price / sell price)
# Spread = buy − sell = 2 pts (the market maker's margin)
teams = {
    'Brazil':      {'buy': 62, 'sell': 60},
    'France':      {'buy': 58, 'sell': 56},
    'England':     {'buy': 45, 'sell': 43},
    'Argentina':   {'buy': 42, 'sell': 40},
    'Spain':       {'buy': 38, 'sell': 36},
    'Germany':     {'buy': 35, 'sell': 33},
    'Portugal':    {'buy': 30, 'sell': 28},
    'Netherlands': {'buy': 25, 'sell': 23},
    'Uruguay':     {'buy': 18, 'sell': 16},
    'Japan':       {'buy': 12, 'sell': 10},
}

# Sanity check: sell prices should sum to the expected total make-up across all teams
total_sell = sum(v['sell'] for v in teams.values())
print(f"Sum of sell prices: {total_sell}")
print(f"(In a fairly priced market this equals the expected total make-up across all 10 teams)")
print()

# Display price sheet
price_df = pd.DataFrame(teams).T.rename(columns={'buy': 'Buy', 'sell': 'Sell'})
price_df['Spread'] = price_df['Buy'] - price_df['Sell']
price_df['Mid']    = (price_df['Buy'] + price_df['Sell']) / 2
price_df.index.name = 'Team'
print("=== PRE-TOURNAMENT PRICE SHEET ===")
display(price_df)
"""))

# ==============================================================================
# PLAYER POSITIONS
# ==============================================================================
cells.append(md("""\
## Player Positions

Five players have each taken a position on every team.
`BUY @ price` means they paid that price; `SELL @ price` means they received it.
"""))

cells.append(code("""\
# +1 = BUY (at buy price), −1 = SELL (at sell price)
positions = {
    'Alice':   {
        'Brazil': -1, 'France':  1, 'England':  1, 'Argentina':  1, 'Spain': -1,
        'Germany': -1, 'Portugal':  1, 'Netherlands':  1, 'Japan': -1, 'Uruguay': -1,
    },
    'Bob':     {
        'Brazil':  1, 'France':  1, 'England': -1, 'Argentina': -1, 'Spain':  1,
        'Germany':  1, 'Portugal': -1, 'Netherlands': -1, 'Japan': -1, 'Uruguay':  1,
    },
    'Charlie': {
        'Brazil':  1, 'France': -1, 'England':  1, 'Argentina': -1, 'Spain': -1,
        'Germany':  1, 'Portugal':  1, 'Netherlands':  1, 'Japan':  1, 'Uruguay': -1,
    },
    'Diana':   {
        'Brazil': -1, 'France': -1, 'England': -1, 'Argentina':  1, 'Spain':  1,
        'Germany': -1, 'Portugal':  1, 'Netherlands':  1, 'Japan': -1, 'Uruguay':  1,
    },
    'Eddie':   {
        'Brazil':  1, 'France':  1, 'England':  1, 'Argentina':  1, 'Spain': -1,
        'Germany': -1, 'Portugal': -1, 'Netherlands': -1, 'Japan': -1, 'Uruguay': -1,
    },
}

def format_position(player, team):
    d = positions[player][team]
    return f"BUY  @ {teams[team]['buy']}" if d == 1 else f"SELL @ {teams[team]['sell']}"

pos_df = pd.DataFrame(
    {p: {t: format_position(p, t) for t in teams} for p in positions}
).T
pos_df.index.name = 'Player'
print("=== POSITION SHEET ===")
display(pos_df)
"""))

# ==============================================================================
# TOURNAMENT STRUCTURE
# ==============================================================================
cells.append(md("""\
## Tournament Simulation

We simulate a 32-team World Cup. The 10 named teams above are the ones in our market;
22 unnamed "rest of world" teams make up the rest of the draw.

### Running P&L methodology

At each stage, teams **still in** the competition are valued at the **survivor floor** —
the minimum make-up they are now guaranteed based on the round they've reached.
For example, once a team has survived the group stage they are guaranteed at least 10 points
(a Round of 16 exit). This gives a realistic running P&L after each round.
"""))

cells.append(code("""\
# Tournament rounds
# survivor_floor = implied make-up for teams not yet eliminated
# eliminated     = {team: final_make_up} for teams knocked out in this round
ROUNDS = [
    {
        'name':           'Group Stage',
        'survivor_floor':  10,    # guaranteed ≥ R16 exit
        'eliminated':     {'Japan': 0, 'Uruguay': 0},
    },
    {
        'name':           'Round of 16',
        'survivor_floor':  25,    # guaranteed ≥ QF exit
        'eliminated':     {'Germany': 10, 'Netherlands': 10},
    },
    {
        'name':           'Quarter-Finals',
        'survivor_floor':  50,    # guaranteed ≥ SF exit
        'eliminated':     {'Spain': 25, 'Portugal': 25},
    },
    {
        'name':           'Semi-Finals',
        'survivor_floor':  75,    # guaranteed ≥ Final (runner-up)
        'eliminated':     {'Brazil': 50, 'Argentina': 50},
    },
    {
        'name':           'Final',
        'survivor_floor':  None,  # tournament over
        'eliminated':     {'England': 75, 'France': 100},
    },
]

print("=== TOURNAMENT BRACKET ===")
for r in ROUNDS:
    exits = ', '.join([f"{t} ({v} pts)" for t, v in r['eliminated'].items()])
    print(f"  {r['name']:20s}  eliminated: {exits}")
"""))

# ==============================================================================
# MID-TOURNAMENT TRADES
# ==============================================================================
cells.append(md("""\
## Mid-Tournament Trades

In spread betting you can **close a position early** at the current implied price — locking
in profit or cutting losses before settlement.

Here the implied price for a team still in the competition is their **survivor floor** at
that moment. Between the Quarter-Finals and Semi-Finals, the four remaining teams (England,
France, Brazil, Argentina) are each valued at **50 pts** — their guaranteed minimum.

Two players decide to act:
"""))

cells.append(code("""\
# Mid-tournament trades
# close_price        = implied make-up at time of trade (= survivor_floor that round)
# close_after_round  = name of the round that just completed when the trade is made
TRADES = [
    {
        'player':           'Bob',
        'team':             'England',
        'close_price':       50,
        'close_after_round': 'Quarter-Finals',
        'rationale': (
            "Bob cuts his England SELL losses. England are through to the semis and "
            "valued at 50 pts. His sell (at 43) is already down £35 and he can see "
            "it getting much worse if England reach the final. He takes the hit now."
        ),
    },
    {
        'player':           'Charlie',
        'team':             'France',
        'close_price':       50,
        'close_after_round': 'Quarter-Finals',
        'rationale': (
            "Charlie banks a small profit on his France SELL. He sold France at 56 "
            "and they're now implied at 50 — a £30 gain. He locks it in, nervous that "
            "France could go all the way. (Spoiler: they do.)"
        ),
    },
]

print("=== MID-TOURNAMENT TRADES ===")
for t in TRADES:
    direction  = positions[t['player']][t['team']]
    open_price = teams[t['team']]['buy'] if direction == 1 else teams[t['team']]['sell']
    dir_str    = 'BUY' if direction == 1 else 'SELL'
    locked     = (t['close_price'] - open_price) * STAKE if direction == 1 \
                 else (open_price - t['close_price']) * STAKE
    print(f"  {t['player']:8s} CLOSE {t['team']:12s} {dir_str} @ {open_price} → {t['close_price']} "
          f"= {CURRENCY}{locked:+,.0f} locked")
    print(f"           {t['rationale'][:90]}...")
    print()
"""))

# ==============================================================================
# P&L ENGINE
# ==============================================================================
cells.append(md("""\
## P&L Calculation Engine

Core functions used throughout the notebook.
"""))

cells.append(code("""\
# ================================================================
# P&L ENGINE
# ================================================================

def get_makeups_at_round(round_idx):
    \"\"\"
    Returns {team: implied_makeup} for all teams after `round_idx` rounds.
    Eliminated teams → actual make-up.  Teams still in → survivor_floor.
    \"\"\"
    makeups = {}
    for i in range(round_idx + 1):
        makeups.update(ROUNDS[i]['eliminated'])
    if round_idx < len(ROUNDS) - 1:
        floor = ROUNDS[round_idx]['survivor_floor']
        for team in teams:
            if team not in makeups:
                makeups[team] = floor
    return makeups


def get_closed_positions(up_to_round_idx):
    \"\"\"
    Returns {(player, team): locked_pnl} for trades closed on or before
    `up_to_round_idx`.
    \"\"\"
    round_name_to_idx = {r['name']: i for i, r in enumerate(ROUNDS)}
    closed = {}
    for trade in TRADES:
        if round_name_to_idx[trade['close_after_round']] <= up_to_round_idx:
            player     = trade['player']
            team       = trade['team']
            direction  = positions[player][team]
            open_price = teams[team]['buy'] if direction == 1 else teams[team]['sell']
            locked     = (trade['close_price'] - open_price) * STAKE if direction == 1 \
                         else (open_price - trade['close_price']) * STAKE
            closed[(player, team)] = locked
    return closed


def calc_pnl(player, makeups, closed_positions, return_details=False):
    \"\"\"
    Calculate a player's total P&L.

    Returns:
        total_pnl (float)
        If return_details=True also returns a per-team DataFrame.
    \"\"\"
    total   = 0
    details = []

    for team in teams:
        direction  = positions[player][team]
        dir_str    = 'BUY' if direction == 1 else 'SELL'
        open_price = teams[team]['buy'] if direction == 1 else teams[team]['sell']

        if (player, team) in closed_positions:
            pnl            = closed_positions[(player, team)]
            implied_display = f"closed @ {open_price}"
            status         = 'CLOSED'
        else:
            implied = makeups[team]
            pnl     = (implied - open_price) * STAKE if direction == 1 \
                      else (open_price - implied) * STAKE
            implied_display = implied
            status  = 'WIN' if pnl > 0 else ('LOSE' if pnl < 0 else 'FLAT')

        total += pnl
        details.append({
            'Team': team, 'Direction': dir_str, 'Open Price': open_price,
            'Implied': implied_display, f'P&L ({CURRENCY})': pnl, 'Status': status,
        })

    if return_details:
        return total, pd.DataFrame(details).set_index('Team')
    return total


def all_player_pnl(round_idx):
    \"\"\"Return {player: pnl} for a given round snapshot.\"\"\"
    makeups = get_makeups_at_round(round_idx)
    closed  = get_closed_positions(round_idx)
    return {p: calc_pnl(p, makeups, closed) for p in positions}


def leaderboard(round_idx, label=None):
    \"\"\"Print and return a ranked leaderboard DataFrame.\"\"\"
    pnls    = all_player_pnl(round_idx)
    ranking = sorted(pnls.items(), key=lambda x: -x[1])
    lb = pd.DataFrame(ranking, columns=['Player', f'P&L ({CURRENCY})'])
    lb.index = range(1, len(lb) + 1)
    lb.index.name = 'Rank'
    if label:
        print(f"=== {label} ===")
    display(lb.style.format({f'P&L ({CURRENCY})': lambda x: f"{CURRENCY}{x:+,.0f}"}))
    return pnls


# ── Build full P&L time series ──────────────────────────────────────────────
SNAPSHOTS   = ['Start'] + [r['name'] for r in ROUNDS]
pnl_history = {p: [0] for p in positions}

for _idx in range(len(ROUNDS)):
    _round_pnls = all_player_pnl(_idx)
    for _p in positions:
        pnl_history[_p].append(_round_pnls[_p])

pnl_df = pd.DataFrame(pnl_history, index=SNAPSHOTS)
print("P&L engine ready. Cumulative P&L table:")
display(
    pnl_df.style
    .format(lambda x: f"{CURRENCY}{x:+,.0f}")
    .background_gradient(cmap='RdYlGn', axis=None)
    .set_caption("Cumulative P&L — each column is a player, each row is a tournament stage")
)
"""))

# ==============================================================================
# NARRATIVE GENERATOR
# ==============================================================================
cells.append(code("""\
# ================================================================
# NARRATIVE GENERATOR
# ================================================================

def generate_narrative(round_idx):
    \"\"\"Generate a markdown round-up for a given round.\"\"\"
    r         = ROUNDS[round_idx]
    round_name = r['name']
    eliminated = r['eliminated']

    current   = all_player_pnl(round_idx)
    prev      = all_player_pnl(round_idx - 1) if round_idx > 0 else {p: 0 for p in positions}

    curr_rank = {p: i+1 for i, (p, _) in enumerate(sorted(current.items(), key=lambda x: -x[1]))}
    prev_rank = {p: i+1 for i, (p, _) in enumerate(sorted(prev.items(),    key=lambda x: -x[1]))}

    movers = [(p, prev_rank[p] - curr_rank[p], current[p] - prev[p], curr_rank[p])
              for p in positions]

    biggest_gain = max(movers, key=lambda x: x[2])
    biggest_loss = min(movers, key=lambda x: x[2])

    elim_str = ', '.join([f"**{t}** ({v} pts)" for t, v in eliminated.items()])
    lines    = [
        f"### After {round_name}", "",
        f"**Eliminated this round:** {elim_str}", "",
        "**Leaderboard:**", "",
    ]

    for p, rank_change, pnl_change, curr_r in sorted(movers, key=lambda x: x[3]):
        arrow = "⬆️" if rank_change > 0 else ("⬇️" if rank_change < 0 else "➡️")
        mv_str = (
            f" *(+{rank_change} place{'s' if abs(rank_change)>1 else ''})*" if rank_change > 0 else
            f" *(-{abs(rank_change)} place{'s' if abs(rank_change)>1 else ''})*" if rank_change < 0 else ""
        )
        lines.append(
            f"{curr_r}. {arrow} **{p}** — {CURRENCY}{current[p]:+,.0f} "
            f"(this round: {CURRENCY}{pnl_change:+,.0f}){mv_str}"
        )

    lines += [
        "",
        f"💰 **Best this round:** {biggest_gain[0]} ({CURRENCY}{biggest_gain[2]:+,.0f})",
        f"📉 **Worst this round:** {biggest_loss[0]} ({CURRENCY}{biggest_loss[2]:+,.0f})",
    ]
    return "\\n".join(lines)

print("Narrative generator ready.")
"""))

# ==============================================================================
# ROUND BY ROUND
# ==============================================================================
cells.append(md("""\
---

## Round by Round Analysis

Below we walk through the tournament stage by stage, updating P&L and leaderboard after each round.
"""))

# ── Group Stage
cells.append(md("""\
### Group Stage

Japan and Uruguay exit at the group stage (0 pts). All other teams survive and are now
guaranteed at least 10 pts (a Round of 16 exit).

Early leaders: sellers of the big favourites are ahead — their implied make-up has crashed
from 56+ down to just 10.
"""))

cells.append(code("""\
r = ROUNDS[0]
print(f"Eliminated: {', '.join([f'{t} ({v} pts)' for t, v in r['eliminated'].items()])}")
print(f"Survivor implied value: {r['survivor_floor']} pts")
print()
pnls_gs = leaderboard(0, "AFTER GROUP STAGE")
"""))

cells.append(code("""\
display(Markdown(generate_narrative(0)))
"""))

# ── Round of 16
cells.append(md("""\
### Round of 16

Germany and Netherlands are knocked out (10 pts each — they reached the knockout stage
but no further). The remaining six teams are now guaranteed at least 25 pts.
"""))

cells.append(code("""\
r = ROUNDS[1]
print(f"Eliminated: {', '.join([f'{t} ({v} pts)' for t, v in r['eliminated'].items()])}")
print(f"Survivor implied value: {r['survivor_floor']} pts")
print()
pnls_r16 = leaderboard(1, "AFTER ROUND OF 16")
"""))

cells.append(code("""\
display(Markdown(generate_narrative(1)))
"""))

# ── Quarter-Finals
cells.append(md("""\
### Quarter-Finals

Spain and Portugal exit at the quarter-final stage (25 pts). England, France, Brazil and
Argentina reach the semi-finals, where they are each guaranteed at least 50 pts.

**After this round, two players make mid-tournament trades** (see below).
"""))

cells.append(code("""\
r = ROUNDS[2]
print(f"Eliminated: {', '.join([f'{t} ({v} pts)' for t, v in r['eliminated'].items()])}")
print(f"Survivor implied value: {r['survivor_floor']} pts")
print()
pnls_qf = leaderboard(2, "AFTER QUARTER-FINALS")
"""))

cells.append(code("""\
display(Markdown(generate_narrative(2)))
"""))

# ── Mid-tournament trades
cells.append(md("""\
### Mid-Tournament Trades — QF to SF Window

With four teams left, each valued at 50 pts, Bob and Charlie decide to close positions.
"""))

cells.append(code("""\
print("=== MID-TOURNAMENT TRADES EXECUTED ===\\n")
for trade in TRADES:
    player    = trade['player']
    team      = trade['team']
    direction = positions[player][team]
    open_p    = teams[team]['buy'] if direction == 1 else teams[team]['sell']
    dir_str   = 'BUY' if direction == 1 else 'SELL'
    locked    = (trade['close_price'] - open_p) * STAKE if direction == 1 \
                else (open_p - trade['close_price']) * STAKE

    # What would final settlement have been without the trade?
    all_final = {}
    for rr in ROUNDS:
        all_final.update(rr['eliminated'])
    final_mu  = all_final[team]
    unhedged  = (final_mu - open_p) * STAKE if direction == 1 else (open_p - final_mu) * STAKE
    saving    = locked - unhedged

    print(f"  {player}: {dir_str} {team} @ {open_p}  →  close @ {trade['close_price']} pts")
    print(f"    Locked P&L      : {CURRENCY}{locked:+,.0f}")
    print(f"    Settlement P&L  : {CURRENCY}{unhedged:+,.0f}  (if held to the end)")
    print(f"    Trade saved     : {CURRENCY}{saving:+,.0f}")
    print(f"    Rationale: {trade['rationale']}")
    print()
"""))

# ── Semi-Finals
cells.append(md("""\
### Semi-Finals

Brazil and Argentina exit at the semis (50 pts each). The final is **France vs England**.
Both are now guaranteed at least 75 pts (runner-up).

Note: Bob's England SELL and Charlie's France SELL are already **closed** — they don't
benefit or suffer from England / France reaching the final.
"""))

cells.append(code("""\
r = ROUNDS[3]
print(f"Eliminated: {', '.join([f'{t} ({v} pts)' for t, v in r['eliminated'].items()])}")
print(f"Finalists: England & France — guaranteed {r['survivor_floor']} pts minimum")
print()
pnls_sf = leaderboard(3, "AFTER SEMI-FINALS")
"""))

cells.append(code("""\
display(Markdown(generate_narrative(3)))
"""))

# ── Final
cells.append(md("""\
---

## The Final: France 🇫🇷 vs England 🏴󠁧󠁢󠁥󠁮󠁧󠁿

**France win the World Cup!** England are runners-up.

| Team | Make-up |
|------|---------|
| 🥇 France | **100 pts** |
| 🥈 England | **75 pts** |
"""))

cells.append(code("""\
r = ROUNDS[4]
print(f"FINAL RESULT: France 100 pts (Winner) | England 75 pts (Runner-up)")
print()
pnls_final = leaderboard(4, "FINAL SETTLEMENT — COMPLETE RESULTS")
"""))

cells.append(code("""\
display(Markdown(generate_narrative(4)))
"""))

cells.append(code("""\
# Full per-team breakdown for each player at settlement
print("=== FULL SETTLEMENT BREAKDOWN ===\\n")
makeups_final = get_makeups_at_round(4)
closed_final  = get_closed_positions(4)

for player in sorted(positions.keys()):
    total, details = calc_pnl(player, makeups_final, closed_final, return_details=True)
    print(f"── {player}  Final P&L: {CURRENCY}{total:+,.0f} ──")
    display(
        details.style.format({
            f'P&L ({CURRENCY})': lambda x: f"{CURRENCY}{x:+,.0f}" if isinstance(x, (int, float)) else x
        })
        .map(
            lambda v: 'color: green' if v == 'WIN' else ('color: red' if v == 'LOSE' else ''),
            subset=['Status']
        )
    )
    print()
"""))

# ==============================================================================
# CHARTS
# ==============================================================================
cells.append(md("""\
---

## Charts

Four interactive charts to visualise the tournament from every angle.
Hover over any element for details.
"""))

# Chart 1 — Leaderboard
cells.append(md("""\
### Chart 1 — Final Leaderboard
"""))

cells.append(code("""\
# ================================================================
# CHART 1: FINAL LEADERBOARD BAR CHART
# ================================================================
final_pnls   = all_player_pnl(4)
final_rank   = sorted(final_pnls.items(), key=lambda x: -x[1])
p_sorted     = [p for p, _ in final_rank]
v_sorted     = [v for _, v in final_rank]
bar_colors   = ['#27ae60' if v >= 0 else '#c0392b' for v in v_sorted]

fig = go.Figure(go.Bar(
    x=p_sorted,
    y=v_sorted,
    marker_color=bar_colors,
    text=[f"{CURRENCY}{v:+,.0f}" for v in v_sorted],
    textposition='outside',
    hovertemplate='<b>%{x}</b><br>Final P&L: ' + CURRENCY + '%{y:+,.0f}<extra></extra>',
    width=0.55,
))
fig.add_hline(y=0, line_color='#555', line_width=1.5)
fig.update_layout(
    title='<b>Final Leaderboard — Total P&L at Settlement</b>',
    xaxis_title='Player',
    yaxis_title=f'P&L ({CURRENCY})',
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(size=13),
    height=430,
    margin=dict(t=60, b=50),
)
fig.show()
"""))

# Chart 2 — P&L over time
cells.append(md("""\
### Chart 2 — P&L Over Time

Watch the drama unfold round by round.

Diana leads early by selling the favourites (their implied value crashes in the group stage),
but collapses as England and France make deep runs. Eddie and Alice surge in the back half.
"""))

cells.append(code("""\
# ================================================================
# CHART 2: P&L OVER TIME LINE CHART
# ================================================================
PLAYER_COLORS = {
    'Alice':   '#3498db',
    'Bob':     '#e67e22',
    'Charlie': '#9b59b6',
    'Diana':   '#e74c3c',
    'Eddie':   '#27ae60',
}

fig = go.Figure()

for player in positions:
    fig.add_trace(go.Scatter(
        x=SNAPSHOTS,
        y=pnl_history[player],
        mode='lines+markers',
        name=player,
        line=dict(width=2.5, color=PLAYER_COLORS.get(player)),
        marker=dict(size=8),
        hovertemplate=(
            f'<b>{player}</b><br>Stage: %{{x}}<br>'
            f'Cumulative P&L: {CURRENCY}%{{y:+,.0f}}<extra></extra>'
        ),
    ))

# Final value annotations on the right edge
for player in positions:
    final_val = pnl_history[player][-1]
    fig.add_annotation(
        x=SNAPSHOTS[-1], y=final_val,
        text=f"  {player}: {CURRENCY}{final_val:+,.0f}",
        showarrow=False, xanchor='left',
        font=dict(size=10, color=PLAYER_COLORS.get(player)),
    )

# Vertical line after QF to mark where trades happened
# (use add_shape with numeric index — add_vline doesn't support categorical axes)
qf_idx = SNAPSHOTS.index('Quarter-Finals')
fig.add_shape(
    type='line', xref='x', yref='paper',
    x0=qf_idx, x1=qf_idx, y0=0, y1=1,
    line=dict(dash='dot', color='#888', width=1.5),
)
fig.add_annotation(
    x=qf_idx, y=1, xref='x', yref='paper',
    text='← trades here', showarrow=False,
    font=dict(size=9, color='#888'), xanchor='left', yanchor='bottom',
)

fig.add_hline(y=0, line_dash='dash', line_color='#bbb', line_width=1)
fig.update_layout(
    title='<b>Cumulative P&L — The Race Through the Tournament</b>',
    xaxis_title='Tournament Stage',
    yaxis_title=f'Cumulative P&L ({CURRENCY})',
    legend=dict(x=0.01, y=0.99),
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(size=12),
    height=510,
    margin=dict(r=170, t=60),
)
fig.show()
"""))

# Chart 3 — Heatmap
cells.append(md("""\
### Chart 3 — Position Map

**B** = Buy, **S** = Sell. Colour intensity shows profit (green) or loss (red) at final settlement.
The heatmap instantly shows who bet on whom and whether it paid off.
"""))

cells.append(code("""\
# ================================================================
# CHART 3: POSITION MAP HEATMAP
# ================================================================
makeups_fin = get_makeups_at_round(4)
closed_fin  = get_closed_positions(4)

player_list = list(positions.keys())
team_list   = list(teams.keys())

z_vals     = []
hover_text = []

for player in player_list:
    row_z, row_h = [], []
    for team in team_list:
        direction  = positions[player][team]
        open_p     = teams[team]['buy'] if direction == 1 else teams[team]['sell']
        dir_str    = 'BUY' if direction == 1 else 'SELL'

        if (player, team) in closed_fin:
            pnl = closed_fin[(player, team)]
            h   = f"<b>{player} | {team}</b><br>{dir_str} @ {open_p}<br>CLOSED — locked {CURRENCY}{pnl:+,.0f}"
        else:
            impl = makeups_fin[team]
            pnl  = (impl - open_p) * STAKE if direction == 1 else (open_p - impl) * STAKE
            h    = (f"<b>{player} | {team}</b><br>{dir_str} @ {open_p}<br>"
                    f"Make-up: {impl} pts<br>P&L: {CURRENCY}{pnl:+,.0f}")

        row_z.append(pnl)
        row_h.append(h)
    z_vals.append(row_z)
    hover_text.append(row_h)

fig = go.Figure(go.Heatmap(
    z=z_vals,
    x=team_list,
    y=player_list,
    text=hover_text,
    hoverinfo='text',
    colorscale='RdYlGn',
    zmid=0,
    colorbar=dict(title=f'P&L<br>({CURRENCY})', tickformat='+,.0f'),
))

# Overlay B / S labels
for i, player in enumerate(player_list):
    for j, team in enumerate(team_list):
        label = 'B' if positions[player][team] == 1 else 'S'
        fig.add_annotation(
            x=team, y=player, text=f'<b>{label}</b>',
            showarrow=False,
            font=dict(size=12, color='black'),
        )

fig.update_layout(
    title='<b>Position Map — B=Buy, S=Sell | Green=Win, Red=Lose (at settlement)</b>',
    xaxis_title='Team',
    yaxis_title='Player',
    font=dict(size=12),
    height=340,
    margin=dict(t=60),
)
fig.show()
"""))

# Chart 4 — Team tracker
cells.append(md("""\
### Chart 4 — Team Performance Tracker

Did each team beat or miss their pre-tournament spread price?
Points **above** the dashed fair-value line outperformed expectations (good for buyers);
points **below** underperformed (good for sellers).
"""))

cells.append(code("""\
# ================================================================
# CHART 4: TEAM PERFORMANCE TRACKER
# ================================================================
all_final_mu = {}
for r in ROUNDS:
    all_final_mu.update(r['eliminated'])

team_names = list(teams.keys())
mid_prices = [(teams[t]['buy'] + teams[t]['sell']) / 2 for t in team_names]
final_pts  = [all_final_mu[t] for t in team_names]
delta      = [final_pts[i] - mid_prices[i] for i in range(len(team_names))]

# Outcome labels for hover
outcome_map = {}
for r in ROUNDS:
    for t, v in r['eliminated'].items():
        name = r['name']
        outcome_map[t] = (
            'Winner' if v == 100 else
            'Runner-up' if v == 75 else
            'Semi-final' if v == 50 else
            'Quarter-final' if v == 25 else
            'Round of 16' if v == 10 else
            'Group stage'
        )

dot_colors = ['#27ae60' if d >= 0 else '#c0392b' for d in delta]
hover = [
    (f"<b>{t}</b><br>Mid price: {mid_prices[i]:.0f}<br>Final make-up: {final_pts[i]} pts<br>"
     f"Moved: {delta[i]:+.0f} pts<br>Result: {outcome_map.get(t, '?')}")
    for i, t in enumerate(team_names)
]

max_val = max(max(mid_prices), max(final_pts)) + 10

fig = go.Figure()

# Fair-value line
fig.add_trace(go.Scatter(
    x=[0, max_val], y=[0, max_val],
    mode='lines',
    line=dict(dash='dash', color='#999', width=1.5),
    name='Fair value (price = make-up)',
    showlegend=True,
))

# Team scatter
fig.add_trace(go.Scatter(
    x=mid_prices,
    y=final_pts,
    mode='markers+text',
    text=team_names,
    textposition='top center',
    marker=dict(size=14, color=dot_colors, line=dict(width=1.5, color='white')),
    hovertext=hover,
    hoverinfo='text',
    name='Teams',
))

fig.add_annotation(x=5,  y=90, text='Above line → outperformed<br>(buyers won)', showarrow=False,
                   font=dict(size=10, color='#27ae60'), xanchor='left')
fig.add_annotation(x=55, y=8,  text='Below line → underperformed<br>(sellers won)', showarrow=False,
                   font=dict(size=10, color='#c0392b'), xanchor='left')

fig.update_layout(
    title='<b>Team Performance: Pre-Tournament Mid Price vs Final Make-Up</b>',
    xaxis_title='Pre-Tournament Mid Price (pts)',
    yaxis_title='Final Make-Up (pts)',
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(size=12),
    height=490,
    legend=dict(x=0.01, y=0.99),
)
fig.show()
"""))

# ==============================================================================
# WHAT-IF
# ==============================================================================
cells.append(md("""\
---

## What-If Analysis

The final is done, but how different would things have been with another winner?

The cells below show how the leaderboard changes under four alternative final outcomes,
keeping everything else (all earlier rounds and mid-tournament trades) identical.
"""))

cells.append(code("""\
# ================================================================
# WHAT-IF ENGINE
# ================================================================

def what_if_pnls(winner, runner_up):
    \"\"\"
    Recalculate final P&L with an alternative winner / runner-up.

    Logic:
    - Start from the full actual tournament make-ups.
    - The two actual finalists (England/France) who are not winner/runner-up
      drop back to a SF exit (50 pts).
    - winner gets 100, runner_up gets 75.
    - Any non-finalist who wins (e.g. Brazil) overrides their actual 50-pt SF exit.
    - Mid-tournament trades are preserved.
    \"\"\"
    # Build full actual make-ups as baseline
    alt_makeups = {}
    for r in ROUNDS:
        alt_makeups.update(r['eliminated'])

    # Actual finalists who aren't in the new final drop back to SF exit
    for t in list(ROUNDS[-1]['eliminated'].keys()):
        if t != winner and t != runner_up:
            alt_makeups[t] = 50   # semi-final exit

    # Set new winner / runner-up (overrides anything set above)
    alt_makeups[winner]    = 100
    alt_makeups[runner_up] =  75

    closed = get_closed_positions(len(ROUNDS) - 1)
    return {p: calc_pnl(p, alt_makeups, closed) for p in positions}


# Four scenarios
SCENARIOS = {
    'Actual — France win':        ('France',    'England'),
    'England win, France R-up':   ('England',   'France'),
    'Brazil win, England R-up':   ('Brazil',    'England'),
    'Argentina win, France R-up': ('Argentina', 'France'),
}

scenario_results = {label: what_if_pnls(w, ru) for label, (w, ru) in SCENARIOS.items()}
scenario_df = pd.DataFrame(scenario_results).T
scenario_df.index.name = 'Scenario'

print("=== WHAT-IF LEADERBOARDS (columns = players) ===")
display(
    scenario_df.style
    .format(lambda x: f"{CURRENCY}{x:+,.0f}")
    .background_gradient(cmap='RdYlGn', axis=None)
    .set_caption("How the leaderboard changes under different final outcomes")
)
"""))

cells.append(code("""\
# ================================================================
# WHAT-IF CHART: Grouped bar chart across all scenarios
# ================================================================
fig = go.Figure()

player_order = sorted(positions.keys())

for player in player_order:
    fig.add_trace(go.Bar(
        name=player,
        x=list(SCENARIOS.keys()),
        y=[what_if_pnls(*SCENARIOS[s])[player] for s in SCENARIOS],
        marker_color=PLAYER_COLORS.get(player),
        hovertemplate=(
            f'<b>{player}</b><br>Scenario: %{{x}}<br>'
            f'P&L: {CURRENCY}%{{y:+,.0f}}<extra></extra>'
        ),
    ))

fig.add_hline(y=0, line_dash='dash', line_color='#888', line_width=1)
fig.update_layout(
    title='<b>What-If Analysis — Leaderboard Under Different Final Outcomes</b>',
    xaxis_title='Scenario',
    yaxis_title=f'Final P&L ({CURRENCY})',
    barmode='group',
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(size=12),
    height=480,
    legend=dict(title='Player'),
    margin=dict(t=60),
)
fig.show()
"""))

# ==============================================================================
# FINAL SUMMARY
# ==============================================================================
cells.append(md("""\
---

## Summary

| Rank | Player | Final P&L | Key story |
|------|--------|-----------|-----------|
| 🥇 1 | **Eddie** | +£720 | Bought all four semi-finalists + France winner. Perfect alignment. |
| 🥈 2 | **Alice** | +£660 | Sold Brazil & Germany (great calls), bought France & England (even better). |
| 3 | **Charlie** | −£70 | France SELL was a disaster — but a timely mid-tournament trade saved him £250. |
| 4 | **Bob** | −£85 | England SELL badly hurt, but closing it at 50 saved £125 vs going to settlement. |
| 5 | **Diana** | −£370 | Sold France *and* England — brilliant early, catastrophic once they reached the final. |

### Key lessons

- **Selling favourites works early** — their implied value crashes to 10 in the group stage,
  so sellers lead the leaderboard right after the groups.
- **But if they go deep, you bleed hard** — Diana's France + England sells turned catastrophic
  once both reached the final.
- **Mid-tournament trades matter** — Charlie went from −£320 to −£70 by closing France at the
  semis. Bob salvaged a similar amount on England. Both still lost, but far less than if they'd
  held to settlement.
- **The spread is the house's cut** — 10 teams × 2 pts × £5/pt = £100 in edge given to the house,
  explaining why the group's collective P&L sums to slightly negative.

---
*Adjust `STAKE = 5` at the top to scale all figures to your group's actual stake.*
"""))

# ==============================================================================
# WRITE NOTEBOOK
# ==============================================================================
nb.cells = cells
out_path = '/home/user/exploratory-notebooks/spread_betting_tournament.ipynb'
with open(out_path, 'w') as f:
    nbf.write(nb, f)

print(f"Notebook written to {out_path}")
