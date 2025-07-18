import pygame
import json

class Highscore:
    def __init__(self):
        self.highscore = 0
        self.load_highscore()

    def load_highscore(self):
        try:
            with open('highscore.json', 'r') as f:
                self.highscore = json.load(f)
        except FileNotFoundError:
            self.highscore = 0

    def save_highscore(self):
        with open('highscore.json', 'w') as f:
            json.dump(self.highscore, f)

    def set_highscore(self, score):
        if score > self.highscore:
            self.highscore = score
            self.save_highscore()
