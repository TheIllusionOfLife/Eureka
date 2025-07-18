import pygame
from enemy import Enemy

class Boss(Enemy):
    def __init__(self, pos, groups, obstacle_sprites, player):
        super().__init__(pos, groups, obstacle_sprites, player)
        self.image = pygame.image.load('../assets/images/boss.png').convert_alpha()
        self.rect = self.image.get_rect(topleft = pos)
        self.speed = 1
        self.health = 100
