import pygame

class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, direction, groups):
        super().__init__(groups)
        self.image = pygame.Surface((5,5))
        self.image.fill('white')
        self.rect = self.image.get_rect(center = pos)
        self.direction = direction
        self.speed = 10
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 1000

    def update(self):
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed

        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()
