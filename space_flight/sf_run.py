"""The modernized 3.5D hybrid edition of Space Flight."""

import os
import sys
import pygame
import numpy as np
from random import randint, uniform, choice
from pathlib import Path
from numpy.typing import NDArray

# Inject the project root into sys.path to support direct python execution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from porter.viewport import PortViewport

# 1. Initialize file-relative workspace directories
GAME_ROOT: Path = Path(__file__).resolve().parent
GRAPHICS_DIR: Path = GAME_ROOT / "graphics"
SOUND_DIR: Path = GAME_ROOT / "sound"
SCORE_DIR: Path = GAME_ROOT / "highscores"


class StartingScreen(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.options_clicked = False
        self.controls_clicked = False
        self.highscores_clicked = False
        global score
        score = 0

        self.image = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "game title.png")
        ).convert_alpha()
        self.rect = self.image.get_rect(topleft=(0, 0))

        self.start_game = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "start.png")
        ).convert_alpha()

        self.controls = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "controls.png")
        ).convert_alpha()

        self.highscores = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "highscores.png")
        ).convert_alpha()

        self.quit = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "quit.png")
        ).convert_alpha()

    def animations(self):
        screen.blit(self.start_game, (120, 345))
        screen.blit(self.controls, (120, 450))
        screen.blit(self.highscores, (120, 555))
        screen.blit(self.quit, (120, 660))

    def interaction(self):
        global game_state
        if pygame.mouse.get_pressed(3) == (True, False, False):
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(120, 680) and m_pos[1] in range(345, 435):
                self.options_clicked = True

            if m_pos[0] in range(120, 680) and m_pos[1] in range(450, 540):
                self.controls_clicked = True

            if m_pos[0] in range(120, 680) and m_pos[1] in range(555, 645):
                self.highscores_clicked = True

            if m_pos[0] in range(120, 680) and m_pos[1] in range(660, 750):
                pygame.quit()
                sys.exit()

        if self.options_clicked and pygame.mouse.get_pressed(3) == (False, False, False):
            game_state = "options"
            start_menu.empty()
            options.add(Options())

        if self.controls_clicked and pygame.mouse.get_pressed(3) == (False, False, False):
            game_state = "controls"
            start_menu.empty()
            controls.add(Controls())

        if self.highscores_clicked and pygame.mouse.get_pressed(3) == (False, False, False):
            game_state = "highscores"
            start_menu.empty()
            highscores.add(Highscores())

    def update(self):
        self.animations()
        self.interaction()


class Controls(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.back_clicked = False

        self.image = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "controls page.png")
        ).convert_alpha()
        self.rect = self.image.get_rect(topleft=(0, 0))

        self.back = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "back.png")
        ).convert_alpha()

    def animations(self):
        screen.blit(self.back, (285, 640))

    def interaction(self):
        global game_state
        if pygame.mouse.get_pressed(3) == (True, False, False):
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(285, 515) and m_pos[1] in range(640, 730):
                self.back_clicked = True

        if self.back_clicked and pygame.mouse.get_pressed(3) == (False, False, False):
            game_state = "start"
            controls.empty()
            start_menu.add(StartingScreen())

    def update(self):
        self.animations()
        self.interaction()


class Highscores(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.show = "medium"
        self.back_clicked = False
        self.left_clicked = False
        self.right_clicked = False

        self.image = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / f"{self.show} title.png")
        ).convert_alpha()
        self.rect = self.image.get_rect(
            topleft=(screen_width / 2 - self.image.get_width() / 2, 25)
        )

        self.arrow_left = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "arrow left.png")
        ).convert_alpha()
        self.arrow_right = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "arrow right.png")
        ).convert_alpha()
        self.back = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "back.png")
        ).convert_alpha()

        highscore_name = open(str(SCORE_DIR / f"{self.show} names.txt"), "r")
        name_list_reader = highscore_name.readlines()
        name_list_formatter = "".join(name_list_reader)
        self.names = name_list_formatter.split()

        highscore_score = open(str(SCORE_DIR / f"{self.show} scores.txt"), "r")
        score_list_reader = highscore_score.readlines()
        score_list_formatter = "".join(score_list_reader)
        self.scores = score_list_formatter.split()

    def animations(self):
        self.image = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / f"{self.show} title.png")
        ).convert_alpha()
        self.rect = self.image.get_rect(
            topleft=(screen_width / 2 - self.image.get_width() / 2, 25)
        )

        if self.show in ("medium", "hard"):
            screen.blit(self.arrow_left, (0, 300))
        if self.show in ("medium", "easy"):
            screen.blit(self.arrow_right, (720, 300))
        screen.blit(self.back, (285, 640))

        pygame.draw.rect(screen, (140, 255, 251), (100, 178, 604, 434), 2)
        pygame.draw.line(screen, (140, 255, 251), (400, 180), (400, 610), 2)

        for y_pos, name in enumerate(self.names[1:11]):
            screen.blit(
                font_1.render(name, True, (14, 209, 69)),
                (220, 190 + y_pos * 42)
            )
            if y_pos < 9:
                pygame.draw.line(
                    screen, (140, 255, 251),
                    (100, 222 + y_pos * 42), (700, 222 + y_pos * 42)
                )

        for y_pos, number in enumerate(self.scores[1:11]):
            screen.blit(
                font_1.render(number, True, (14, 209, 69)),
                (550 - len(number) * 7 / 2, 190 + y_pos * 42)
            )

    def interaction(self):
        global game_state

        if pygame.mouse.get_pressed(3) == (True, False, False):
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(0, 80) and m_pos[1] in range(300, 435):
                self.left_clicked = True

        if self.left_clicked and pygame.mouse.get_pressed(3) == (False, False, False):
            if self.show == "hard":
                self.show = "medium"
            elif self.show == "medium":
                self.show = "easy"
            self.change_site()
            self.left_clicked = False

        if pygame.mouse.get_pressed(3) == (True, False, False):
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(720, 800) and m_pos[1] in range(300, 435):
                self.right_clicked = True

        if self.right_clicked and pygame.mouse.get_pressed(3) == (False, False, False):
            if self.show == "easy":
                self.show = "medium"
            elif self.show == "medium":
                self.show = "hard"
            self.change_site()
            self.right_clicked = False

        if pygame.mouse.get_pressed(3) == (True, False, False):
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(285, 515) and m_pos[1] in range(640, 730):
                self.back_clicked = True

        if self.back_clicked and pygame.mouse.get_pressed(3) == (False, False, False):
            game_state = "start"
            highscores.empty()
            start_menu.add(StartingScreen())

    def change_site(self):
        highscore_name = open(str(SCORE_DIR / f"{self.show} names.txt"), "r")
        name_list_reader = highscore_name.readlines()
        name_list_formatter = "".join(name_list_reader)
        self.names = name_list_formatter.split()

        highscore_score = open(str(SCORE_DIR / f"{self.show} scores.txt"), "r")
        score_list_reader = highscore_score.readlines()
        score_list_formatter = "".join(score_list_reader)
        self.scores = score_list_formatter.split()

    def update(self):
        self.animations()
        self.interaction()


class Options(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.game_start_clicked = False

        img = pygame.image.load(str(GRAPHICS_DIR / "ship" / "ship 33x33.png"))
        self.image = pygame.transform.scale(img, (66, 66)).convert_alpha()
        self.rect = self.image.get_rect(
            midtop=(screen_width // 2, screen_height - 200)
        )

        exhaust_dir = GRAPHICS_DIR / "ship" / "exhaust"
        exhaust_images = os.listdir(str(exhaust_dir))
        exhaust_list = [
            pygame.image.load(str(exhaust_dir / img)) for img in exhaust_images
        ]
        self.exhaust_list = [
            pygame.transform.scale(img, (66, 66)).convert_alpha()
            for img in exhaust_list
        ]
        self.exhaust_index = 0
        self.exhaust_img = self.exhaust_list[self.exhaust_index]

        self.difficulty = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "select difficulty.png")
        ).convert_alpha()

        self.easy = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "easy.png")
        ).convert_alpha()
        self.easy_selected = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "easy on.png")
        ).convert_alpha()

        self.medium = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "medium.png")
        ).convert_alpha()
        self.medium_selected = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "medium on.png")
        ).convert_alpha()

        self.hard = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "hard.png")
        ).convert_alpha()
        self.hard_selected = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "hard on.png")
        ).convert_alpha()

        self.play_game = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "play game.png")
        ).convert_alpha()

    def animation(self):
        global difficulty, easy, medium, hard
        self.exhaust_index += 0.5
        if self.exhaust_index >= len(self.exhaust_list):
            self.exhaust_index = 0
        self.exhaust_img = self.exhaust_list[int(self.exhaust_index)]
        screen.blit(self.exhaust_img, (self.rect.x, self.rect.y + 50))

        if difficulty == easy:
            screen.blit(self.easy_selected, (235, 255))
        else:
            screen.blit(self.easy, (235, 255))

        if difficulty == medium:
            screen.blit(self.medium_selected, (235, 360))
        else:
            screen.blit(self.medium, (235, 360))

        if difficulty == hard:
            screen.blit(self.hard_selected, (235, 465))
        else:
            screen.blit(self.hard, (235, 465))

        screen.blit(self.difficulty, (0, 50))
        screen.blit(self.play_game, (140, 580))

    def interaction(self):
        global game_state
        if pygame.mouse.get_pressed(3) == (True, False, False):
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(235, 565) and m_pos[1] in range(255, 345):
                set_difficulty(easy)
            if m_pos[0] in range(235, 565) and m_pos[1] in range(360, 450):
                set_difficulty(medium)
            if m_pos[0] in range(235, 565) and m_pos[1] in range(465, 555):
                set_difficulty(hard)

            if m_pos[0] in range(140, 660) and m_pos[1] in range(580, 720):
                self.game_start_clicked = True

        if self.game_start_clicked and pygame.mouse.get_pressed(3) == (False, False, False):
            game_state = "game"
            menu_music.fadeout(2000)
            game_music.play(loops=-1, fade_ms=2000)
            options.empty()
            ship.add(PlayerShip())
            pygame.mouse.set_pos(ship.sprite.rect.center)

    def update(self):
        self.animation()
        self.interaction()


class PauseScreen(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.back_clicked = False

        self.image = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "back.png")
        ).convert_alpha()
        self.rect = self.image.get_rect(topleft=(285, 355))

    def interaction(self):
        global game_state
        pygame.mouse.set_visible(True)
        pressed = pygame.key.get_pressed()

        if pygame.mouse.get_pressed(3) == (True, False, False):
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(285, 515) and m_pos[1] in range(355, 445):
                self.back_clicked = True

        if pressed[pygame.K_ESCAPE]:
            self.back_clicked = True

        if self.back_clicked and pygame.mouse.get_pressed(3) == (False, False, False) and not pressed[pygame.K_ESCAPE]:
            game_state = "game"
            pygame.mouse.set_pos(ship.sprite.rect.center)
            pause.empty()

    def update(self):
        self.interaction()


class GameOver(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.nothing_clicked = False
        self.back_clicked = False

        self.image = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "game over.png")
        ).convert_alpha()
        self.rect = self.image.get_rect(topleft=(0, 100))

        self.final_score = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "final score.png")
        ).convert_alpha()

        self.back = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "back.png")
        ).convert_alpha()

        game_music.fadeout(2000)
        menu_music.play(loops=-1, fade_ms=2000)

    def animations(self):
        global score
        screen.blit(self.final_score, (0, 310))
        screen.blit(self.back, (285, 640))
        screen.blit(
            font_3.render(str(score), True, (140, 255, 251)),
            (screen_width / 2 - len(str(score)) * 12, 450)
        )

    def interaction(self):
        global game_state, score, difficulty
        if pygame.mouse.get_pressed(3) == (False, False, False):
            self.nothing_clicked = True
        if self.nothing_clicked:
            if pygame.mouse.get_pressed(3) == (True, False, False):
                m_pos = pygame.mouse.get_pos()
                if m_pos[0] in range(285, 515) and m_pos[1] in range(640, 730):
                    self.back_clicked = True

        if self.back_clicked and pygame.mouse.get_pressed(3) == (False, False, False):
            if test_highscore(score, difficulty):
                game_state = "input name"
                game_over.empty()
                input_name.add(PlayerName())
            else:
                game_state = "start"
                input_name.empty()
                start_menu.add(StartingScreen())

    def update(self):
        self.animations()
        self.interaction()


class PlayerName(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.submit_clicked = False
        self.player_name = ""

        self.image = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "game over.png")
        ).convert_alpha()
        self.rect = self.image.get_rect(topleft=(0, 100))

        self.new_highscore = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "new highscore.png")
        ).convert_alpha()
        self.enter_name = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "enter name.png")
        ).convert_alpha()
        self.enter = pygame.image.load(
            str(GRAPHICS_DIR / "artwork" / "enter.png")
        ).convert_alpha()

    def animations(self):
        global player_name
        screen.blit(self.new_highscore, (35, 260))
        screen.blit(self.enter_name, (25, 360))
        screen.blit(self.enter, (250, 640))
        self.player_name = font_3.render(player_name, True, (140, 255, 251))
        screen.blit(
            self.player_name,
            ((screen_width / 2 - self.player_name.get_width() / 2), 495)
        )
        pygame.draw.rect(screen, (140, 255, 251), (175, 493, 454, 94), 2)

    def interaction(self):
        global game_state, player_name, score, difficulty

        if pygame.mouse.get_pressed(3) == (True, False, False):
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(285, 515) and m_pos[1] in range(640, 730):
                self.submit_clicked = True

        if self.submit_clicked and pygame.mouse.get_pressed(3) == (False, False, False):
            place_highscore(player_name, score, difficulty)
            game_state = "start"
            input_name.empty()
            start_menu.add(StartingScreen())

    def update(self):
        self.animations()
        self.interaction()


class PlayerShip(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.score = None
        self.movement_speed = 10
        self.laser_cooldown = 0
        self.trigger_laser_fire = 0
        self.use_mouse = True
        self.activate_shield = True
        self.health = 10
        self.energy = 200
        self.pause_clicked = False
        self.dx_tilt = 0.0

        img = pygame.image.load(
            str(GRAPHICS_DIR / "ship" / "ship 33x33.png")
        )
        self.image = pygame.transform.scale(img, (66, 66)).convert_alpha()
        self.rect = self.image.get_rect(
            midtop=(screen_width // 2, screen_height - 200)
        )
        self.mask = pygame.mask.from_surface(self.image)

        light_dir = GRAPHICS_DIR / "ship" / "lights"
        light_images = os.listdir(str(light_dir))
        lights_list = [
            pygame.image.load(str(light_dir / img)) for img in light_images
        ]
        self.lights_list = [
            pygame.transform.scale(img, (42, 14)).convert_alpha()
            for img in lights_list
        ]
        self.lights_index = 0
        self.lights_img = self.lights_list[self.lights_index]

        exhaust_dir = GRAPHICS_DIR / "ship" / "exhaust"
        exhaust_images = os.listdir(str(exhaust_dir))
        exhaust_list = [
            pygame.image.load(str(exhaust_dir / img)) for img in exhaust_images
        ]
        self.exhaust_list = [
            pygame.transform.scale(img, (66, 66)).convert_alpha()
            for img in exhaust_list
        ]
        self.exhaust_index = 0
        self.exhaust_img = self.exhaust_list[self.exhaust_index]

        laser_dir = GRAPHICS_DIR / "ship" / "laser gun"
        laser_gun_images = os.listdir(str(laser_dir))
        laser_gun_list = [
            pygame.image.load(str(laser_dir / img)) for img in laser_gun_images
        ]
        self.laser_gun_list = [
            pygame.transform.scale(img, (66, 66)).convert_alpha()
            for img in laser_gun_list
        ]
        self.laser_gun_index = 0
        self.laser_gun_img = self.laser_gun_list[self.laser_gun_index]

        self.laser_shot_sound = pygame.mixer.Sound(
            str(SOUND_DIR / "player laser shot.wav")
        )
        self.laser_hit_sound = pygame.mixer.Sound(
            str(SOUND_DIR / "ufo laser hit.wav")
        )
        self.powerup_sound = pygame.mixer.Sound(
            str(SOUND_DIR / "powerup.wav")
        )
        self.ufo_explosion_sound = pygame.mixer.Sound(
            str(SOUND_DIR / "ufo explosion.wav")
        )
        self.rock_explosion_sound = pygame.mixer.Sound(
            str(SOUND_DIR / "rock explosion.wav")
        )

    def score_func(self):
        global score
        self.score = score
        screen.blit(
            font_2.render(str(self.score), True, (255, 255, 255)),
            (screen_width / 2 - len(str(score)) * 12, 0)
        )

    def health_func(self):
        global game_state
        if self.health <= 0:
            self.use_mouse = False
            game_state = "game over"
            ship.empty()
            player_shield.empty()
            player_shots.empty()
            powerups.empty()
            enemies.empty()
            enemy_shots.empty()
            obstacles.empty()
            explosions.empty()
            game_over.add(GameOver())

    def controls(self):
        global game_state
        pressed = pygame.key.get_pressed()

        # Keyboard/Mouse Toggle
        if pressed[pygame.K_k]:
            self.use_mouse = False
        if pressed[pygame.K_m]:
            self.use_mouse = True

        target_tilt = 0.0

        # Handle Movement controls
        if not self.use_mouse:
            pygame.mouse.set_visible(True)
            if pressed[pygame.K_LEFT]:
                self.rect.x -= self.movement_speed
                target_tilt = -1.0
            if pressed[pygame.K_RIGHT]:
                self.rect.x += self.movement_speed
                target_tilt = 1.0
            if pressed[pygame.K_UP]:
                self.rect.y -= self.movement_speed
            if pressed[pygame.K_DOWN]:
                self.rect.y += self.movement_speed
        else:
            pygame.mouse.set_visible(False)
            old_x = self.rect.centerx
            self.rect.center = pygame.mouse.get_pos()
            # Map lateral pixel displacement to a target banking ratio
            displacement = self.rect.centerx - old_x
            target_tilt = np.clip(displacement * 0.1, -1.0, 1.0)

        # Apply smooth linear interpolation (lerping) to dynamic banking roll
        self.dx_tilt += (target_tilt - self.dx_tilt) * 0.15

        # Boundary checks
        if self.rect.left < 25:
            self.rect.left = 25
        if self.rect.right > screen_width - 25:
            self.rect.right = screen_width - 25
        if self.rect.top < screen_height // 2:
            self.rect.top = screen_height // 2
        if self.rect.bottom > screen_height - 50:
            self.rect.bottom = screen_height - 50

        # Laser gun controls
        if self.laser_cooldown < 25:
            self.laser_cooldown += 1
        if self.energy > 0:
            if pressed[pygame.K_SPACE] and self.laser_cooldown >= 25 or \
                    pygame.mouse.get_pressed(3) == (True, False, False) and self.laser_cooldown >= 25:
                self.trigger_laser_fire = 1
            if self.trigger_laser_fire and self.laser_gun_index == 4:
                player_shots.add(PlayerLaserBeam())
                self.energy -= 1
                self.laser_cooldown = 0
                self.laser_shot_sound.play()
                self.laser_shot_sound.set_volume(0.2)

        if pressed[pygame.K_ESCAPE]:
            self.pause_clicked = True
        if self.pause_clicked and not pressed[pygame.K_ESCAPE]:
            game_state = "pause"
            pause.add(PauseScreen())
            self.pause_clicked = False

    def animations(self):
        # Viewport Draw Hook
        # Intercept 2D Blit and redirect ship to 3D pipeline
        if not viewport.draw_actor(
            screen, "ship 33x33.png", self.rect.center, 0.0, self.dx_tilt
        ):
            screen.blit(self.image, self.rect)

        self.lights_index += 1
        if self.lights_index >= len(self.lights_list):
            self.lights_index = 0
        self.lights_img = self.lights_list[int(self.lights_index)]
        screen.blit(self.lights_img, (self.rect.x + 12, self.rect.y + 38))

        self.exhaust_index += 0.5
        if self.exhaust_index >= len(self.exhaust_list):
            self.exhaust_index = 0
        self.exhaust_img = self.exhaust_list[int(self.exhaust_index)]
        screen.blit(self.exhaust_img, (self.rect.x, self.rect.y + 50))

        if self.energy > 0:
            if self.trigger_laser_fire:
                self.laser_gun_index += 1
                if self.laser_gun_index >= len(self.laser_gun_list):
                    self.laser_gun_index = 0
                    self.trigger_laser_fire = 0
                self.laser_gun_img = self.laser_gun_list[int(self.laser_gun_index)]
                screen.blit(self.laser_gun_img, (self.rect.x, self.rect.y - 42))

        pygame.draw.rect(screen, (0, 130, 0), (8, 11, 256, 29), 2)
        for i in range(1, 6):
            pygame.draw.line(
                screen, (0, 130 + i * 25, 0), (10, 25),
                (11 + self.health * 25, 25), 30 - i * 5
            )
        pygame.draw.rect(screen, (0, 0, 130), (screen_width - 263, 11, 256, 29), 2)
        for i in range(1, 6):
            pygame.draw.line(
                screen, (0, 0, 130 + i * 25),
                (screen_width - 11 - self.energy * 1.25, 25),
                (screen_width - 10, 25), 30 - i * 5
            )

    def collision(self):
        for laser_beam in enemy_shots:
            if pygame.sprite.collide_rect(self, laser_beam):
                if pygame.sprite.collide_mask(self, laser_beam):
                    laser_beam.kill()
                    if self.health > 0:
                        self.health -= 1
                    self.laser_hit_sound.play()
                    self.laser_hit_sound.set_volume(0.1)
                    explosions.add(Explosion([laser_beam.rect.x, laser_beam.rect.right],
                                             [laser_beam.rect.y, laser_beam.rect.bottom], False))

        for enemy in enemies:
            if pygame.sprite.collide_rect(self, enemy):
                if pygame.sprite.collide_mask(self, enemy):
                    enemy.kill()
                    if self.health > 0:
                        self.health -= 1
                    self.ufo_explosion_sound.play()
                    self.ufo_explosion_sound.set_volume(0.2)
                    explosions.add(Explosion([enemy.rect.x, enemy.rect.right], [enemy.rect.y, enemy.rect.bottom], True))

        for obstacle in obstacles:
            if pygame.sprite.collide_rect(self, obstacle):
                if pygame.sprite.collide_mask(self, obstacle):
                    obstacle.kill()
                    if self.health > 0:
                        self.health -= 1
                    self.rock_explosion_sound.play()
                    self.rock_explosion_sound.set_volume(0.2)
                    explosions.add(Explosion([obstacle.rect.x, obstacle.rect.right],
                                             [obstacle.rect.y, obstacle.rect.bottom], True))

        for powerup in powerups:
            if pygame.sprite.collide_rect(self, powerup):
                if pygame.sprite.collide_mask(self, powerup):
                    self.powerup_sound.play()
                    self.powerup_sound.set_volume(0.2)
                    if type(powerup) == ShieldPowerup:
                        powerup.kill()
                        player_shield.add(PlayerShield())
                    if type(powerup) == HealthPowerup:
                        powerup.kill()
                        self.health += 5
                        if self.health >= 10:
                            self.health = 10
                    if type(powerup) == EnergyPowerup:
                        powerup.kill()
                        self.energy += 100
                        if self.energy >= 200:
                            self.energy = 200

    def update(self):
        self.score_func()
        self.health_func()
        self.controls()
        self.animations()
        self.collision()


class PlayerLaserBeam(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        laser_dir = GRAPHICS_DIR / "ship" / "laser beam"
        laser_beam_images = os.listdir(str(laser_dir))
        laser_beam_list = [
            pygame.image.load(str(laser_dir / img)) for img in laser_beam_images
        ]
        self.laser_beam_list = [
            pygame.transform.scale(img, (14, 22)).convert_alpha()
            for img in laser_beam_list
        ]
        self.laser_beam_index = 0
        self.image = self.laser_beam_list[self.laser_beam_index]
        self.rect = self.image.get_rect(midbottom=ship.sprite.rect.midtop)
        self.mask = pygame.mask.from_surface(self.image, threshold=1)

    def animations(self):
        self.laser_beam_index += 1
        if self.laser_beam_index >= len(self.laser_beam_list):
            self.laser_beam_index = 0
        self.image = self.laser_beam_list[int(self.laser_beam_index)]

    def movement(self):
        self.rect.y -= 10
        if self.rect.bottom < 0:
            self.kill()

    def update(self):
        self.animations()
        self.movement()


class PlayerShield(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.shield_health = 5

        shield_dir = GRAPHICS_DIR / "ship" / "shield"
        images = os.listdir(str(shield_dir))
        image_list = [
            pygame.image.load(str(shield_dir / img)) for img in images
        ]
        self.image_list = [
            pygame.transform.scale(img, (98, 98)).convert_alpha()
            for img in image_list
        ]
        self.image_index = 0
        self.image = self.image_list[self.image_index]
        self.rect = self.image.get_rect(
            center=(ship.sprite.rect.centerx, ship.sprite.rect.centery + 9)
        )
        self.mask = pygame.mask.from_surface(self.image, threshold=1)

        self.laser_hit_sound = pygame.mixer.Sound(
            str(SOUND_DIR / "ufo laser hit.wav")
        )
        self.ufo_explosion_sound = pygame.mixer.Sound(
            str(SOUND_DIR / "ufo explosion.wav")
        )
        self.rock_explosion_sound = pygame.mixer.Sound(
            str(SOUND_DIR / "rock explosion.wav")
        )

    def animation(self):
        self.rect = self.image.get_rect(
            center=(ship.sprite.rect.centerx, ship.sprite.rect.centery + 9)
        )
        self.image_index += 0.1
        if self.image_index >= len(self.image_list):
            self.image_index = 0
        self.image = self.image_list[int(self.image_index)]

    def collision(self):
        for laser_beam in enemy_shots:
            if pygame.sprite.collide_rect(self, laser_beam):
                if pygame.sprite.collide_mask(self, laser_beam):
                    laser_beam.kill()
                    self.shield_health -= 1
                    self.laser_hit_sound.play()
                    self.laser_hit_sound.set_volume(0.1)
                    explosions.add(Explosion([laser_beam.rect.x, laser_beam.rect.right],
                                             [laser_beam.rect.y, laser_beam.rect.bottom], False))

        for enemy in enemies:
            if pygame.sprite.collide_rect(self, enemy):
                if pygame.sprite.collide_mask(self, enemy):
                    enemy.kill()
                    self.shield_health -= 1
                    self.ufo_explosion_sound.play()
                    self.ufo_explosion_sound.set_volume(0.2)
                    explosions.add(Explosion([enemy.rect.x, enemy.rect.right], [enemy.rect.y, enemy.rect.bottom], True))

        for obstacle in obstacles:
            if pygame.sprite.collide_rect(self, obstacle):
                if pygame.sprite.collide_mask(self, obstacle):
                    obstacle.kill()
                    self.shield_health -= 1
                    self.rock_explosion_sound.play()
                    self.rock_explosion_sound.set_volume(0.2)
                    explosions.add(Explosion([obstacle.rect.x, obstacle.rect.right],
                                             [obstacle.rect.y, obstacle.rect.bottom], True))

        if self.shield_health <= 0:
            self.kill()

    def update(self):
        self.animation()
        self.collision()


class ShieldPowerup(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        pw_dir = GRAPHICS_DIR / "powerups" / "powerup shield"
        images = os.listdir(str(pw_dir))
        self.image_list = [
            pygame.image.load(str(pw_dir / img)).convert_alpha()
            for img in images
        ]
        self.image_index = 0
        self.image = self.image_list[self.image_index]
        self.rect = self.image.get_rect(
            center=(randint(50, screen_width - 50), - 50)
        )
        self.mask = pygame.mask.from_surface(self.image)

    def animation(self):
        self.image_index += 0.5
        if self.image_index >= len(self.image_list):
            self.image_index = 0
        self.image = self.image_list[int(self.image_index)]

    def movement(self):
        self.rect.y += 5
        if self.rect.top > screen_height:
            self.kill()

    def update(self):
        self.animation()
        self.movement()


class HealthPowerup(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        pw_dir = GRAPHICS_DIR / "powerups" / "powerup health"
        images = os.listdir(str(pw_dir))
        self.image_list = [
            pygame.image.load(str(pw_dir / img)).convert_alpha()
            for img in images
        ]
        self.image_index = 0
        self.image = self.image_list[self.image_index]
        self.rect = self.image.get_rect(
            center=(randint(50, screen_width - 50), - 50)
        )
        self.mask = pygame.mask.from_surface(self.image)

    def animation(self):
        self.image_index += 0.25
        if self.image_index >= len(self.image_list):
            self.image_index = 0
        self.image = self.image_list[int(self.image_index)]

    def movement(self):
        self.rect.y += 5
        if self.rect.top > screen_height:
            self.kill()

    def update(self):
        self.animation()
        self.movement()


class EnergyPowerup(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        pw_dir = GRAPHICS_DIR / "powerups" / "powerup energy"
        images = os.listdir(str(pw_dir))
        self.image_list = [
            pygame.image.load(str(pw_dir / img)).convert_alpha()
            for img in images
        ]
        self.image_index = 0
        self.image = self.image_list[self.image_index]
        self.rect = self.image.get_rect(
            center=(randint(50, screen_width - 50), - 50)
        )
        self.mask = pygame.mask.from_surface(self.image)

    def animation(self):
        self.image_index += 0.25
        if self.image_index >= len(self.image_list):
            self.image_index = 0
        self.image = self.image_list[int(self.image_index)]

    def movement(self):
        self.rect.y += 5
        if self.rect.top > screen_height:
            self.kill()

    def update(self):
        self.animation()
        self.movement()


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        global game_speed
        self.x_movement_speed = 6 * game_speed
        self.y_movement_speed = 1 * game_speed
        self.move_down_cooldown = 0
        self.distance_moved = 0
        self.move_down = False
        self.speed_change_cooldown = 0
        self.turn_direction = randint(0, 1)
        self.movement_direction = randint(0, 1)
        self.evading_chance = 50
        self.evaded = randint(0, 1)
        self.evasion_cooldown = 0
        self.trigger_laser_fire = 0
        self.laser_cooldown = randint(120, 240)

        img = pygame.image.load(
            str(GRAPHICS_DIR / "enemy" / "ufo 33x33.png")
        ).convert_alpha()
        self.image = pygame.transform.scale(img, (66, 66)).convert_alpha()
        self.rect = self.image.get_rect(
            midtop=(randint(75, screen_width - 75), -50)
        )
        self.mask = pygame.mask.from_surface(self.image)

        light_dir = GRAPHICS_DIR / "enemy" / "lights"
        light_images = os.listdir(str(light_dir))
        lights_list = [
            pygame.image.load(str(light_dir / img)) for img in light_images
        ]
        self.lights_list = [
            pygame.transform.scale(img, (66, 66)).convert_alpha()
            for img in lights_list
        ]
        self.lights_index = 0
        self.lights_img = self.lights_list[self.lights_index]

        laser_dir = GRAPHICS_DIR / "enemy" / "laser gun"
        laser_gun_images = os.listdir(str(laser_dir))
        laser_gun_list = [
            pygame.image.load(str(laser_dir / img)) for img in laser_gun_images
        ]
        self.laser_gun_list = [
            pygame.transform.scale(img, (66, 22)).convert_alpha()
            for img in laser_gun_list
        ]
        self.laser_gun_index = 0
        self.laser_gun_img = self.laser_gun_list[self.laser_gun_index]

        self.laser_shot_sound = pygame.mixer.Sound(
            str(SOUND_DIR / "ufo laser shot.wav")
        )
        self.explosion_sound = pygame.mixer.Sound(
            str(SOUND_DIR / "ufo explosion.wav")
        )

    def animations(self):
        # Viewport Draw Hook
        # Intercept 2D Blit and redirect UFO to 3D pipeline
        if not viewport.draw_actor(
            screen, "ufo 33x33.png", self.rect.center, 0.0, 0.0
        ):
            screen.blit(self.image, self.rect)

        if self.turn_direction:
            self.lights_index += 0.5
            if self.lights_index >= len(self.lights_list):
                self.lights_index = 0
            self.lights_img = self.lights_list[int(self.lights_index)]
        else:
            self.lights_index -= 0.5
            if self.lights_index <= 0:
                self.lights_index = len(self.lights_list) - 1
            self.lights_img = self.lights_list[int(self.lights_index)]
        screen.blit(self.lights_img, self.rect.topleft)

        if self.trigger_laser_fire:
            self.laser_gun_index += 0.5
            if self.laser_gun_index >= len(self.laser_gun_list):
                self.laser_gun_index = 0
                self.trigger_laser_fire = 0
            self.laser_gun_img = self.laser_gun_list[int(self.laser_gun_index)]
            screen.blit(self.laser_gun_img, (self.rect.x, self.rect.y + 58))

    def movement(self):
        global game_speed
        if self.rect.top < 75:
            self.rect.centery += self.y_movement_speed * 2

        if self.movement_direction:
            self.rect.centerx += self.x_movement_speed
        else:
            self.rect.centerx -= self.x_movement_speed

        for laser_beam in player_shots:
            if self.rect.left <= laser_beam.rect.centerx <= self.rect.right and laser_beam.rect.top > self.rect.centery:
                if self.evading_chance >= randint(0, 100) and not self.evaded:
                    self.movement_direction = not self.movement_direction
                    self.evaded = True

        if self.evaded:
            self.evasion_cooldown += 1
            if self.evasion_cooldown >= 150:
                self.evaded = False
                self.evasion_cooldown = 0

        self.speed_change_cooldown += 1
        if self.speed_change_cooldown >= 30:
            self.x_movement_speed = randint(3, 6) * game_speed
            self.speed_change_cooldown = 0

        self.move_down_cooldown += 1 * game_speed
        if self.move_down_cooldown >= 120:
            self.move_down_cooldown = 0
            self.move_down = True

        if self.move_down:
            self.rect.bottom += self.y_movement_speed
            self.distance_moved += 1 * self.y_movement_speed
            if self.distance_moved >= 75:
                self.distance_moved = 0
                self.move_down = False

        if self.rect.bottom <= screen_height // 2:
            if self.rect.left <= 25:
                self.movement_direction = True
            if self.rect.right >= screen_width - 25:
                self.movement_direction = False
        if self.rect.right <= 0 or self.rect.left >= screen_width:
            self.kill()

    def laser_fire(self):
        self.laser_cooldown -= 1
        if self.laser_cooldown <= 0:
            self.laser_cooldown = 0
            if self.rect.left <= ship.sprite.rect.right <= self.rect.right or \
                    self.rect.right >= ship.sprite.rect.left >= self.rect.left:
                self.trigger_laser_fire = 1
                self.laser_cooldown = randint(60, 90)
        if self.trigger_laser_fire and self.laser_gun_index == 4:
            enemy_shots.add(EnemyLaserBeam(self.rect.midbottom))
            self.laser_shot_sound.play()
            self.laser_shot_sound.set_volume(0.15)

    def collision(self):
        global score
        for laser_beam in player_shots:
            if self.rect.top >= 0:
                if pygame.sprite.collide_rect(self, laser_beam):
                    if pygame.sprite.collide_mask(self, laser_beam):
                        score += 100
                        laser_beam.kill()
                        self.explosion_sound.play()
                        self.explosion_sound.set_volume(0.2)
                        explosions.add(Explosion([self.rect.x, self.rect.right], [self.rect.y, self.rect.bottom], True))
                        self.kill()

    def update(self):
        self.animations()
        self.movement()
        self.laser_fire()
        self.collision()


class EnemyLaserBeam(pygame.sprite.Sprite):
    def __init__(self, pos):
        global game_speed
        self.movement_speed = 3 + (18 * game_speed / 6)
        self.pos = pos
        super().__init__()
        laser_dir = GRAPHICS_DIR / "enemy" / "laser beam"
        laser_beam_images = os.listdir(str(laser_dir))
        laser_beam_list = [
            pygame.image.load(str(laser_dir / img)) for img in laser_beam_images
        ]
        self.laser_beam_list = [
            pygame.transform.scale(img, (14, 22)).convert_alpha()
            for img in laser_beam_list
        ]
        self.laser_beam_index = 0
        self.image = self.laser_beam_list[self.laser_beam_index]
        self.rect = self.image.get_rect(midtop=pos)
        self.mask = pygame.mask.from_surface(self.image)

    def animations(self):
        self.laser_beam_index += 0.2
        if self.laser_beam_index >= len(self.laser_beam_list):
            self.laser_beam_index = 0
        self.image = self.laser_beam_list[int(self.laser_beam_index)]

    def movement(self):
        self.rect.y += self.movement_speed
        if self.rect.top > screen_height:
            self.kill()

    def update(self):
        self.animations()
        self.movement()


class Obstacle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        global game_speed
        self.speed_x = randint(0, 5) * game_speed
        self.speed_y = randint(2, 5) * game_speed
        self.direction_x = randint(0, 1)
        self.turn_direction = randint(0, 1)
        self.turn_speed = uniform(0.5, 1)

        rock_dir = GRAPHICS_DIR / "obstacles" / "rock"
        obstacle_images = os.listdir(str(rock_dir))
        obstacle_list = [
            pygame.image.load(str(rock_dir / img)) for img in obstacle_images
        ]
        self.obstacle_list = [
            pygame.transform.scale(img, (78, 78)).convert_alpha()
            for img in obstacle_list
        ]
        self.obstacle_index = 0
        self.image = self.obstacle_list[self.obstacle_index]
        self.rect = self.image.get_rect(
            center=(randint(-100, screen_width + 100), -50)
        )
        self.mask = pygame.mask.from_surface(self.image)

        self.explosion_sound = pygame.mixer.Sound(
            str(SOUND_DIR / "rock explosion.wav")
        )

    def animation(self):
        if self.turn_direction:
            self.obstacle_index += self.turn_speed
            if self.obstacle_index >= len(self.obstacle_list):
                self.obstacle_index = 0
            self.image = self.obstacle_list[int(self.obstacle_index)]
        else:
            self.obstacle_index -= self.turn_speed
            if self.obstacle_index <= 0:
                self.obstacle_index = len(self.obstacle_list) - 1
            self.image = self.obstacle_list[int(self.obstacle_index)]

    def movement(self):
        if self.direction_x:
            self.rect.x += self.speed_x
        else:
            self.rect.x -= self.speed_x
        self.rect.y += self.speed_y
        if self.rect.right >= screen_width + 150 or self.rect.x <= -150:
            self.speed_x = randint(2, 5) * game_speed
            self.speed_y = randint(2, 5) * game_speed
            self.direction_x = not self.direction_x
        if self.rect.top > screen_height:
            self.kill()

    def collision(self):
        global score
        for laser_beam in player_shots:
            if pygame.sprite.collide_rect(self, laser_beam):
                if pygame.sprite.collide_mask(self, laser_beam):
                    score += 10
                    laser_beam.kill()
                    self.explosion_sound.play()
                    self.explosion_sound.set_volume(0.2)
                    explosions.add(Explosion([self.rect.x, self.rect.right], [self.rect.y, self.rect.bottom], True))
                    self.kill()

    def update(self):
        self.animation()
        self.movement()
        self.collision()


class Explosion(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, original=False):
        super().__init__()
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.rand_pos_x = randint(pos_x[0], pos_x[1])
        self.rand_pos_y = randint(pos_y[0], pos_y[1])
        self.original = original

        exp_dir = GRAPHICS_DIR / "explosion"
        explosion_images = os.listdir(str(exp_dir))
        explosion_list = [
            pygame.image.load(str(exp_dir / img)) for img in explosion_images
        ]
        self.explosion_list = [
            pygame.transform.scale(img, (50, 50)).convert_alpha()
            for img in explosion_list
        ]
        self.explosion_index = 0
        self.image = self.explosion_list[self.explosion_index]
        self.rect = self.image.get_rect(center=(self.rand_pos_x, self.rand_pos_y))
        self.mask = pygame.mask.from_surface(self.image)

    def animation(self):
        self.explosion_index += 1
        if self.explosion_index >= len(self.explosion_list):
            self.explosion_index = len(self.explosion_list) - 1
            self.kill()
        self.image = self.explosion_list[int(self.explosion_index)]

        if self.original:
            explosions.add(Explosion(self.pos_x, self.pos_y))

    def update(self):
        self.animation()


class Star(pygame.sprite.Sprite):
    def __init__(self, y_pos=-50):
        super().__init__()
        
        s1_dir = GRAPHICS_DIR / "bg" / "star 1"
        star_1 = os.listdir(str(s1_dir))
        self.star_1_list = [
            pygame.image.load(str(s1_dir / img)) for img in star_1
        ]

        s2_dir = GRAPHICS_DIR / "bg" / "star 2"
        star_2 = os.listdir(str(s2_dir))
        self.star_2_list = [
            pygame.image.load(str(s2_dir / img)) for img in star_2
        ]

        s3_dir = GRAPHICS_DIR / "bg" / "star 3"
        star_3 = os.listdir(str(s3_dir))
        self.star_3_list = [
            pygame.image.load(str(s3_dir / img)) for img in star_3
        ]

        s4_dir = GRAPHICS_DIR / "bg" / "star 4"
        star_4 = os.listdir(str(s4_dir))
        self.star_4_list = [
            pygame.image.load(str(s4_dir / img)) for img in star_4
        ]

        self.all_stars_list = [self.star_1_list, self.star_2_list, self.star_3_list, self.star_4_list]

        self.star_index = randint(0, len(self.star_1_list) - 1)
        self.all_stars_index = randint(0, len(self.all_stars_list) - 1)
        self.star_distance = randint(0, 20)

        self.image = self.all_stars_list[self.all_stars_index][self.star_index]
        self.rect = self.image.get_rect(center=(randint(-25, screen_width + 25), y_pos))

        if self.star_distance in (0, 1, 2, 3, 4, 5):
            for num_1, star_list in enumerate(self.all_stars_list):
                for num_2, star in enumerate(star_list):
                    self.all_stars_list[num_1][num_2] = pygame.transform.scale(star, (13, 13)).convert_alpha()

        elif self.star_distance in (6, 7, 8, 9, 10):
            for num_1, star_list in enumerate(self.all_stars_list):
                for num_2, star in enumerate(star_list):
                    self.all_stars_list[num_1][num_2] = pygame.transform.scale(star, (26, 26)).convert_alpha()

        elif self.star_distance in (11, 12, 13, 14):
            for num_1, star_list in enumerate(self.all_stars_list):
                for num_2, star in enumerate(star_list):
                    self.all_stars_list[num_1][num_2] = pygame.transform.scale(star, (39, 39)).convert_alpha()

        if self.star_distance in (15, 16, 17):
            for num_1, star_list in enumerate(self.all_stars_list):
                for num_2, star in enumerate(star_list):
                    self.all_stars_list[num_1][num_2] = pygame.transform.scale(star, (52, 52)).convert_alpha()

        elif self.star_distance in (18, 19):
            for num_1, star_list in enumerate(self.all_stars_list):
                for num_2, star in enumerate(star_list):
                    self.all_stars_list[num_1][num_2] = pygame.transform.scale(star, (89, 89)).convert_alpha()

        elif self.star_distance == 20:
            for num_1, star_list in enumerate(self.all_stars_list):
                for num_2, star in enumerate(star_list):
                    self.all_stars_list[num_1][num_2] = pygame.transform.scale(star, (117, 117)).convert_alpha()

    def animation(self):
        self.star_index += 0.5
        if self.star_index >= len(self.star_1_list):
            self.star_index = 0
        self.image = self.all_stars_list[self.all_stars_index][int(self.star_index)]

    def movement(self):
        global game_speed
        if self.star_distance in (0, 1, 2, 3, 4, 5):
            self.rect.y += 1 * game_speed
        elif self.star_distance in (6, 7, 8, 9, 10):
            self.rect.y += 2 * game_speed
        elif self.star_distance in (11, 12, 13, 14):
            self.rect.y += 3 * game_speed
        elif self.star_distance in (15, 16, 17):
            self.rect.y += 4 * game_speed
        elif self.star_distance in (18, 19):
            self.rect.y += 5 * game_speed
        else:
            self.rect.y += 6 * game_speed
        if self.rect.top > screen_height:
            self.kill()

    def update(self):
        self.animation()
        self.movement()


def update_fps():
    fps = str(int(clock.get_fps()))
    fps_text = font_2.render(fps, True, (140, 255, 251))
    return fps_text


def test_highscore(actual_player_score, difficulty_setting):
    if difficulty_setting == 1000:
        diff = "easy"
    elif difficulty_setting == 500:
        diff = "medium"
    else:
        diff = "hard"
    highscore_scores = open(str(SCORE_DIR / f"{diff} scores.txt"), "r")
    board_scores = highscore_scores.readlines()
    highscore_scores.close()

    if actual_player_score > int(board_scores[10]):
        return True
    else:
        return False


def place_highscore(actual_player_name, actual_player_score, difficulty_setting):
    if difficulty_setting == 1000:
        diff = "easy"
    elif difficulty_setting == 500:
        diff = "medium"
    else:
        diff = "hard"
    highscore_scores = open(str(SCORE_DIR / f"{diff} scores.txt"), "r")
    board_scores = highscore_scores.readlines()
    highscore_scores.close()

    highscore_names = open(str(SCORE_DIR / f"{diff} names.txt"), "r")
    board_names = highscore_names.readlines()
    highscore_names.close()

    highscore_scores = open(str(SCORE_DIR / f"{diff} scores.txt"), "w")
    highscore_names = open(str(SCORE_DIR / f"{diff} names.txt"), "w")

    for board_place in range(10, 0, -1):
        if int(board_scores[board_place]) < actual_player_score <= int(board_scores[board_place - 1]):
            board_scores.insert(board_place, str(actual_player_score) + "\n")
            board_scores.pop()

            board_names.insert(board_place, str(actual_player_name) + "\n")
            board_names.pop()

    highscore_scores.writelines(board_scores)
    highscore_names.writelines(board_names)

    highscore_scores.close()
    highscore_names.close()


def set_difficulty(selected):
    global difficulty
    difficulty = selected


def update_enemy_timer():
    global game_speed
    pygame.time.set_timer(enemy_timer, int(2000 / game_speed))


def update_obstacle_timer():
    global game_speed
    pygame.time.set_timer(
        obstacle_timer,
        randint(int(1000 / game_speed), int(3000 / game_speed))
    )


pygame.init()

screen_width = 800
screen_height = 800
game_init = True
game_state = "start"
game_speed = 1
score = 0
easy = 1000
medium = 500
hard = 200
difficulty = medium
player_name = ""
legal_letters = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
                 "Q," "W", "E", "R", "T", "Z", "U", "I", "O", "P",
                 "A", "S", "D", "F", "G", "H", "J", "K", "L",
                 "Y", "X", "C", "V", "B", "N", "M")

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Space Flight")
icon = pygame.image.load(
    str(GRAPHICS_DIR / "artwork" / "joe mini logo.png")
).convert_alpha()
pygame.display.set_icon(icon)

# 2. Instantiate the modular 3D Viewport Bridge
viewport: PortViewport = PortViewport(screen, screen_width, screen_height)

# space_flight/space_flight_main.py (Section Replacement)
# High-precision top-down camera coordinates for 1:1 pixel locking
cam_yaw: float = 0.0
cam_pitch: float = -1.5707963267948966  # Looks straight down (-pi/2 rad)
camera_pos: NDArray[np.float64] = np.array(
    [16.0, 16.0, 25.0], dtype=np.float64
)

font_1 = pygame.font.SysFont("Agency FB", 20)
font_2 = pygame.font.SysFont("Agency FB", 48)
font_3 = pygame.font.SysFont("Agency FB", 72)

menu_music = pygame.mixer.Sound(str(SOUND_DIR / "menu music.mp3"))
menu_music.set_volume(0.1)
game_music = pygame.mixer.Sound(str(SOUND_DIR / "game music.mp3"))
game_music.set_volume(0.1)

clock = pygame.time.Clock()

enemy_timer = pygame.USEREVENT + 1
pygame.time.set_timer(enemy_timer, 2000)

obstacle_timer = pygame.USEREVENT + 2
pygame.time.set_timer(obstacle_timer, randint(1000, 2500))

powerup_timer = pygame.USEREVENT + 3
pygame.time.set_timer(powerup_timer, randint(10000, 25000))

start_menu = pygame.sprite.GroupSingle(StartingScreen())
options = pygame.sprite.GroupSingle()
controls = pygame.sprite.GroupSingle()
highscores = pygame.sprite.GroupSingle()
game_over = pygame.sprite.GroupSingle()
input_name = pygame.sprite.GroupSingle()
pause = pygame.sprite.GroupSingle()

ship = pygame.sprite.GroupSingle()
player_shots = pygame.sprite.Group()
player_shield = pygame.sprite.GroupSingle()

enemies = pygame.sprite.Group()
enemy_shots = pygame.sprite.Group()

obstacles = pygame.sprite.Group()
stars = pygame.sprite.Group()
powerups = pygame.sprite.Group()
explosions = pygame.sprite.Group()

while True:
    # Clear the 3D Drawing queues at the start of each frame
    viewport.clear()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if game_state == "game":
            if event.type == enemy_timer:
                enemies.add(Enemy())
                update_enemy_timer()

            if event.type == obstacle_timer:
                obstacles.add(Obstacle())
                update_obstacle_timer()

            if event.type == powerup_timer:
                powerups.add(choice([ShieldPowerup(), HealthPowerup(), EnergyPowerup()]))

        if game_state == "input name":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.key == pygame.K_RETURN:
                    place_highscore(player_name, score, difficulty)
                    game_state = "start"
                    input_name.empty()
                    start_menu.add(StartingScreen())
                else:
                    if len(player_name) <= 10:
                        player_name += event.unicode.upper() if event.unicode.upper() in legal_letters else player_name

    if game_init:
        menu_music.play(loops=-1)
        for _ in range(35):
            stars.add(Star(y_pos=randint(-25, screen_height + 25)))
        game_init = False

    if len(stars) <= 35:
        stars.add(Star())

    stars.draw(screen)
    stars.update()

    if game_state == "start":
        player_name = ""
        start_menu.draw(screen)
        start_menu.update()

    if game_state == "options":
        options.draw(screen)
        options.update()

    if game_state == "controls":
        controls.draw(screen)
        controls.update()

    if game_state == "highscores":
        highscores.draw(screen)
        highscores.update()

    if game_state == "pause":
        pause.draw(screen)
        pause.update()

    if game_state == "game":
        if score > difficulty:
            game_speed = 1 + score / difficulty / 25

        explosions.draw(screen)
        explosions.update()

        obstacles.draw(screen)
        obstacles.update()

        enemies.draw(screen)
        enemies.update()

        enemy_shots.draw(screen)
        enemy_shots.update()

        player_shots.draw(screen)
        player_shots.update()

        powerups.draw(screen)
        powerups.update()

        # Update entity groups (queues 3D meshes inside drawing routines)
        ship.update()
        enemies.update()

        # Render 3D Layer (Draws all queued voxel models with proper depth sorting)
        viewport.render_3d_layer(camera_pos, cam_yaw, cam_pitch, 600.0)

        # Draw transparent shields & overlay items on top
        player_shield.draw(screen)
        player_shield.update()

    if game_state == "game over":
        game_over.draw(screen)
        game_over.update()

    if game_state == "input name":
        input_name.draw(screen)
        input_name.update()

    pygame.display.update()
    clock.tick(60)
