# Card Game Interview Practice (Parts 1-3)

This folder is a focused practice package for the card-game interview described in your screenshots and discussion thread.

## Problem framing

You simulate a 4-player game with a standard 52-card deck.

Part 1: Setup
- Build `Card`, `Deck`, and `Player` models.
- Shuffle and deal 13 cards to each player.
- Keep the model simple and readable.

Part 2: Trick Taking
- Pick a starting player.
- Starter can play any card.
- Other players must follow the starter suit if possible.
- If a player has no card in the starter suit, they can play any card.
- Print each move as:
  `Player {X} played {Card}`
- Trick winner = highest rank among cards in the starter suit.
- Winner becomes the next trick's starting player.
- Repeat until all players have no cards (13 tricks total in a full game).

Part 3: Scoring
- At each trick, winner takes points from all cards played in that trick:
  - `5` -> 5 points
  - `10` -> 10 points
  - `K` -> 10 points
  - all others -> 0
- At the end of each trick, print points won.
- At game end, print each player's total points.
- Print player name(s) with highest total points.

## Discussion-driven assumptions

Based on interview comments, this prep uses assumptions that often show up:
- You may be given starter classes (`Card`, `Deck`, `Player`) and asked to add helper functions.
- You are usually allowed to edit provided classes if needed.
- `RANKS` and `SUITS` may be plain strings, not enums.
- Strategy is not graded; rule-correct simulation is graded.
- This is usually not a classic LeetCode DS/Algo problem; it is object modeling + simulation + clean extension.

## Implementation files

- `card_game.py`
  - Full implementation for setup, trick-taking, and scoring.
  - Main entry points:
    - `run_full_game(seed=2026, starting_player_index=0, verbose=True)`
    - `simulate_game(players, starting_player_index=0, rng=None, verbose=True)`
    - `play_trick(players, starting_player_index, rng=None, verbose=True)`

- `demo.py`
  - Runs one full game and prints interview-style output.

- `test_card_game.py`
  - Unit tests for follow-suit rules, winner logic, scoring, and full-game completion.

## Expected input/output contract

Input:
- No stdin is required.
- `run_full_game` takes optional parameters:
  - `seed` (`int | None`) for deterministic card choices and shuffle.
  - `starting_player_index` (`0-3`) for first trick starter.
  - `verbose` (`bool`) for console output.

Output:
- Trick logs:
  - `Player {X} played {rank} of {suit}`
  - `Winner: Player {X}`
  - `Points won this trick: {points}`
- Final logs:
  - `Player {X}: {total_points}`
  - top scorer line

## What interviewers usually expect

- Correct rule handling (follow-suit, trick winner, next starter).
- Clean function decomposition.
- Stable rank comparison when ranks are strings.
- Reasonable test coverage.
- Ability to extend from Part 2 to Part 3 without rewriting everything.

## Quick run

From this folder:

```bash
python demo.py
python -m unittest test_card_game.py -v
```

