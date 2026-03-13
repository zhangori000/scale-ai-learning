import random
import unittest

from card_game import Card, Deck, create_players, deal_cards, play_trick, simulate_game


class CardGameTests(unittest.TestCase):
    def test_follow_suit_rule(self) -> None:
        players = create_players()
        players[0].hand = [Card("Hearts", "2")]
        players[1].hand = [Card("Clubs", "A"), Card("Hearts", "3")]
        players[2].hand = [Card("Spades", "K")]
        players[3].hand = [Card("Hearts", "A")]

        result = play_trick(players=players, starting_player_index=0, verbose=False)
        by_player = {play.player_index: play.card for play in result.plays}

        self.assertEqual(by_player[1].suit, "Hearts")
        self.assertEqual(by_player[2].suit, "Spades")
        self.assertEqual(result.winner_index, 3)

    def test_winner_uses_lead_suit_only(self) -> None:
        players = create_players()
        players[0].hand = [Card("Hearts", "4")]
        players[1].hand = [Card("Hearts", "K")]
        players[2].hand = [Card("Spades", "A")]
        players[3].hand = [Card("Hearts", "10")]

        result = play_trick(players=players, starting_player_index=0, verbose=False)

        self.assertEqual(result.lead_suit, "Hearts")
        self.assertEqual(result.winner_index, 1)
        self.assertEqual(result.points_won, 20)
        self.assertEqual(players[1].points, 20)

    def test_full_game_runs_13_rounds_and_consumes_all_cards(self) -> None:
        players = create_players()
        deck = Deck()
        rng = random.Random(11)
        deck.shuffle(rng=rng)
        deal_cards(deck=deck, players=players, cards_per_player=13)

        result = simulate_game(players=players, starting_player_index=0, rng=rng, verbose=False)

        self.assertEqual(result.rounds_played, 13)
        self.assertTrue(all(len(player.hand) == 0 for player in players))
        self.assertEqual(sum(result.final_scores.values()), 100)
        self.assertGreaterEqual(len(result.top_scorers), 1)


if __name__ == "__main__":
    unittest.main()

