"""Orchestrator context coordinating subsystems and loops."""

import sys
import time
from random import choice, randint
from pathlib import Path
import pygame
import numpy as np

import src.settings as settings
from src.assets import AssetRegistry
from src.screens.menu import StartingScreen
from src.screens.pause import PauseScreen
from src.screens.game_over import GameOver
from src.screens.player_name import PlayerName
from src.screens.options import Options
from src.screens.controls import Controls
from src.screens.highscores import Highscores

from src.entities.player import PlayerShip
from src.entities.star import Star
from src.entities.enemy import Enemy
from src.entities.obstacle import Obstacle
from src.entities.powerups import (
    ShieldPowerup, HealthPowerup, EnergyPowerup
)
from src.entities.explosion import Explosion

# =========================================================================
# PORTER INTEGRATION: RETRO-BRIDGE RENDERING UTILITIES
# =========================================================================
# We import the custom top-down projection viewport, VoxelSurface
# proxy, camera properties, and specialized groups to route parent
# drawing contexts directly into the 3D rendering pipeline.
# =========================================================================
from porter.group import VoxelSpriteGroup, VoxelGroupSingle
from porter.viewport import PortViewport, VoxelSurface
from porter.porter_settings import (
    PORTER_CAMERA_HEIGHT,
    PORTER_CAMERA_YAW,
    PORTER_CAMERA_PITCH,
)


class SafeSound:
    """Wrapper to prevent audio channel saturation and clipping."""

    def __init__(self, path: Path, max_overlap: int = 3) -> None:
        """Initialize the sound wrapper with a maximum overlap."""
        self.sound: pygame.mixer.Sound = pygame.mixer.Sound(str(path))
        self.max_overlap: int = max_overlap

    def play(self, loops: int = 0, fade_ms: int = 0) -> None:
        """Play sound safely if overlap limits are not exceeded."""
        if self.sound.get_num_channels() < self.max_overlap:
            self.sound.play(loops=loops, fade_ms=fade_ms)

    def set_volume(self, value: float) -> None:
        """Set audio volume."""
        self.sound.set_volume(value)

    def fadeout(self, time: int) -> None:
        """Fade out audio."""
        self.sound.fadeout(time)


class Game:
    """The master game manager class encapsulating active session state."""

    def __init__(self) -> None:
        """Initialize context, window displays, timers, and sprite groups."""
        pygame.init()
        pygame.mixer.init()

        raw_screen: pygame.Surface = pygame.display.set_mode(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        )
        pygame.display.set_caption("Space Flight")

        # =====================================================================
        # PORTER INTEGRATION: SURFACE PROXY INTERCEPTION HOOK
        # =====================================================================
        # Instead of binding directly to a standard Pygame screen, we
        # wrap it in our custom VoxelSurface proxy. This intercepts both
        # .blit() and .blits() calls to redirect standard 2D sprite draws
        # into the 3D rendering pipeline.
        # =====================================================================
        self.viewport: PortViewport = PortViewport(
            raw_screen,
            float(settings.SCREEN_WIDTH),
            float(settings.SCREEN_HEIGHT),
        )
        self.screen: VoxelSurface = VoxelSurface(raw_screen, self.viewport)

        icon_path: Path = (
            settings.GRAPHICS_DIR / "artwork" / "joe mini logo.png"
        )
        if icon_path.exists():
            icon: pygame.Surface = pygame.image.load(
                str(icon_path)
            ).convert_alpha()
            pygame.display.set_icon(icon)

        # Initialize the centralized asset loading pipeline
        self.assets: AssetRegistry = AssetRegistry()

        # Ensure directory persistence
        self._ensure_highscore_files()

        # Engine states
        self.game_init: bool = True
        self.music_started: bool = False
        self.game_state: str = "start"
        self.game_speed: float = 1.0
        self.score: int = 0
        self.difficulty: int = settings.DIFFICULTY_MEDIUM
        self.player_name: str = ""

        # UI Font registry with absolute fallback mechanisms
        font_fallbacks: list[str] = [
            "Agency FB", "Century Gothic", "Arial", "sans-serif"
        ]
        local_font_path: Path = (
            settings.GRAPHICS_DIR / "fonts" / "font.ttf"
        )

        if local_font_path.exists():
            self.font_1: pygame.font.Font = pygame.font.Font(
                str(local_font_path), 20
            )
            self.font_2: pygame.font.Font = pygame.font.Font(
                str(local_font_path), 48
            )
            self.font_3: pygame.font.Font = pygame.font.Font(
                str(local_font_path), 72
            )
        else:
            self.font_1 = pygame.font.SysFont(font_fallbacks, 20)
            self.font_2 = pygame.font.SysFont(font_fallbacks, 48)
            self.font_3 = pygame.font.SysFont(font_fallbacks, 72)

        # Load Audio Sound Systems
        self.sound_menu_music: SafeSound = self._load_sound(
            "menu music.mp3"
        )
        self.sound_menu_music.set_volume(0.1)
        self.sound_game_music: SafeSound = self._load_sound(
            "game music.mp3"
        )
        self.sound_game_music.set_volume(0.1)
        self.sound_player_laser_shot: SafeSound = self._load_sound(
            "player laser shot.wav"
        )
        self.sound_ufo_laser_hit: SafeSound = self._load_sound(
            "ufo laser hit.wav"
        )
        self.sound_powerup: SafeSound = self._load_sound("powerup.wav")
        self.sound_ufo_explosion: SafeSound = self._load_sound(
            "ufo explosion.wav"
        )
        self.sound_rock_explosion: SafeSound = self._load_sound(
            "rock explosion.wav"
        )
        self.sound_ufo_laser_shot: SafeSound = self._load_sound(
            "ufo laser shot.wav"
        )

        self.clock: pygame.time.Clock = pygame.time.Clock()

        # Telemetry tracking variables for standard 2D overlay comparison
        self._last_time: float = time.perf_counter()
        self._smoothed_fps: float = float(settings.FPS)
        self._fps_history: list[tuple[float, float]] = []

        # WASM-safe inline timer boundaries (tracking timestamps in ms)
        self.current_time: int = 0
        self.next_enemy_spawn: int = 0
        self.next_obstacle_spawn: int = 0
        self.next_powerup_spawn: int = 0

        # Organize Sprite Group Entities
        self.start_menu: pygame.sprite.GroupSingle = (
            pygame.sprite.GroupSingle(StartingScreen(self))
        )
        self.options: pygame.sprite.GroupSingle = (
            pygame.sprite.GroupSingle()
        )
        self.controls: pygame.sprite.GroupSingle = (
            pygame.sprite.GroupSingle()
        )
        self.highscores: pygame.sprite.GroupSingle = (
            pygame.sprite.GroupSingle()
        )
        self.game_over: pygame.sprite.GroupSingle = (
            pygame.sprite.GroupSingle()
        )
        self.input_name: pygame.sprite.GroupSingle = (
            pygame.sprite.GroupSingle()
        )
        self.pause: pygame.sprite.GroupSingle = (
            pygame.sprite.GroupSingle()
        )

        # =====================================================================
        # PORTER INTEGRATION: SPECIALIZED SPRITE GROUP INJECTION
        # =====================================================================
        # We inject specialized voxel sprite groups ONLY for primary parent
        # hulls (ship, enemies, obstacles). These anchors feed their actual
        # physical Sprite object references to the parent pipeline to handle
        # 3D coordinate mapping, passive velocity-tilt, and attachments.
        # =====================================================================
        self.ship = VoxelGroupSingle(viewport=self.viewport)
        self.enemies = VoxelSpriteGroup(viewport=self.viewport)
        self.obstacles = VoxelSpriteGroup(viewport=self.viewport)

        # Standard independent overlays remain standard 2D Pygame groups
        self.player_shots: pygame.sprite.Group = pygame.sprite.Group()
        self.player_shield: pygame.sprite.GroupSingle = (
            pygame.sprite.GroupSingle()
        )
        self.enemy_shots: pygame.sprite.Group = pygame.sprite.Group()
        self.stars: pygame.sprite.Group = pygame.sprite.Group()
        self.powerups: pygame.sprite.Group = pygame.sprite.Group()
        self.explosions: pygame.sprite.Group = pygame.sprite.Group()

    def _load_sound(self, filename: str) -> SafeSound:
        """Load Sound wrapping with safe fallbacks."""
        path: Path = settings.SOUND_DIR / filename
        return SafeSound(path)

    def _ensure_highscore_files(self) -> None:
        """Autocreates missing highscore directory files."""
        settings.HIGHSCORES_DIR.mkdir(parents=True, exist_ok=True)
        for diff in ("easy", "medium", "hard"):
            n_file: Path = settings.HIGHSCORES_DIR / f"{diff} names.txt"
            s_file: Path = settings.HIGHSCORES_DIR / f"{diff} scores.txt"
            if not n_file.exists():
                with open(n_file, "w") as f:
                    f.write(
                        "UNUSED\n"
                        + "\n".join(["--empty--"] * 10)
                        + "\n"
                    )
            if not s_file.exists():
                with open(s_file, "w") as f:
                    f.write(
                        "999999999\n"
                        + "\n".join([str(10 - i) for i in range(10)])
                        + "\n"
                    )

    def test_highscore(self, score: int, difficulty_setting: int) -> bool:
        """Check if the session score qualifies for the leaderboard."""
        diff: str = self.get_difficulty_name(difficulty_setting)
        score_path: Path = settings.HIGHSCORES_DIR / f"{diff} scores.txt"
        with open(score_path, "r") as f:
            board_scores: list[str] = f.readlines()
        return score > int(board_scores[10].strip())

    def place_highscore(
        self, name: str, score: int, difficulty_setting: int
    ) -> None:
        """Insert high score entry into persistence files."""
        # Clean trailing spaces and fallback to a default safe anon string
        cleaned_name: str = name.strip()
        if not cleaned_name:
            cleaned_name = "--ANON--"

        diff: str = self.get_difficulty_name(difficulty_setting)
        score_path: Path = settings.HIGHSCORES_DIR / f"{diff} scores.txt"
        name_path: Path = settings.HIGHSCORES_DIR / f"{diff} names.txt"

        with open(score_path, "r") as f:
            board_scores: list[str] = f.readlines()
        with open(name_path, "r") as f:
            board_names: list[str] = f.readlines()

        for i in range(10, 0, -1):
            score_val = int(board_scores[i].strip())
            prev_val = int(board_scores[i - 1].strip())
            if score_val < score <= prev_val:
                board_scores.insert(i, f"{score}\n")
                board_scores.pop()
                board_names.insert(i, f"{cleaned_name}\n")
                board_names.pop()

        with open(score_path, "w") as f:
            f.writelines(board_scores)
        with open(name_path, "w") as f:
            f.writelines(board_names)

    def get_difficulty_name(self, value: int) -> str:
        """Translate difficulty integer setting into directory naming."""
        if value == settings.DIFFICULTY_EASY:
            return "easy"
        if value == settings.DIFFICULTY_MEDIUM:
            return "medium"
        return "hard"

    def transition_to(self, state: str) -> None:
        """Transition game state and handle centralized routing."""
        self.start_menu.empty()
        self.options.empty()
        self.controls.empty()
        self.highscores.empty()
        self.game_over.empty()
        self.input_name.empty()
        self.pause.empty()

        self.game_state = state

        if state == "game":
            pygame.event.set_grab(True)
        else:
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)

        # Centralized reset of session score and name upon menu exit/entry
        if state == "start":
            self.score = 0
            self.player_name = ""
            self.start_menu.add(StartingScreen(self))
        elif state == "options":
            self.options.add(Options(self))
        elif state == "controls":
            self.controls.add(Controls(self))
        elif state == "highscores":
            self.highscores.add(Highscores(self))
        elif state == "pause":
            self.pause.add(PauseScreen(self))
        elif state == "game over":
            self.game_over.add(GameOver(self))
        elif state == "input name":
            self.input_name.add(PlayerName(self))

    def start_game(self) -> None:
        """Configure session play buffers and play in-game audio."""
        self.sound_menu_music.fadeout(2000)
        self.sound_game_music.play(loops=-1, fade_ms=2000)
        self.transition_to("game")
        self.ship.add(PlayerShip(self))
        pygame.mouse.set_pos(self.ship.sprite.rect.center)

        # Initialize timing timestamps relative to start tick
        now: int = pygame.time.get_ticks()
        self.next_enemy_spawn = now + 2000
        self.next_obstacle_spawn = now + randint(1000, 2500)
        self.next_powerup_spawn = now + randint(10000, 25000)

    def trigger_pause(self) -> None:
        """Freeze combat and transition to standard paused HUD state."""
        self.transition_to("pause")

    def resume_game(self) -> None:
        """Unfreeze simulation and return context cursor mapping."""
        self.transition_to("game")
        pygame.mouse.set_pos(self.ship.sprite.rect.center)

    def trigger_game_over(self) -> None:
        """Purge play vectors and redirect to scoreboard submission."""
        self.ship.empty()
        self.player_shield.empty()
        self.player_shots.empty()
        self.powerups.empty()
        self.enemies.empty()
        self.enemy_shots.empty()
        self.obstacles.empty()
        self.explosions.empty()

        # Reset global speed multiplier back to baseline immediately on death
        self.game_speed = 1.0

        self.transition_to("game over")

    def handle_events(self) -> None:
        """Execute central single-frame inputs and state mappings."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.shutdown()

            # Unlock browser audio context on first interactive touch
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                if not self.music_started and self.game_state == "start":
                    self.sound_menu_music.play(loops=-1)
                    self.music_started = True

            is_focus_lost: bool = False
            if event.type == pygame.ACTIVEEVENT:
                if hasattr(event, "gain") and event.gain == 0:
                    if hasattr(event, "state") and event.state == 2:
                        is_focus_lost = True
            elif event.type == pygame.WINDOWFOCUSLOST:
                is_focus_lost = True

            if is_focus_lost and self.game_state == "game":
                self.trigger_pause()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == "game":
                        self.trigger_pause()
                    elif self.game_state == "pause":
                        self.resume_game()

            if self.game_state == "input name":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    elif event.key == pygame.K_RETURN:
                        self.place_highscore(
                            self.player_name, self.score, self.difficulty
                        )
                        self.transition_to("start")
                    else:
                        if len(self.player_name) <= settings.MAX_NAME_LENGTH:
                            char: str = event.unicode.upper()
                            if char in settings.LEGAL_LETTERS:
                                self.player_name += char

    def update(self, dt: float) -> None:
        """Compute logical motion, custom timers, and animation ticks."""
        if self.game_init:
            for _ in range(35):
                start_y: int = randint(
                    -25, settings.SCREEN_HEIGHT + 25
                )
                self.stars.add(Star(self, y_pos=start_y))
            self.game_init = False

        if len(self.stars) <= 35:
            self.stars.add(Star(self))

        self.stars.update(dt)

        self.current_time = pygame.time.get_ticks()

        if self.game_state == "start":
            self.player_name = ""
            self.start_menu.update(dt)
        elif self.game_state == "options":
            self.options.update(dt)
        elif self.game_state == "controls":
            self.controls.update(dt)
        elif self.game_state == "highscores":
            self.highscores.update(dt)
        elif self.game_state == "pause":
            self.pause.update(dt)
        elif self.game_state == "game":
            if self.score > self.difficulty:
                self.game_speed = 1.0 + self.score / self.difficulty / 25.0

            # Dynamic game speed scaling factor (damped)
            scaling_factor: float = (
                settings.BASE_GAME_SPEED_SCALING_DAMPENER
                + self.game_speed
            ) / (
                settings.BASE_GAME_SPEED_SCALING_DAMPENER
                + settings.INITIAL_GAME_SPEED
            )

            # Custom clock spawning threshold evaluations
            if self.current_time >= self.next_enemy_spawn:
                self.enemies.add(Enemy(self))
                self.next_enemy_spawn = self.current_time + int(
                    2000 / scaling_factor
                )

            if self.current_time >= self.next_obstacle_spawn:
                self.obstacles.add(Obstacle(self))
                min_delay: int = int(1000 / scaling_factor)
                max_delay: int = int(3000 / scaling_factor)
                self.next_obstacle_spawn = (
                    self.current_time + randint(min_delay, max_delay)
                )

            if self.current_time >= self.next_powerup_spawn:
                choice_pow = choice(
                    [
                        ShieldPowerup(self),
                        HealthPowerup(self),
                        EnergyPowerup(self),
                    ]
                )
                self.powerups.add(choice_pow)
                
                # Dynamic Powerup Spawn rate scaling
                next_delay: float = randint(
                    settings.BASE_POWERUP_SPAWN_RATE_MIN,
                    settings.BASE_POWERUP_SPAWN_RATE_MAX
                ) / scaling_factor
                
                self.next_powerup_spawn = (
                    self.current_time + int(next_delay)
                )

            self.explosions.update(dt)
            self.obstacles.update(dt)
            self.enemies.update(dt)
            self.enemy_shots.update(dt)
            self.player_shots.update(dt)
            self.powerups.update(dt)
            self.ship.update(dt)
            self.player_shield.update(dt)
        elif self.game_state == "game over":
            self.game_over.update(dt)
        elif self.game_state == "input name":
            self.input_name.update(dt)

    def draw(self) -> None:
        """Renders all layer objects to the screen."""

        # =====================================================================
        # PORTER INTEGRATION: PASS 1 - DRAW DISTANT 2D BACKGROUND
        # =====================================================================
        # We wipe the viewport and its accumulation queues, then draw the
        # flat, distant 2D background starfield layers.
        # =====================================================================
        self.viewport.clear()
        self.stars.draw(self.screen)

        if self.game_state == "start":
            self.start_menu.draw(self.screen)
            if self.start_menu.sprite:
                self.start_menu.sprite.draw_extras(self.screen)
        elif self.game_state == "options":
            self.options.draw(self.screen)
            if self.options.sprite:
                self.options.sprite.draw_extras(self.screen)
        elif self.game_state == "controls":
            self.controls.draw(self.screen)
            if self.controls.sprite:
                self.controls.sprite.draw_extras(self.screen)
        elif self.game_state == "highscores":
            self.highscores.draw(self.screen)
            if self.highscores.sprite:
                self.highscores.sprite.draw_extras(self.screen)
        elif self.game_state == "pause":
            self.pause.draw(self.screen)
        elif self.game_state == "game":
            self.explosions.draw(self.screen)
            self.obstacles.draw(self.screen)
            self.enemies.draw(self.screen)

            # =================================================================
            # PORTER INTEGRATION: PASS 2 - ACTIVE CONTEXT LOCKS (UFO)
            # =================================================================
            # Before calling 'draw_extras', we bind the active parent ID in
            # the viewport. This ensures that any subsequent blits (such as
            # dynamic light animations) are stitched to this specific UFO.
            # =================================================================
            for enemy in self.enemies:
                self.viewport.active_parent_id = id(enemy)
                enemy.draw_extras(self.screen)
            self.viewport.active_parent_id = None

            self.enemy_shots.draw(self.screen)
            self.player_shots.draw(self.screen)
            self.powerups.draw(self.screen)
            self.ship.draw(self.screen)

            # =================================================================
            # PORTER INTEGRATION: PASS 2 - ACTIVE CONTEXT LOCKS (PLAYER)
            # =================================================================
            # Bind the active parent ID to the player ship before executing
            # its extras. This ensures exhaust flames align with the ship.
            # =================================================================
            if self.ship.sprite:
                self.viewport.active_parent_id = id(self.ship.sprite)
                self.ship.sprite.draw_extras(self.screen)
            self.viewport.active_parent_id = None

            self.player_shield.draw(self.screen)
        elif self.game_state == "game over":
            self.game_over.draw(self.screen)
            if self.game_over.sprite:
                self.game_over.sprite.draw_extras(self.screen)
        elif self.game_state == "input name":
            self.input_name.draw(self.screen)
            if self.input_name.sprite:
                self.input_name.sprite.draw_extras(self.screen)

        # =====================================================================
        # PORTER INTEGRATION: PASS 3 - EXECUTE 3.5D PROJECTION RENDER PASS
        # =====================================================================
        # This triggers the rasterizer. All enqueued 3D parent cores and
        # stitched attachments are projected, sorted, shaded, and drawn.
        # =====================================================================
        self.viewport.render_3d_layer(
            cam_pos=np.array(
                [16.0, 16.0, PORTER_CAMERA_HEIGHT], dtype=np.float64
            ),
            yaw=PORTER_CAMERA_YAW,
            pitch=PORTER_CAMERA_PITCH,
            fov=600.0,
        )

        # Draw standard performance diagnostic panel in the lower-right
        if settings.SHOW_FPS:
            self._render_diagnostic_fps()

        pygame.display.update()

    def _render_diagnostic_fps(self) -> None:
        """Samples frame intervals and draws real-time telemetry."""
        current_time: float = time.perf_counter()
        delta_sec: float = current_time - self._last_time
        self._last_time = current_time

        delta_sec = max(0.0001, delta_sec)
        raw_fps: float = 1.0 / delta_sec

        alpha = 0.05
        self._smoothed_fps = (
            (self._smoothed_fps * (1.0 - alpha)) + (raw_fps * alpha)
        )

        self._fps_history.append((current_time, raw_fps))

        cutoff = current_time - 5.0
        self._fps_history = [
            item for item in self._fps_history if item[0] >= cutoff
        ]

        raw_values = [item[1] for item in self._fps_history]
        min_fps = min(raw_values) if raw_values else raw_fps
        max_fps = max(raw_values) if raw_values else raw_fps

        fps_text_1: str = f"Avg FPS: {self._smoothed_fps:5.1f}"
        fps_text_2: str = f"Min/Max: {min_fps:5.1f} - {max_fps:5.1f}"

        fps_surf_1 = self.font_1.render(fps_text_1, True, (0, 255, 0))
        fps_surf_2 = self.font_1.render(fps_text_2, True, (0, 255, 0))

        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        text_w = max(fps_surf_1.get_width(), fps_surf_2.get_width())
        h1 = fps_surf_1.get_height()
        h2 = fps_surf_2.get_height()
        text_h = h1 + h2 + 4

        pad = 6
        box_w = text_w + (pad * 2)
        box_h = text_h + (pad * 2)
        
        # Position box at the lower-right corner
        box_x = screen_w - box_w - 10
        box_y = screen_h - box_h - 10

        bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_surf.fill((20, 20, 20, 180))
        pygame.draw.rect(
            bg_surf, (100, 100, 100, 200), (0, 0, box_w, box_h), 1
        )

        self.screen.blit(bg_surf, (box_x, box_y))
        self.screen.blit(fps_surf_1, (box_x + pad, box_y + pad))
        self.screen.blit(fps_surf_2, (box_x + pad, box_y + pad + h1 + 4))

    def shutdown(self) -> None:
        """Terminate subsystems safely and exit execution."""
        pygame.quit()
        sys.exit()

    def run(self) -> None:
        """Synchronous main execution loop running on the desktop."""
        while True:
            dt: float = self.clock.tick(settings.FPS) / 1000.0
            dt = min(dt, 0.1)

            self.handle_events()
            self.update(dt)
            self.draw()
