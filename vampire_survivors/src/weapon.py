import pygame

class Weapon(pygame.sprite.Sprite):
    def __init__(self, player, groups):
        super().__init__(groups)
        self.player = player
        self.direction = pygame.math.Vector2(0,-1)
        self.image = pygame.Surface((10,10))
        self.image.fill('red')
        self.rect = self.image.get_rect(center = player.rect.center)

    def update(self):
        if self.player.direction.magnitude() != 0:
            self.direction = self.player.direction.copy()

        self.rect.center = self.player.rect.center + self.direction * 30
