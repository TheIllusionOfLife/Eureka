import pygame, sys
from player import Player
from weapon import Weapon
from enemy import Enemy
from projectile import Projectile
from highscore import Highscore
from boss import Boss
from powerup import Powerup
from character import Character
import random

class Game:
    def __init__(self):
        pygame.init()
        # pygame.mixer.init()
        self.screen = pygame.display.set_mode((1280,720))
        pygame.display.set_caption('Vampire Survivors')
        self.clock = pygame.time.Clock()

        self.all_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.projectile_sprites = pygame.sprite.Group()
        self.powerup_sprites = pygame.sprite.Group()

        self.character = None

        self.enemy_spawn_timer = pygame.USEREVENT + 1
        pygame.time.set_timer(self.enemy_spawn_timer, 1000)

        self.boss_spawn_timer = pygame.USEREVENT + 2
        pygame.time.set_timer(self.boss_spawn_timer, 10000)

        self.powerup_spawn_timer = pygame.USEREVENT + 3
        pygame.time.set_timer(self.powerup_spawn_timer, 5000)

        # pygame.mixer.music.load('../assets/sounds/music.wav')
        # pygame.mixer.music.play(-1)

        self.score = 0
        self.highscore = Highscore()


    def spawn_enemy(self):
        x = random.randint(0, self.screen.get_width())
        y = random.randint(0, self.screen.get_height())
        Enemy((x,y), [self.all_sprites, self.enemy_sprites], self.obstacle_sprites, self.player)

    def spawn_boss(self):
        x = random.randint(0, self.screen.get_width())
        y = random.randint(0, self.screen.get_height())
        Boss((x,y), [self.all_sprites, self.enemy_sprites], self.obstacle_sprites, self.player)

    def spawn_powerup(self):
        x = random.randint(0, self.screen.get_width())
        y = random.randint(0, self.screen.get_height())
        Powerup((x,y), [self.all_sprites, self.powerup_sprites])

    def run(self):
        self.player = Player((640,360),[self.all_sprites],self.obstacle_sprites, self.all_sprites, self.projectile_sprites, self.character)
        self.weapon = Weapon(self.player,[self.all_sprites])
        self.playing = True
        while self.playing:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.paused = True
                        self.pause_menu()
                if event.type == self.enemy_spawn_timer:
                    self.spawn_enemy()
                if event.type == self.boss_spawn_timer:
                    self.spawn_boss()
                if event.type == self.powerup_spawn_timer:
                    self.spawn_powerup()

            self.screen.fill('black')
            self.all_sprites.draw(self.screen)
            self.all_sprites.update()
            self.check_collisions()
            self.draw_score()
            pygame.display.update()
            self.clock.tick(60)

    def check_collisions(self):
        # Projectiles and enemies
        for projectile in self.projectile_sprites:
            hits = pygame.sprite.spritecollide(projectile, self.enemy_sprites, False)
            for hit in hits:
                hit.health -= 1
                if hit.health <= 0:
                    hit.kill()
                    self.player.gain_experience(10)
                    self.score += 100
                projectile.kill()

        # Player and enemies
        hits = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False)
        if hits:
            self.player.kill()
            self.game_over()

        # Player and powerups
        hits = pygame.sprite.spritecollide(self.player, self.powerup_sprites, True)
        if hits:
            self.player.speed += 1

    def draw_score(self):
        font = pygame.font.Font(None, 36)
        text = font.render(f'Score: {self.score}', 1, (255, 255, 255))
        textpos = text.get_rect(topleft=(10, 10))
        self.screen.blit(text, textpos)

    def game_over(self):
        self.highscore.set_highscore(self.score)
        self.screen.fill('black')
        font = pygame.font.Font(None, 74)
        text = font.render('Game Over', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=300)
        self.screen.blit(text, textpos)
        font = pygame.font.Font(None, 36)
        text = font.render(f'Highscore: {self.highscore.highscore}', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=400)
        self.screen.blit(text, textpos)
        pygame.display.flip()
        pygame.time.wait(2000)
        pygame.quit()
        sys.exit()

    def title_screen(self):
        self.screen.fill('black')
        font = pygame.font.Font(None, 74)
        text = font.render('Vampire Survivors', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=300)
        self.screen.blit(text, textpos)
        font = pygame.font.Font(None, 36)
        text = font.render('Press any key to start', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=400)
        self.screen.blit(text, textpos)
        font = pygame.font.Font(None, 36)
        text = font.render('Press S for settings', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=450)
        self.screen.blit(text, textpos)
        font = pygame.font.Font(None, 36)
        text = font.render('Press C for credits', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=500)
        self.screen.blit(text, textpos)
        font = pygame.font.Font(None, 36)
        text = font.render('Press T for tutorial', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=550)
        self.screen.blit(text, textpos)
        pygame.display.flip()
        self.wait_for_key()

    def pause_menu(self):
        self.screen.fill('black')
        font = pygame.font.Font(None, 74)
        text = font.render('Paused', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=300)
        self.screen.blit(text, textpos)
        font = pygame.font.Font(None, 36)
        text = font.render('Press C to continue or Q to quit', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=400)
        self.screen.blit(text, textpos)
        pygame.display.flip()
        self.wait_for_pause()

    def settings_menu(self):
        self.screen.fill('black')
        font = pygame.font.Font(None, 74)
        text = font.render('Settings', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=300)
        self.screen.blit(text, textpos)
        font = pygame.font.Font(None, 36)
        text = font.render('Press B to go back', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=400)
        self.screen.blit(text, textpos)
        pygame.display.flip()
        self.wait_for_settings()

    def credits_screen(self):
        self.screen.fill('black')
        font = pygame.font.Font(None, 74)
        text = font.render('Credits', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=300)
        self.screen.blit(text, textpos)
        font = pygame.font.Font(None, 36)
        text = font.render('Created by Jules', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=400)
        self.screen.blit(text, textpos)
        font = pygame.font.Font(None, 36)
        text = font.render('Press B to go back', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=500)
        self.screen.blit(text, textpos)
        pygame.display.flip()
        self.wait_for_credits()

    def wait_for_credits(self):
        waiting = True
        while waiting:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.quit()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_b:
                        waiting = False
                        self.title_screen()

    def tutorial_screen(self):
        self.screen.fill('black')
        font = pygame.font.Font(None, 74)
        text = font.render('Tutorial', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=100)
        self.screen.blit(text, textpos)
        font = pygame.font.Font(None, 36)
        text = font.render('Use the arrow keys to move', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=200)
        self.screen.blit(text, textpos)
        text = font.render('Press the spacebar to shoot', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=250)
        self.screen.blit(text, textpos)
        text = font.render('Avoid the enemies', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=300)
        self.screen.blit(text, textpos)
        text = font.render('Kill enemies to gain experience and level up', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=350)
        self.screen.blit(text, textpos)
        text = font.render('Press B to go back', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=500)
        self.screen.blit(text, textpos)
        pygame.display.flip()
        self.wait_for_tutorial()

    def wait_for_tutorial(self):
        waiting = True
        while waiting:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.quit()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_b:
                        waiting = False
                        self.title_screen()

    def wait_for_settings(self):
        waiting = True
        while waiting:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.quit()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_b:
                        waiting = False
                        self.title_screen()

    def wait_for_pause(self):
        waiting = True
        while waiting:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.quit()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_c:
                        waiting = False
                    if event.key == pygame.K_q:
                        waiting = False
                        self.quit()

    def wait_for_key(self):
        waiting = True
        while waiting:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.quit()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_s:
                        self.settings_menu()
                    elif event.key == pygame.K_c:
                        self.credits_screen()
                    elif event.key == pygame.K_t:
                        self.tutorial_screen()
                    else:
                        waiting = False

    def quit(self):
        pygame.quit()
        sys.exit()


    def character_selection_screen(self):
        self.screen.fill('black')
        font = pygame.font.Font(None, 74)
        text = font.render('Choose your character', 1, (255, 255, 255))
        textpos = text.get_rect(centerx=self.screen.get_width()/2, y=100)
        self.screen.blit(text, textpos)

        self.characters = [
            Character('Player 1', '../assets/images/player.png', 5, 100),
            Character('Player 2', '../assets/images/player2.png', 7, 80)
        ]

        for i, character in enumerate(self.characters):
            font = pygame.font.Font(None, 36)
            text = font.render(character.name, 1, (255, 255, 255))
            textpos = text.get_rect(centerx=self.screen.get_width()/2, y=200 + i * 50)
            self.screen.blit(text, textpos)

        pygame.display.flip()
        self.wait_for_character_selection()

    def wait_for_character_selection(self):
        waiting = True
        while waiting:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.quit()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_1:
                        self.character = self.characters[0]
                        waiting = False
                    if event.key == pygame.K_2:
                        self.character = self.characters[1]
                        waiting = False


if __name__ == '__main__':
    game = Game()
    game.title_screen()
    game.character_selection_screen()
    game.run()
