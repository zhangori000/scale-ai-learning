from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

SUITS: List[str] = ["Clubs", "Diamonds", "Hearts", "Spades"]
RANKS: List[str] = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_TO_VALUE: Dict[str, int] = {rank: index for index, rank in enumerate(RANKS, start=2)}
FISH_POINT_BY_RANK: Dict[str, int] = {"5": 5, "10": 10, "K": 10}


@dataclass(frozen=True)
class Card:
    suit: str
    rank: str

    def __post_init__(self) -> None:
        if self.suit not in SUITS:
            raise ValueError(f"Unknown suit: {self.suit}")
        if self.rank not in RANKS:
            raise ValueError(f"Unknown rank: {self.rank}")

    def __str__(self) -> str:
        return f"{self.rank} of {self.suit}"


def build_standard_cards() -> List[Card]:
    return [Card(suit=suit, rank=rank) for suit in SUITS for rank in RANKS]


class Deck:
    def __init__(self, cards: Optional[Sequence[Card]] = None) -> None:
        self.cards: List[Card] = list(cards) if cards is not None else build_standard_cards()

    def shuffle(self, rng: Optional[random.Random] = None) -> None:
        if rng is None:
            random.shuffle(self.cards)
            return
        rng.shuffle(self.cards)

    def draw(self) -> Card:
        if not self.cards:
            raise ValueError("Cannot draw from an empty deck.")
        return self.cards.pop()

    def __len__(self) -> int:
        return len(self.cards)


@dataclass
class Player:
    name: str
    hand: List[Card] = field(default_factory=list)
    points: int = 0

    def receive_card(self, card: Card) -> None:
        self.hand.append(card)

    def has_suit(self, suit: str) -> bool:
        return any(card.suit == suit for card in self.hand)

    def play_card(self, lead_suit: Optional[str] = None, rng: Optional[random.Random] = None) -> Card:
        if not self.hand:
            raise ValueError(f"Player {self.name} has no cards left.")

        if lead_suit is not None:
            valid_indices = [index for index, card in enumerate(self.hand) if card.suit == lead_suit]
            if not valid_indices:
                valid_indices = list(range(len(self.hand)))
        else:
            valid_indices = list(range(len(self.hand)))

        chosen_index = valid_indices[0] if rng is None else rng.choice(valid_indices)
        return self.hand.pop(chosen_index)


@dataclass(frozen=True)
class PlayedCard:
    player_index: int
    player_name: str
    card: Card


@dataclass(frozen=True)
class TrickResult:
    starting_player_index: int
    lead_suit: str
    plays: Tuple[PlayedCard, ...]
    winner_index: int
    winner_name: str
    points_won: int


@dataclass(frozen=True)
class GameResult:
    tricks: Tuple[TrickResult, ...]
    final_scores: Dict[str, int]
    top_scorers: Tuple[str, ...]

    @property
    def rounds_played(self) -> int:
        return len(self.tricks)


def card_points(card: Card) -> int:
    return FISH_POINT_BY_RANK.get(card.rank, 0)


def create_players(count: int = 4) -> List[Player]:
    return [Player(name=str(index + 1)) for index in range(count)]


def deal_cards(deck: Deck, players: Sequence[Player], cards_per_player: int = 13) -> None:
    for _ in range(cards_per_player):
        for player in players:
            player.receive_card(deck.draw())


def play_trick(
    players: Sequence[Player],
    starting_player_index: int,
    rng: Optional[random.Random] = None,
    verbose: bool = True,
) -> TrickResult:
    if len(players) != 4:
        raise ValueError("This interview problem expects exactly 4 players.")

    play_order = [(starting_player_index + offset) % len(players) for offset in range(len(players))]
    plays: List[PlayedCard] = []
    lead_suit: Optional[str] = None

    for turn_index, player_index in enumerate(play_order):
        player = players[player_index]
        lead_for_turn = lead_suit if turn_index > 0 else None
        card = player.play_card(lead_suit=lead_for_turn, rng=rng)
        if lead_suit is None:
            lead_suit = card.suit

        played = PlayedCard(player_index=player_index, player_name=player.name, card=card)
        plays.append(played)
        if verbose:
            print(f"Player {player.name} played {card}")

    assert lead_suit is not None
    lead_suit_plays = [played for played in plays if played.card.suit == lead_suit]
    winning_play = max(lead_suit_plays, key=lambda item: RANK_TO_VALUE[item.card.rank])
    points_won = sum(card_points(item.card) for item in plays)
    players[winning_play.player_index].points += points_won

    if verbose:
        print(f"Winner: Player {winning_play.player_name}")
        print(f"Points won this trick: {points_won}")
        print()

    return TrickResult(
        starting_player_index=starting_player_index,
        lead_suit=lead_suit,
        plays=tuple(plays),
        winner_index=winning_play.player_index,
        winner_name=winning_play.player_name,
        points_won=points_won,
    )


def simulate_game(
    players: Sequence[Player],
    starting_player_index: int = 0,
    rng: Optional[random.Random] = None,
    verbose: bool = True,
) -> GameResult:
    if len(players) != 4:
        raise ValueError("This interview problem expects exactly 4 players.")

    tricks: List[TrickResult] = []
    next_start = starting_player_index

    while True:
        hand_sizes = {len(player.hand) for player in players}
        if hand_sizes == {0}:
            break
        if len(hand_sizes) != 1:
            raise ValueError("All players must have the same number of cards before each trick.")

        trick_result = play_trick(players=players, starting_player_index=next_start, rng=rng, verbose=verbose)
        tricks.append(trick_result)
        next_start = trick_result.winner_index

    final_scores = {player.name: player.points for player in players}
    max_score = max(final_scores.values(), default=0)
    top_scorers = tuple(name for name, score in final_scores.items() if score == max_score)

    if verbose:
        print("Final Scores")
        for player in players:
            print(f"Player {player.name}: {player.points}")

        if len(top_scorers) == 1:
            print(f"Top scorer: Player {top_scorers[0]}")
        else:
            label = ", ".join(f"Player {name}" for name in top_scorers)
            print(f"Top scorers: {label}")

    return GameResult(tricks=tuple(tricks), final_scores=final_scores, top_scorers=top_scorers)


def run_full_game(
    seed: Optional[int] = 2026,
    starting_player_index: int = 0,
    verbose: bool = True,
) -> GameResult:
    players = create_players(count=4)
    deck = Deck()
    rng = random.Random(seed) if seed is not None else random.Random()
    deck.shuffle(rng=rng)
    deal_cards(deck=deck, players=players, cards_per_player=13)
    return simulate_game(players=players, starting_player_index=starting_player_index, rng=rng, verbose=verbose)

