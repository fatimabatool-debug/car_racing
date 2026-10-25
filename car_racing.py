"""Car Racing - a top-down traffic racer built with pygame (no asset files needed).

Install:  pip install pygame
Run:      python car_racing.py

Controls: LEFT/RIGHT (A/D) = steer, UP (W) = accelerate, DOWN (S) = brake
          R = restart after a crash, ESC = quit
Goal:     Weave through traffic, collect coins, and travel as far as you can.
"""
import random
import sys

import pygame

WIDTH, HEIGHT, FPS = 640, 720, 60
ROAD_L, ROAD_R, LANES = 120, 520, 4
LANE_W = (ROAD_R - ROAD_L) // LANES
CAR_W, CAR_H = 44, 80
GRASS, ASPHALT, WHITE, YELLOW, RED = (46, 125, 70), (60, 62, 70), (235, 235, 235), (250, 210, 60), (225, 60, 60)
TRAFFIC_COLORS = [(70, 130, 220), (240, 140, 50), (150, 90, 200), (230, 230, 230), (60, 190, 170)]

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car Racing")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 22)
big_font = pygame.font.SysFont("consolas", 54, bold=True)


def lane_center(lane):
    return ROAD_L + lane * LANE_W + LANE_W // 2


def draw_car(rect, color):
    pygame.draw.rect(screen, (25, 25, 30), (rect.x - 4, rect.y + 10, 6, 18), border_radius=2)       # wheels
    pygame.draw.rect(screen, (25, 25, 30), (rect.right - 2, rect.y + 10, 6, 18), border_radius=2)
    pygame.draw.rect(screen, (25, 25, 30), (rect.x - 4, rect.bottom - 28, 6, 18), border_radius=2)
    pygame.draw.rect(screen, (25, 25, 30), (rect.right - 2, rect.bottom - 28, 6, 18), border_radius=2)
    pygame.draw.rect(screen, color, rect, border_radius=10)                                           # body
    pygame.draw.rect(screen, (170, 215, 240), (rect.x + 6, rect.y + 18, rect.w - 12, 16), border_radius=4)  # windshield
    pygame.draw.rect(screen, (170, 215, 240), (rect.x + 8, rect.bottom - 24, rect.w - 16, 10), border_radius=4)


class Traffic:
    def __init__(self, lane):
        self.lane = lane
        self.speed = random.uniform(3.5, 7.0)  # forward speed; slower than the player's top speed
        self.color = random.choice(TRAFFIC_COLORS)
        self.rect = pygame.Rect(0, -CAR_H - 20, CAR_W, CAR_H)
        self.rect.centerx = lane_center(lane)


class Coin:
    def __init__(self, lane):
        self.rect = pygame.Rect(0, -40, 24, 24)
        self.rect.centerx = lane_center(lane)


class Game:
    def __init__(self, high_score=0):
        self.player = pygame.Rect(0, HEIGHT - 150, CAR_W, CAR_H)
        self.player.centerx = lane_center(1)
        self.speed = 5.0
        self.distance = 0.0
        self.coins_collected = 0
        self.traffic, self.coins = [], []
        self.spawn_timer = 0
        self.stripe_offset = 0.0
        self.trees = [[random.choice((50, 580)) + random.randint(-25, 25), random.randint(0, HEIGHT)] for _ in range(9)]
        self.high_score = high_score
        self.over = False

    @property
    def meters(self):
        return int(self.distance / 20)

    @property
    def score(self):
        return self.meters + self.coins_collected * 50

    def spawn(self):
        # Never block more than 2 lanes near the top, so there is always a gap to drive through
        busy = {t.lane for t in self.traffic if t.rect.top < 260}
        free = [lane for lane in range(LANES) if lane not in busy]
        if len(busy) >= 2 or not free:
            return
        if random.random() < 0.28:
            self.coins.append(Coin(random.choice(free)))
        else:
            self.traffic.append(Traffic(random.choice(free)))

    def update(self, keys):
        if self.over:
            return
        steer = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed += 0.12
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed -= 0.30
        else:
            self.speed -= 0.03  # gentle engine drag
        self.speed = max(3.0, min(self.speed, 16.0))

        # Steering is a bit sharper at higher speed
        self.player.x += steer * (4 + self.speed * 0.25)
        if not ROAD_L - 4 < self.player.left or not self.player.right < ROAD_R + 4:
            self.crash()  # leaving the road
            return

        self.distance += self.speed
        self.stripe_offset = (self.stripe_offset + self.speed) % 80
        for tree in self.trees:
            tree[1] += self.speed
            if tree[1] > HEIGHT + 40:
                tree[:] = [random.choice((50, 580)) + random.randint(-25, 25), -40]

        # Spawn traffic more frequently as the run goes on
        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            self.spawn()
            self.spawn_timer = max(18, random.randint(40, 80) - self.meters // 80)

        hitbox = self.player.inflate(-8, -12)
        for car in self.traffic:
            car.rect.y += self.speed - car.speed  # relative motion
            if hitbox.colliderect(car.rect.inflate(-8, -12)):
                self.crash()
                return
        for coin in self.coins[:]:
            coin.rect.y += self.speed
            if hitbox.colliderect(coin.rect):
                self.coins.remove(coin)
                self.coins_collected += 1
        self.traffic = [c for c in self.traffic if -400 < c.rect.y < HEIGHT + 120]
        self.coins = [c for c in self.coins if c.rect.y < HEIGHT + 40]

    def crash(self):
        self.over = True
        self.high_score = max(self.high_score, self.score)

    def draw(self):
        screen.fill(GRASS)
        for x, y in self.trees:
            pygame.draw.rect(screen, (90, 60, 35), (x - 3, y + 14, 6, 14))
            pygame.draw.circle(screen, (30, 95, 50), (int(x), int(y)), 20)
        pygame.draw.rect(screen, ASPHALT, (ROAD_L, 0, ROAD_R - ROAD_L, HEIGHT))
        pygame.draw.rect(screen, WHITE, (ROAD_L - 6, 0, 6, HEIGHT))
        pygame.draw.rect(screen, WHITE, (ROAD_R, 0, 6, HEIGHT))
        for lane in range(1, LANES):
            x = ROAD_L + lane * LANE_W
            for y in range(-80, HEIGHT, 80):
                pygame.draw.rect(screen, WHITE, (x - 2, y + self.stripe_offset, 4, 40))
        for coin in self.coins:
            pygame.draw.circle(screen, YELLOW, coin.rect.center, 12)
            pygame.draw.circle(screen, (200, 160, 30), coin.rect.center, 12, 3)
        for car in self.traffic:
            draw_car(car.rect, car.color)
        draw_car(self.player, RED)

        for i, text in enumerate((f"Score: {self.score}", f"Distance: {self.meters} m",
                                  f"Coins: {self.coins_collected}", f"Best: {self.high_score}")):
            screen.blit(font.render(text, True, WHITE), (12, 10 + i * 26))
        speedo = font.render(f"{int(self.speed * 10)} km/h", True, YELLOW)
        screen.blit(speedo, (WIDTH - speedo.get_width() - 12, HEIGHT - 36))

        if self.over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))
            for text, fnt, color, dy in (("CRASH!", big_font, RED, -30), (f"Score: {self.score}", font, WHITE, 25),
                                         ("Press R to restart", font, WHITE, 60)):
                surf = fnt.render(text, True, color)
                screen.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + dy)))


def main():
    game = Game()
    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game.over:
                game = Game(game.high_score)
        game.update(pygame.key.get_pressed())
        game.draw()
        pygame.display.flip()


if __name__ == "__main__":
    main()
