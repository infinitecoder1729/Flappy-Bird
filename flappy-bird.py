import pygame
import random
import sys
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple

# Initialize Pygame
pygame.init()

# Game Constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.4
FLAP_POWER = -9
PIPE_VELOCITY = -4
PIPE_GAP = 120
MIN_PIPE_HEIGHT = 50
MAX_PIPE_HEIGHT = SCREEN_HEIGHT - PIPE_GAP - MIN_PIPE_HEIGHT

# Colors (HSL-inspired palette)
COLOR_BG_DARK = (20, 25, 35)
COLOR_BG_LIGHT = (135, 206, 250)
COLOR_BG_ACCENT = (30, 130, 180)
COLOR_BIRD = (255, 200, 87)
COLOR_BIRD_DARK = (220, 160, 50)
COLOR_PIPE = (60, 200, 80)
COLOR_PIPE_DARK = (40, 150, 60)
COLOR_PIPE_SHINE = (100, 230, 120)
COLOR_GROUND = (139, 69, 19)
COLOR_GROUND_DARK = (101, 50, 15)
COLOR_TEXT = (255, 255, 255)
COLOR_SCORE = (255, 215, 0)
COLOR_SHADOW = (0, 0, 0, 100)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    PAUSED = 4

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    size: float
    lifetime: float
    color: Tuple[int, int, int]
    
    def update(self, dt: float):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.lifetime -= dt
        self.size *= 0.98
    
    def draw(self, surface: pygame.Surface):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / 1.0))
            color = (*self.color, alpha)
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), max(1, int(self.size)))

class Bird:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.velocity = 0
        self.rotation = 0
        self.size = 16
        self.flap_cooldown = 0
        self.particles: List[Particle] = []
        
    def flap(self):
        if self.flap_cooldown <= 0:
            self.velocity = FLAP_POWER
            self.flap_cooldown = 0.1
            # Generate flap particles
            for _ in range(5):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 5)
                self.particles.append(Particle(
                    self.x, self.y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    random.uniform(2, 4),
                    0.5,
                    (255, 200, 87)
                ))
    
    def update(self, dt: float):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.flap_cooldown -= dt
        
        # Update rotation based on velocity
        self.rotation = min(90, max(-30, self.velocity * 3))
        
        # Update particles
        for particle in self.particles[:]:
            particle.update(dt)
            if particle.lifetime <= 0:
                self.particles.remove(particle)
    
    def draw(self, surface: pygame.Surface):
        # Draw bird body (circle)
        pygame.draw.circle(surface, COLOR_BIRD, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(surface, COLOR_BIRD_DARK, (int(self.x), int(self.y)), self.size, 2)
        
        # Draw eye
        eye_offset_x = math.cos(math.radians(self.rotation)) * 6
        eye_offset_y = -4
        eye_x = int(self.x + eye_offset_x)
        eye_y = int(self.y + eye_offset_y)
        pygame.draw.circle(surface, (0, 0, 0), (eye_x, eye_y), 3)
        pygame.draw.circle(surface, (255, 255, 255), (eye_x - 1, eye_y - 1), 1)
        
        # Draw wing
        wing_points = [
            (self.x + 8, self.y - 2),
            (self.x + 18, self.y - 5),
            (self.x + 15, self.y + 5)
        ]
        pygame.draw.polygon(surface, COLOR_BIRD_DARK, wing_points)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(surface)
    
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.size, self.y - self.size, 
                          self.size * 2, self.size * 2)

class Pipe:
    def __init__(self, x: float, gap_y: float):
        self.x = x
        self.gap_y = gap_y
        self.width = 50
        self.passed = False
    
    def update(self, dt: float):
        self.x += PIPE_VELOCITY
    
    def draw(self, surface: pygame.Surface):
        # Draw top pipe
        top_height = self.gap_y
        pygame.draw.rect(surface, COLOR_PIPE, (self.x, 0, self.width, top_height))
        pygame.draw.rect(surface, COLOR_PIPE_DARK, (self.x, 0, self.width, top_height), 2)
        
        # Draw pipe shine effect
        pygame.draw.line(surface, COLOR_PIPE_SHINE, (self.x + 5, 0), 
                        (self.x + 5, top_height), 1)
        
        # Draw bottom pipe
        bottom_y = self.gap_y + PIPE_GAP
        bottom_height = SCREEN_HEIGHT - bottom_y
        pygame.draw.rect(surface, COLOR_PIPE, (self.x, bottom_y, self.width, bottom_height))
        pygame.draw.rect(surface, COLOR_PIPE_DARK, (self.x, bottom_y, self.width, bottom_height), 2)
        
        # Draw pipe shine effect
        pygame.draw.line(surface, COLOR_PIPE_SHINE, (self.x + 5, bottom_y), 
                        (self.x + 5, bottom_y + bottom_height), 1)
    
    def is_off_screen(self) -> bool:
        return self.x + self.width < 0
    
    def collides_with(self, bird: Bird) -> bool:
        bird_rect = bird.get_rect()
        
        # Check collision with top pipe
        if bird_rect.top < self.gap_y and bird_rect.left < self.x + self.width and bird_rect.right > self.x:
            return True
        
        # Check collision with bottom pipe
        if bird_rect.bottom > self.gap_y + PIPE_GAP and bird_rect.left < self.x + self.width and bird_rect.right > self.x:
            return True
        
        return False

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird - First Edition")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 24)
        
        self.state = GameState.MENU
        self.score = 0
        self.high_score = 0
        self.particles: List[Particle] = []
        self.pipe_spawn_timer = 0
        self.pipe_spawn_interval = 2.0
        
        self.reset_game()
    
    def reset_game(self):
        self.bird = Bird(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)
        self.pipes: List[Pipe] = []
        self.score = 0
        self.particle_system: List[Particle] = []
        self.pipe_spawn_timer = self.pipe_spawn_interval
        self.shake_intensity = 0
        self.frame_count = 0
    
    def spawn_pipe(self):
        gap_y = random.randint(MIN_PIPE_HEIGHT, MAX_PIPE_HEIGHT)
        self.pipes.append(Pipe(SCREEN_WIDTH + 50, gap_y))
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                    if self.state == GameState.MENU:
                        self.state = GameState.PLAYING
                        self.reset_game()
                    elif self.state == GameState.PLAYING:
                        self.bird.flap()
                    elif self.state == GameState.GAME_OVER:
                        self.state = GameState.MENU
                
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.MENU or self.state == GameState.GAME_OVER:
                    self.state = GameState.PLAYING
                    self.reset_game()
                elif self.state == GameState.PLAYING:
                    self.bird.flap()
        
        return True
    
    def update(self, dt: float):
        if self.state == GameState.PLAYING:
            # Update bird
            self.bird.update(dt)
            
            # Update pipes
            for pipe in self.pipes:
                pipe.update(dt)
            
            # Remove off-screen pipes
            self.pipes = [p for p in self.pipes if not p.is_off_screen()]
            
            # Spawn new pipes
            self.pipe_spawn_timer -= dt
            if self.pipe_spawn_timer <= 0:
                self.spawn_pipe()
                self.pipe_spawn_timer = self.pipe_spawn_interval
            
            # Check collisions with pipes
            for pipe in self.pipes:
                if pipe.collides_with(self.bird):
                    self.state = GameState.GAME_OVER
                    self.shake_intensity = 0.1
                    self.create_collision_particles(self.bird.x, self.bird.y)
                    if self.score > self.high_score:
                        self.high_score = self.score
            
            # Check collision with ground or ceiling
            if self.bird.y - self.bird.size <= 0 or self.bird.y + self.bird.size >= SCREEN_HEIGHT:
                self.state = GameState.GAME_OVER
                self.shake_intensity = 0.1
                self.create_collision_particles(self.bird.x, self.bird.y)
                if self.score > self.high_score:
                    self.high_score = self.score
            
            # Check if bird passed a pipe
            for pipe in self.pipes:
                if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                    pipe.passed = True
                    self.score += 1
                    self.create_score_particles(SCREEN_WIDTH // 2, 50)
        
        # Update particles
        for particle in self.particles[:]:
            particle.update(dt)
            if particle.lifetime <= 0:
                self.particles.remove(particle)
        
        # Update screen shake
        self.shake_intensity *= 0.95
    
    def create_collision_particles(self, x: float, y: float):
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 8)
            color = (random.randint(200, 255), random.randint(100, 200), random.randint(50, 150))
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                random.uniform(3, 6),
                0.8,
                color
            ))
    
    def create_score_particles(self, x: float, y: float):
        for _ in range(5):
            angle = random.uniform(-math.pi/2, -math.pi/4)
            speed = random.uniform(2, 4)
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                random.uniform(2, 4),
                1.0,
                COLOR_SCORE
            ))
    
    def draw(self):
        # Draw background
        self.screen.fill(COLOR_BG_LIGHT)
        
        # Draw background gradient effect
        for i in range(SCREEN_HEIGHT):
            color_ratio = i / SCREEN_HEIGHT
            r = int(COLOR_BG_LIGHT[0] * (1 - color_ratio) + COLOR_BG_ACCENT[0] * color_ratio)
            g = int(COLOR_BG_LIGHT[1] * (1 - color_ratio) + COLOR_BG_ACCENT[1] * color_ratio)
            b = int(COLOR_BG_LIGHT[2] * (1 - color_ratio) + COLOR_BG_ACCENT[2] * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
        
        # Draw decorative ground
        pygame.draw.rect(self.screen, COLOR_GROUND, (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
        pygame.draw.rect(self.screen, COLOR_GROUND_DARK, (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40), 2)
        
        # Draw grass pattern
        for i in range(0, SCREEN_WIDTH, 20):
            pygame.draw.polygon(self.screen, COLOR_GROUND_DARK, [
                (i, SCREEN_HEIGHT - 40),
                (i + 10, SCREEN_HEIGHT - 35),
                (i + 20, SCREEN_HEIGHT - 40)
            ])
        
        # Draw pipes
        for pipe in self.pipes:
            pipe.draw(self.screen)
        
        # Draw bird
        self.bird.draw(self.screen)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw score
        score_text = self.font_medium.render(str(self.score), True, COLOR_SCORE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 30))
        
        # Draw game state UI
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        elif self.state == GameState.PAUSED:
            self.draw_paused()
        
        # Apply screen shake effect
        if self.shake_intensity > 0:
            shake_x = random.randint(-int(self.shake_intensity * 5), int(self.shake_intensity * 5))
            shake_y = random.randint(-int(self.shake_intensity * 5), int(self.shake_intensity * 5))
            temp_surface = self.screen.copy()
            self.screen.fill(COLOR_BG_LIGHT)
            self.screen.blit(temp_surface, (shake_x, shake_y))
        
        pygame.display.flip()
    
    def draw_menu(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.font_large.render("FLAPPY", True, COLOR_SCORE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))
        
        subtitle = self.font_medium.render("BIRD", True, COLOR_BIRD)
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 150))
        
        # Instructions
        instructions = self.font_small.render("SPACE or CLICK to START", True, COLOR_TEXT)
        self.screen.blit(instructions, (SCREEN_WIDTH // 2 - instructions.get_width() // 2, 300))
        
        controls = self.font_tiny.render("SPACE/UP/W to Flap | ESC to Pause", True, COLOR_TEXT)
        self.screen.blit(controls, (SCREEN_WIDTH // 2 - controls.get_width() // 2, 380))
        
        high_score_text = self.font_small.render(f"Best: {self.high_score}", True, COLOR_SCORE)
        self.screen.blit(high_score_text, (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, 450))
    
    def draw_game_over(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Game Over text
        game_over_text = self.font_large.render("GAME OVER", True, (255, 100, 100))
        self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 100))
        
        # Score display
        score_text = self.font_medium.render(f"Score: {self.score}", True, COLOR_SCORE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 220))
        
        high_score_text = self.font_medium.render(f"Best: {self.high_score}", True, COLOR_TEXT)
        self.screen.blit(high_score_text, (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, 300))
        
        # Restart instruction
        restart_text = self.font_small.render("SPACE or CLICK to Retry", True, COLOR_TEXT)
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 420))
    
    def draw_paused(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Paused text
        paused_text = self.font_large.render("PAUSED", True, COLOR_TEXT)
        self.screen.blit(paused_text, (SCREEN_WIDTH // 2 - paused_text.get_width() // 2, 200))
        
        # Resume instruction
        resume_text = self.font_small.render("ESC to Resume", True, COLOR_TEXT)
        self.screen.blit(resume_text, (SCREEN_WIDTH // 2 - resume_text.get_width() // 2, 350))
    
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            running = self.handle_input()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
