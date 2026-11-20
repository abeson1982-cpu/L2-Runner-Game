"""
Speed Runner - Version A (Keyboard Edition)
Controls:
- SPACE or UP ARROW: Jump (jump over low obstacles)
- DOWN ARROW: Duck / Slide (duck under flying obstacles)
- R or SPACE (on Game Over): Restart game
- ESC: Quit game
"""

import sys
import os
import random
import math
import pygame

# Initialize Pygame & Mixer
pygame.init()
try:
    pygame.mixer.init()
    AUDIO_AVAILABLE = True
except Exception:
    AUDIO_AVAILABLE = False

# Screen Dimensions
WIDTH = 850
HEIGHT = 450
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Speed Runner - Version A (Keyboard Edition)")
CLOCK = pygame.time.Clock()
FPS = 60

# Colors
COLOR_SKY_TOP = (24, 28, 48)
COLOR_SKY_BOTTOM = (45, 52, 84)
COLOR_GROUND = (70, 78, 105)
COLOR_GROUND_LINE = (100, 110, 145)
COLOR_PLAYER = (255, 99, 71)      # Tomato Red
COLOR_PLAYER_HEAD = (255, 220, 180)
COLOR_PLAYER_BAND = (255, 215, 0) # Gold
COLOR_OBSTACLE_LOW = (46, 204, 113) # Emerald Green (Cactus/Spike)
COLOR_OBSTACLE_HIGH = (231, 76, 60) # Crimson Drone/Bat
COLOR_COIN = (255, 215, 0)        # Gold Coin
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (180, 180, 180)
COLOR_DARK_GRAY = (40, 40, 40)
COLOR_TEXT = (240, 240, 245)
COLOR_SHADOW = (20, 20, 30, 80)

# Fonts
FONT_TITLE = pygame.font.SysFont("arial", 42, bold=True)
FONT_BIG = pygame.font.SysFont("arial", 32, bold=True)
FONT_MED = pygame.font.SysFont("arial", 22, bold=True)
FONT_SMALL = pygame.font.SysFont("arial", 16)

# Generate Procedural Sound Effects using NumPy
SOUNDS = {}
if AUDIO_AVAILABLE:
    try:
        import numpy as np
        sample_rate = 44100

        def make_sound(wave_array):
            stereo_wave = np.repeat(wave_array[:, np.newaxis], 2, axis=1)
            return pygame.sndarray.make_sound(stereo_wave.astype(np.int16))

        # Jump Sound: frequency sweeps from 250Hz to 600Hz
        t_jump = np.linspace(0, 0.15, int(sample_rate * 0.15), False)
        f_jump = np.linspace(250, 650, len(t_jump))
        wave_jump = 16000 * np.sin(2 * np.pi * f_jump * t_jump) * np.linspace(1, 0, len(t_jump))
        SOUNDS["jump"] = make_sound(wave_jump)

        # Coin Sound: quick two-tone bell chime (987Hz -> 1318Hz)
        t_coin = np.linspace(0, 0.12, int(sample_rate * 0.12), False)
        wave_coin = 14000 * np.sin(2 * np.pi * 987 * t_coin) * np.linspace(1, 0.4, len(t_coin))
        t_coin2 = np.linspace(0, 0.18, int(sample_rate * 0.18), False)
        wave_coin2 = 14000 * np.sin(2 * np.pi * 1318 * t_coin2) * np.linspace(1, 0, len(t_coin2))
        SOUNDS["coin"] = make_sound(np.concatenate([wave_coin, wave_coin2]))

        # Crash Sound: white noise decay
        t_crash = np.linspace(0, 0.35, int(sample_rate * 0.35), False)
        noise = np.random.uniform(-1, 1, len(t_crash)) * np.linspace(1, 0, len(t_crash))
        SOUNDS["crash"] = make_sound(22000 * noise)

    except Exception:
        SOUNDS = {}


def play_sound(name):
    if name in SOUNDS:
        try:
            SOUNDS[name].play()
        except Exception:
            pass


# Ground & Physics
GROUND_Y = 360
GRAVITY = 0.95
JUMP_FORCE = -15.5


class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, radius=4, lifetime=25):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-2, 2)
        self.vy = vy if vy is not None else random.uniform(-2, 2)
        self.radius = radius
        self.lifetime = lifetime
        self.max_life = lifetime

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0:
            alpha_ratio = self.lifetime / self.max_life
            curr_r = max(1, int(self.radius * alpha_ratio))
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), curr_r)


class Player:
    def __init__(self):
        self.x = 90
        self.y = GROUND_Y
        self.standing_height = 60
        self.ducking_height = 30
        self.width = 36
        self.height = self.standing_height

        self.vy = 0
        self.is_jumping = False
        self.is_ducking = False
        self.anim_frame = 0

    def jump(self):
        if not self.is_jumping and not self.is_ducking:
            self.vy = JUMP_FORCE
            self.is_jumping = True
            play_sound("jump")

    def duck(self, is_down):
        if not self.is_jumping:
            self.is_ducking = is_down
            if self.is_ducking:
                self.height = self.ducking_height
            else:
                self.height = self.standing_height

    def update(self, particles):
        # Physics
        if self.is_jumping:
            self.vy += GRAVITY
            self.y += self.vy

            # Land on ground
            if self.y >= GROUND_Y:
                self.y = GROUND_Y
                self.vy = 0
                self.is_jumping = False
                # Landing dust particles
                for _ in range(6):
                    particles.append(Particle(self.x + self.width // 2, GROUND_Y, (200, 200, 210),
                                              vx=random.uniform(-3, 3), vy=random.uniform(-1.5, -0.2), radius=3))
        else:
            self.anim_frame += 0.25
            # Running dust trail
            if random.random() < 0.35 and not self.is_ducking:
                particles.append(Particle(self.x + 6, GROUND_Y - 2, (160, 165, 185),
                                          vx=random.uniform(-2.5, -1.0), vy=random.uniform(-1.0, 0), radius=3))

    def get_hitbox(self):
        top_y = self.y - self.height
        return pygame.Rect(self.x + 4, top_y + 4, self.width - 8, self.height - 4)

    def draw(self, surface):
        top_y = self.y - self.height

        # Shadow on ground
        shadow_w = self.width + (10 if self.is_ducking else 4)
        if not self.is_jumping:
            shadow_rect = pygame.Rect(self.x - 2, GROUND_Y - 3, shadow_w, 6)
            pygame.draw.ellipse(surface, (30, 35, 50), shadow_rect)
        else:
            dist = max(10, GROUND_Y - self.y)
            sw = max(12, int(shadow_w * (1 - dist / 300)))
            shadow_rect = pygame.Rect(self.x + (self.width - sw) // 2, GROUND_Y - 2, sw, 5)
            pygame.draw.ellipse(surface, (35, 40, 55), shadow_rect)

        if self.is_ducking:
            # Ducking / Sliding posture
            slide_rect = pygame.Rect(self.x, top_y + 6, self.width + 12, self.height - 6)
            pygame.draw.rect(surface, COLOR_PLAYER, slide_rect, border_radius=8)
            # Head
            head_rect = pygame.Rect(self.x + self.width - 4, top_y + 2, 16, 16)
            pygame.draw.rect(surface, COLOR_PLAYER_HEAD, head_rect, border_radius=4)
            # Bandana / Visor
            pygame.draw.line(surface, COLOR_PLAYER_BAND, (head_rect.left, head_rect.top + 4),
                             (head_rect.right, head_rect.top + 4), 3)
            # Eye
            pygame.draw.circle(surface, (20, 20, 20), (head_rect.right - 5, head_rect.top + 8), 2)
        else:
            # Body
            body_rect = pygame.Rect(self.x + 4, top_y + 18, self.width - 8, self.height - 28)
            pygame.draw.rect(surface, COLOR_PLAYER, body_rect, border_radius=6)

            # Head
            head_x = self.x + 6
            head_y = top_y + 2
            pygame.draw.rect(surface, COLOR_PLAYER_HEAD, (head_x, head_y, 22, 18), border_radius=4)

            # Headband
            pygame.draw.line(surface, COLOR_PLAYER_BAND, (head_x, head_y + 5), (head_x + 22, head_y + 5), 3)
            # Headband tails blowing behind
            band_tail = 6 + int(math.sin(self.anim_frame * 1.5) * 4)
            pygame.draw.line(surface, COLOR_PLAYER_BAND, (head_x, head_y + 5), (head_x - band_tail, head_y + 7), 2)

            # Eye
            pygame.draw.circle(surface, (20, 20, 20), (head_x + 16, head_y + 9), 2)

            # Running legs animation
            leg_cycle = math.sin(self.anim_frame)
            leg1_y = top_y + self.height - 10 + int(leg_cycle * 6)
            leg2_y = top_y + self.height - 10 - int(leg_cycle * 6)

            if self.is_jumping:
                # Tucked legs while jumping
                pygame.draw.rect(surface, (50, 50, 60), (self.x + 8, top_y + self.height - 8, 8, 6), border_radius=2)
                pygame.draw.rect(surface, (50, 50, 60), (self.x + 20, top_y + self.height - 12, 8, 8), border_radius=2)
            else:
                # Leg 1
                pygame.draw.line(surface, (50, 50, 60), (self.x + 12, top_y + self.height - 10), (self.x + 10, leg1_y), 4)
                # Leg 2
                pygame.draw.line(surface, (30, 30, 40), (self.x + 22, top_y + self.height - 10), (self.x + 24, leg2_y), 4)


class Obstacle:
    def __init__(self, x, speed, kind="low"):
        self.x = x
        self.kind = kind  # 'low' (jump over) or 'high' (duck under)
        self.speed = speed
        self.passed = False

        if self.kind == "low":
            self.width = random.choice([26, 38, 48])
            self.height = random.randint(38, 52)
            self.y = GROUND_Y - self.height
        else:  # High / flying obstacle
            self.width = 44
            self.height = 24
            # Overhead height requiring ducking
            self.y = GROUND_Y - 75
            self.wing_anim = 0

    def update(self, speed):
        self.x -= speed
        if self.kind == "high":
            self.wing_anim += 0.2

    def get_hitbox(self):
        return pygame.Rect(self.x + 2, self.y + 2, self.width - 4, self.height - 4)

    def draw(self, surface):
        if self.kind == "low":
            # Spikes / Cactus styling
            rect = pygame.Rect(self.x, self.y, self.width, self.height)
            # Main shape
            pygame.draw.rect(surface, COLOR_OBSTACLE_LOW, rect, border_top_left_radius=6, border_top_right_radius=6)
            # Darker stripe highlight
            pygame.draw.line(surface, (30, 160, 90), (self.x + 6, self.y + 4), (self.x + 6, self.y + self.height - 2), 2)
            if self.width > 30:
                pygame.draw.line(surface, (30, 160, 90), (self.x + self.width - 8, self.y + 8),
                                 (self.x + self.width - 8, self.y + self.height - 2), 2)
            # Red warning tip
            pygame.draw.rect(surface, (230, 80, 60), (self.x, self.y, self.width, 5),
                             border_top_left_radius=6, border_top_right_radius=6)
        else:
            # Flying Drone / Bat
            body = pygame.Rect(self.x + 8, self.y + 4, self.width - 16, self.height - 8)
            pygame.draw.ellipse(surface, COLOR_OBSTACLE_HIGH, body)
            # Glowing sensor eye
            pygame.draw.circle(surface, (255, 230, 90), (self.x + 12, self.y + self.height // 2), 3)

            # Animated wings
            wing_flap = int(math.sin(self.wing_anim) * 8)
            pygame.draw.polygon(surface, (200, 50, 40), [
                (self.x + self.width // 2, self.y + 6),
                (self.x + self.width - 4, self.y - wing_flap),
                (self.x + 14, self.y + 4)
            ])


class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.anim = random.uniform(0, math.pi)

    def update(self, speed):
        self.x -= speed
        self.anim += 0.1

    def get_hitbox(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def draw(self, surface):
        scale = abs(math.cos(self.anim))
        coin_w = max(3, int(self.radius * scale))
        rect = pygame.Rect(self.x - coin_w, self.y - self.radius, coin_w * 2, self.radius * 2)
        pygame.draw.ellipse(surface, COLOR_COIN, rect)
        pygame.draw.ellipse(surface, (255, 245, 170), rect, width=2)


class Background:
    def __init__(self):
        # Cloud layers
        self.clouds = [[random.randint(0, WIDTH), random.randint(40, 140), random.randint(45, 80), random.uniform(0.6, 1.2)]
                       for _ in range(5)]
        # Distant hills
        self.hill_offset = 0

    def update(self, game_speed):
        for c in self.clouds:
            c[0] -= c[3]
            if c[0] < -100:
                c[0] = WIDTH + random.randint(20, 80)
                c[1] = random.randint(40, 140)
        self.hill_offset = (self.hill_offset + game_speed * 0.18) % 300

    def draw(self, surface):
        # Sky gradient
        for y in range(GROUND_Y):
            ratio = y / GROUND_Y
            r = int(COLOR_SKY_TOP[0] * (1 - ratio) + COLOR_SKY_BOTTOM[0] * ratio)
            g = int(COLOR_SKY_TOP[1] * (1 - ratio) + COLOR_SKY_BOTTOM[1] * ratio)
            b = int(COLOR_SKY_TOP[2] * (1 - ratio) + COLOR_SKY_BOTTOM[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

        # Clouds
        for c in self.clouds:
            cx, cy, cw, _ = c
            cloud_surf = pygame.Surface((cw * 2, 40), pygame.SRCALPHA)
            pygame.draw.ellipse(cloud_surf, (255, 255, 255, 60), (0, 0, cw, 28))
            pygame.draw.ellipse(cloud_surf, (255, 255, 255, 80), (cw // 3, 4, cw, 30))
            surface.blit(cloud_surf, (cx, cy))

        # Distant Mountains (Parallax Layer)
        mountain_points = []
        for x in range(0, WIDTH + 350, 150):
            screen_x = x - int(self.hill_offset)
            screen_y = GROUND_Y - 45 - int(math.sin(x * 0.02) * 35)
            mountain_points.append((screen_x, screen_y))
        mountain_points.append((WIDTH + 100, GROUND_Y))
        mountain_points.append((-100, GROUND_Y))
        pygame.draw.polygon(surface, (35, 42, 68), mountain_points)

        # Ground base
        pygame.draw.rect(surface, COLOR_GROUND, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        # Ground accent top bar
        pygame.draw.line(surface, COLOR_GROUND_LINE, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)


def load_high_score():
    score_file = os.path.join(os.path.dirname(__file__), "highscore.txt")
    if os.path.exists(score_file):
        try:
            with open(score_file, "r") as f:
                return int(f.read().strip())
        except Exception:
            return 0
    return 0


def save_high_score(high_score):
    score_file = os.path.join(os.path.dirname(__file__), "highscore.txt")
    try:
        with open(score_file, "w") as f:
            f.write(str(int(high_score)))
    except Exception:
        pass


def main():
    player = Player()
    bg = Background()
    obstacles = []
    coins = []
    particles = []

    score = 0.0
    high_score = load_high_score()
    base_speed = 6.0
    spawn_timer = 0
    coin_timer = 0

    state = "START"  # "START", "PLAYING", "GAME_OVER"

    running = True
    while running:
        CLOCK.tick(FPS)
        current_speed = base_speed + (score / 350.0)

        # ---------------- Input Events ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break

                if state == "START":
                    if event.key in (pygame.K_SPACE, pygame.K_UP):
                        state = "PLAYING"
                        player.jump()

                elif state == "PLAYING":
                    if event.key in (pygame.K_SPACE, pygame.K_UP):
                        player.jump()
                    elif event.key == pygame.K_DOWN:
                        player.duck(True)

                elif state == "GAME_OVER":
                    if event.key in (pygame.K_SPACE, pygame.K_r, pygame.K_UP):
                        # Reset
                        player = Player()
                        obstacles.clear()
                        coins.clear()
                        particles.clear()
                        score = 0.0
                        spawn_timer = 0
                        coin_timer = 0
                        state = "PLAYING"
                        player.jump()

            elif event.type == pygame.KEYUP:
                if state == "PLAYING":
                    if event.key == pygame.K_DOWN:
                        player.duck(False)

        # ---------------- State Updates ----------------
        if state == "PLAYING":
            score += 0.15
            bg.update(current_speed)
            player.update(particles)

            # Spawn Obstacles
            spawn_timer += 1
            min_spawn_delay = max(55, int(110 - (current_speed * 2)))
            if spawn_timer > min_spawn_delay:
                if random.random() < 0.035:
                    kind = "high" if random.random() < 0.35 and score > 40 else "low"
                    obstacles.append(Obstacle(WIDTH + 30, current_speed, kind))
                    spawn_timer = 0

            # Spawn Coins
            coin_timer += 1
            if coin_timer > 140:
                if random.random() < 0.04:
                    coin_y = GROUND_Y - 45 if random.random() < 0.5 else GROUND_Y - 95
                    coins.append(Coin(WIDTH + 20, coin_y))
                    coin_timer = 0

            # Update & filter Obstacles
            player_hitbox = player.get_hitbox()
            for obs in obstacles[:]:
                obs.update(current_speed)
                if obs.get_hitbox().colliderect(player_hitbox):
                    play_sound("crash")
                    state = "GAME_OVER"
                    if int(score) > high_score:
                        high_score = int(score)
                        save_high_score(high_score)
                    # Explosion particles
                    for _ in range(25):
                        particles.append(Particle(player.x + 18, player.y - 20, random.choice([
                            COLOR_PLAYER, (255, 200, 50), (255, 255, 255), (100, 100, 110)
                        ]), vx=random.uniform(-5, 5), vy=random.uniform(-6, 2), radius=5, lifetime=35))
                    break

                if obs.x + obs.width < -50:
                    obstacles.remove(obs)

            # Update & collect Coins
            for c in coins[:]:
                c.update(current_speed)
                if c.get_hitbox().colliderect(player_hitbox):
                    play_sound("coin")
                    score += 15
                    # Coin sparkle particles
                    for _ in range(8):
                        particles.append(Particle(c.x, c.y, COLOR_COIN,
                                                  vx=random.uniform(-3, 3), vy=random.uniform(-3, 3), radius=3, lifetime=18))
                    coins.remove(c)
                elif c.x < -30:
                    coins.remove(c)

        # Update particles regardless of state
        for p in particles[:]:
            p.update()
            if p.lifetime <= 0:
                particles.remove(p)

        # ---------------- Drawing ----------------
        bg.draw(SCREEN)

        # Draw Coins
        for c in coins:
            c.draw(SCREEN)

        # Draw Obstacles
        for obs in obstacles:
            obs.draw(SCREEN)

        # Draw Particles
        for p in particles:
            p.draw(SCREEN)

        # Draw Player
        if state != "GAME_OVER":
            player.draw(SCREEN)

        # ---------------- HUD / Overlays ----------------
        # Score HUD
        score_text = FONT_BIG.render(f"SCORE: {int(score):05d}", True, COLOR_TEXT)
        SCREEN.blit(score_text, (25, 20))

        hi_text = FONT_MED.render(f"HI-SCORE: {high_score:05d}", True, (255, 215, 0))
        SCREEN.blit(hi_text, (25, 60))

        speed_text = FONT_SMALL.render(f"SPEED: {current_speed:.1f}x", True, COLOR_GRAY)
        SCREEN.blit(speed_text, (25, 92))

        # Control reminder badge in corner
        controls_hud = FONT_SMALL.render("[SPACE / UP] Jump   [DOWN] Duck", True, (200, 205, 220))
        SCREEN.blit(controls_hud, (WIDTH - controls_hud.get_width() - 25, 25))

        # Start Overlay
        if state == "START":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((15, 20, 35, 180))
            SCREEN.blit(overlay, (0, 0))

            title = FONT_TITLE.render("SPEED RUNNER", True, COLOR_TEXT)
            sub = FONT_MED.render("Version A - Keyboard Edition", True, (130, 200, 255))
            press = FONT_MED.render("Press SPACE or UP ARROW to Start", True, (255, 220, 80))

            c_jump = FONT_SMALL.render("• SPACE or UP ARROW : Jump over low obstacles", True, COLOR_WHITE)
            c_duck = FONT_SMALL.render("• DOWN ARROW : Duck under flying drones", True, COLOR_WHITE)
            c_coins = FONT_SMALL.render("• Collect GOLD COINS for +15 bonus points!", True, (255, 215, 0))

            cx = WIDTH // 2
            SCREEN.blit(title, (cx - title.get_width() // 2, 85))
            SCREEN.blit(sub, (cx - sub.get_width() // 2, 140))
            SCREEN.blit(press, (cx - press.get_width() // 2, 195))

            box_rect = pygame.Rect(cx - 210, 245, 420, 110)
            pygame.draw.rect(SCREEN, (35, 40, 60), box_rect, border_radius=8)
            pygame.draw.rect(SCREEN, (70, 80, 120), box_rect, width=2, border_radius=8)

            SCREEN.blit(c_jump, (cx - 190, 258))
            SCREEN.blit(c_duck, (cx - 190, 288))
            SCREEN.blit(c_coins, (cx - 190, 318))

        # Game Over Overlay
        elif state == "GAME_OVER":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((25, 10, 15, 190))
            SCREEN.blit(overlay, (0, 0))

            over_title = FONT_TITLE.render("GAME OVER", True, (255, 80, 80))
            final_score = FONT_BIG.render(f"Final Score: {int(score)}", True, COLOR_TEXT)
            high_label = FONT_MED.render(f"Best Score: {high_score}", True, (255, 215, 0))
            restart_hint = FONT_MED.render("Press SPACE or R to Play Again", True, (255, 255, 255))

            cx = WIDTH // 2
            SCREEN.blit(over_title, (cx - over_title.get_width() // 2, 110))
            SCREEN.blit(final_score, (cx - final_score.get_width() // 2, 180))
            SCREEN.blit(high_label, (cx - high_label.get_width() // 2, 225))
            SCREEN.blit(restart_hint, (cx - restart_hint.get_width() // 2, 285))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

