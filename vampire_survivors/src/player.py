import pygame
from projectile import Projectile

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites, all_sprites, projectile_sprites, character):
        super().__init__(groups)
        self.image = pygame.image.load(character.image).convert_alpha()
        self.rect = self.image.get_rect(topleft = pos)

        self.direction = pygame.math.Vector2()
        self.speed = character.speed
        self.health = character.health

        self.obstacle_sprites = obstacle_sprites
        self.all_sprites = all_sprites
        self.projectile_sprites = projectile_sprites

        self.experience = 0
        self.level = 1
        self.experience_to_next_level = 100

    def input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP]:
            self.direction.y = -1
        elif keys[pygame.K_DOWN]:
            self.direction.y = 1
        else:
            self.direction.y = 0

        if keys[pygame.K_RIGHT]:
            self.direction.x = 1
        elif keys[pygame.K_LEFT]:
            self.direction.x = -1
        else:
            self.direction.x = 0

    def move(self,speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        self.rect.x += self.direction.x * speed
        self.collision('horizontal')
        self.rect.y += self.direction.y * speed
        self.collision('vertical')

    def collision(self,direction):
        if direction == 'horizontal':
            for sprite in self.obstacle_sprites:
                if sprite.rect.colliderect(self.rect):
                    if self.direction.x > 0: # moving right
                        self.rect.right = sprite.rect.left
                    if self.direction.x < 0: # moving left
                        self.rect.left = sprite.rect.right

        if direction == 'vertical':
            for sprite in self.obstacle_sprites:
                if sprite.rect.colliderect(self.rect):
                    if self.direction.y > 0: # moving down
                        self.rect.bottom = sprite.rect.top
                    if self.direction.y < 0: # moving up
                        self.rect.top = sprite.rect.bottom

    def update(self):
        self.input()
        self.move(self.speed)
        self.attack()

    def attack(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            Projectile((self.rect.centerx, self.rect.centery), self.direction, [self.all_sprites, self.projectile_sprites])
            # laser_sound = pygame.mixer.Sound('../assets/sounds/laser.wav')
            # laser_sound.play()

    def gain_experience(self, amount):
        self.experience += amount
        if self.experience >= self.experience_to_next_level:
            self.level += 1
            self.experience = 0
            self.experience_to_next_level *= 1.5
