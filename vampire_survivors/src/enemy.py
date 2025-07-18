import pygame

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites, player):
        super().__init__(groups)
        self.image = pygame.image.load('../assets/images/enemy.png').convert_alpha()
        self.rect = self.image.get_rect(topleft = pos)

        self.direction = pygame.math.Vector2()
        self.speed = 3
        self.player = player
        self.health = 1

        self.obstacle_sprites = obstacle_sprites

    def update(self):
        self.direction = (self.player.rect.center - self.rect.center).normalize()
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed
