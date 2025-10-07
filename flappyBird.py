import pygame, random, time
from pygame.locals import *

# VARIABLES
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
SPEED = 8
GRAVITY = 0.5
GAME_SPEED = 5

GROUND_WIDTH = 2 * SCREEN_WIDTH
GROUND_HEIGHT = 100

PIPE_WIDTH = 80
PIPE_HEIGHT = 500

PIPE_GAP = 150
HORIZONTAL_GAP = 300  # Global definition for initial spacing

wing = 'assets/audio/wing.wav'
hit = 'assets/audio/hit.wav'

pygame.mixer.init()


class Bird(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.images = [pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha(),
                       pygame.image.load('assets/sprites/bluebird-midflap.png').convert_alpha(),
                       pygame.image.load('assets/sprites/bluebird-downflap.png').convert_alpha()]

        self.speed = SPEED

        self.current_image = 0
        self.image = pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = SCREEN_WIDTH / 6
        self.rect[1] = SCREEN_HEIGHT / 2

        # Animation control variables
        self.animation_counter = 0
        self.animation_speed = 3

    def update(self):
        self.speed += GRAVITY

        # Only update the image index every 'animation_speed' frames
        self.animation_counter = (self.animation_counter + 1)
        if self.animation_counter >= self.animation_speed:
            self.animation_counter = 0
            self.current_image = (self.current_image + 1) % 3
            self.image = self.images[self.current_image]

        # UPDATE HEIGHT
        self.rect[1] += self.speed

    def bump(self):
        self.speed = -SPEED

    def begin(self):
        self.animation_counter = (self.animation_counter + 1)
        if self.animation_counter >= self.animation_speed:
            self.animation_counter = 0
            self.current_image = (self.current_image + 1) % 3
            self.image = self.images[self.current_image]


class Pipe(pygame.sprite.Sprite):

    def __init__(self, inverted, xpos, ysize):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load('assets/sprites/pipe-green.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (PIPE_WIDTH, PIPE_HEIGHT))

        self.rect = self.image.get_rect()
        self.rect[0] = xpos

        if inverted:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect[1] = - (self.rect[3] - ysize)
        else:
            self.rect[1] = SCREEN_HEIGHT - ysize

        self.mask = pygame.mask.from_surface(self.image)
        self.scored = False

    def update(self):
        self.rect[0] -= GAME_SPEED


class Ground(pygame.sprite.Sprite):

    def __init__(self, xpos):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('assets/sprites/base.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (GROUND_WIDTH, GROUND_HEIGHT))

        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        self.rect[1] = SCREEN_HEIGHT - GROUND_HEIGHT

    def update(self):
        self.rect[0] -= GAME_SPEED


def is_off_screen(sprite):
    return sprite.rect[0] < -(sprite.rect[2])


def get_random_pipes(xpos):
    size = random.randint(100, 300)
    pipe = Pipe(False, xpos, size)
    pipe_inverted = Pipe(True, xpos, SCREEN_HEIGHT - size - PIPE_GAP)
    return pipe, pipe_inverted


# Function containing all game logic for a single round
def flappy_game(screen, clock, score_font, BACKGROUND, BEGIN_IMAGE):
    # Initialize the Score variable (MUST be reset for each game)
    score = 0
    game_over = False

    # --- SETUP SPRITES FOR NEW GAME ---
    bird_group = pygame.sprite.Group()
    bird = Bird()
    bird_group.add(bird)

    ground_group = pygame.sprite.Group()
    for i in range(2):
        ground = Ground(GROUND_WIDTH * i)
        ground_group.add(ground)

    pipe_group = pygame.sprite.Group()

    # Initial pipe setup
    pipes_start = get_random_pipes(SCREEN_WIDTH * 1.5)
    pipe_group.add(pipes_start[0])
    pipe_group.add(pipes_start[1])

    pipes_second = get_random_pipes(SCREEN_WIDTH * 1.5 + HORIZONTAL_GAP)
    pipe_group.add(pipes_second[0])
    pipe_group.add(pipes_second[1])

    # --- BEGIN LOOP ---
    begin = True
    while begin:

        clock.tick(60)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return -1  # Exit function if QUIT is pressed

            if event.type == KEYDOWN:
                if event.key == K_SPACE or event.key == K_UP:
                    bird.bump()
                    pygame.mixer.music.load(wing)
                    pygame.mixer.music.play()
                    begin = False

        screen.blit(BACKGROUND, (0, 0))
        screen.blit(BEGIN_IMAGE, (120, 150))

        bird.begin()
        ground_group.update()

        bird_group.draw(screen)
        ground_group.draw(screen)

        pygame.display.update()

    # --- MAIN GAME LOOP ---
    while not game_over:

        clock.tick(60)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return -1  # Exit function if QUIT is pressed
            if event.type == KEYDOWN:
                if event.key == K_SPACE or event.key == K_UP:
                    bird.bump()
                    pygame.mixer.music.load(wing)
                    pygame.mixer.music.play()

        screen.blit(BACKGROUND, (0, 0))

        # Ground movement/replacement logic
        if is_off_screen(ground_group.sprites()[0]):
            ground_group.remove(ground_group.sprites()[0])
            new_ground = Ground(GROUND_WIDTH - 20)
            ground_group.add(new_ground)

        # Pipe movement/replacement logic
        if is_off_screen(pipe_group.sprites()[0]):
            pipe_group.remove(pipe_group.sprites()[0])
            pipe_group.remove(pipe_group.sprites()[0])

            # Use HORIZONTAL_GAP for consistent spacing
            new_pipe_x = pipe_group.sprites()[-1].rect[0] + HORIZONTAL_GAP

            pipes = get_random_pipes(new_pipe_x)
            pipe_group.add(pipes[0])
            pipe_group.add(pipes[1])

        # 1. Update all sprites
        bird_group.update()
        ground_group.update()
        pipe_group.update()

        # 2. Collision Check: If crash occurs, set the flag and break the loop immediately
        if (pygame.sprite.groupcollide(bird_group, ground_group, False, False, pygame.sprite.collide_mask) or
                pygame.sprite.groupcollide(bird_group, pipe_group, False, False, pygame.sprite.collide_mask)):
            pygame.mixer.music.load(hit)
            pygame.mixer.music.play()
            game_over = True
            break  # Exit the while loop immediately on crash

        # 3. Score Keeping Logic
        if pipe_group.sprites():
            bottom_pipe = pipe_group.sprites()[0]

            if bird.rect[0] > bottom_pipe.rect[0] + PIPE_WIDTH and not bottom_pipe.scored:
                score += 1
                bottom_pipe.scored = True

                if len(pipe_group.sprites()) > 1:
                    pipe_group.sprites()[1].scored = True

        # 4. Drawing
        bird_group.draw(screen)
        pipe_group.draw(screen)
        ground_group.draw(screen)

        # --- DRAW SCORE ---
        score_text = score_font.render(str(score), True, (255, 255, 255))
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 50))

        pygame.display.update()

    # --- END OF while not game_over: LOOP ---

    # 5. Final Game Over Return
    if game_over:
        time.sleep(1)  # Delay happens AFTER the loop has fully stopped
        return score

    return -1  # Should only happen if QUIT was pressed during the loop


def main_loop():
    # Initialize all Pygame elements necessary for the main loop
    # We must do this inside the execution block to ensure correct startup order.
    pygame.init()
    pygame.font.init()

    # Asset/Font setup
    score_font = pygame.font.Font("assets/flappy-bird-font/FlappyBirdRegular-9Pq0.ttf", 80)
    prompt_font = pygame.font.Font("assets/flappy-bird-font/FlappyBirdRegular-9Pq0.ttf", 40)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Flappy Bird')
    BACKGROUND = pygame.image.load('assets/sprites/background-day.png').convert()
    BACKGROUND = pygame.transform.scale(BACKGROUND, (SCREEN_WIDTH, SCREEN_HEIGHT))
    BEGIN_IMAGE = pygame.image.load('assets/sprites/message.png').convert_alpha()
    clock = pygame.time.Clock()

    running = True
    while running:
        # Start a new game by calling the function
        final_score = flappy_game(screen, clock, score_font, BACKGROUND, BEGIN_IMAGE)

        # Check if the game was quit via the X button during gameplay
        if final_score < 0:
            running = False
            break

        # Game Over Screen Logic
        game_over_image = pygame.image.load('assets/sprites/gameover.png').convert_alpha()

        waiting_for_restart = True
        while waiting_for_restart:

            # Draw the static game over screen elements
            screen.blit(game_over_image, (SCREEN_WIDTH // 2 - game_over_image.get_width() // 2, SCREEN_HEIGHT // 4))

            # Display the final score
            final_score_text = score_font.render(f"SCORE: {final_score}", True, (255, 255, 255))
            screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2.9))

            # Prompt: Spacebar to Restart
            restart_prompt_text = prompt_font.render(f"Press Spacebar to Restart", True, (0, 0, 0))
            screen.blit(restart_prompt_text, (SCREEN_WIDTH // 2 - restart_prompt_text.get_width() // 2, SCREEN_HEIGHT // 2.1))

            pygame.display.update()

            # Handle events for restart/quit
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                    waiting_for_restart = False
                if event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        waiting_for_restart = False  # Exit inner loop, start new game
                    if event.key == K_ESCAPE:
                        running = False
                        waiting_for_restart = False

    pygame.quit()


if __name__ == '__main__':
    main_loop()