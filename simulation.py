import pygame
import random

# Configuración
WIDTH, HEIGHT = 800, 600
FPS = 30
RABBIT_SPEED = 2
FOX_SPEED = 3
FOOD_RESPAWN_TIME = 10  # frames
REPRODUCE_DISTANCE = 15
REPRODUCE_PROBABILITY_RABBIT = 0.01
REPRODUCE_PROBABILITY_FOX = 0.01
STARVATION_TIME_FOX = 300
STARVATION_TIME_RABBIT = 300  # frames
MAX_RABBITS = 30
MAX_FOXES = 10
VISION_RADIUS = 100  # distancia para detectar comida o presas

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Colores
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)

class Food(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((6, 6))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(center=(random.randint(0, WIDTH), random.randint(0, HEIGHT)))

class Rabbit(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        self.time_since_food = 0
        self.age = 0
        self.direction = (random.uniform(-1, 1), random.uniform(-1, 1))
        self.change_dir_timer = 0

    def move_randomly(self):
        self.change_dir_timer += 1
        if self.change_dir_timer > 60:
            # Cambia dirección aleatoriamente cada 30 frames
            self.direction = (random.uniform(-1, 1), random.uniform(-1, 1))
            self.change_dir_timer = 0

        dx, dy = self.direction
        self.rect.x += int(dx * RABBIT_SPEED)
        self.rect.y += int(dy * RABBIT_SPEED)
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    

    def update(self, foods):
        self.age += 1
        self.time_since_food += 1

        target = None
        min_dist = VISION_RADIUS ** 2
        for food in foods:
            dist = (self.rect.centerx - food.rect.centerx) ** 2 + (self.rect.centery - food.rect.centery) ** 2
            if dist < min_dist:
                min_dist = dist
                target = food

        if target:
            dx = target.rect.centerx - self.rect.centerx
            dy = target.rect.centery - self.rect.centery
            dist = max((dx**2 + dy**2) ** 0.5, 1)
            self.rect.x += int(RABBIT_SPEED * dx / dist)
            self.rect.y += int(RABBIT_SPEED * dy / dist)
        else:
            self.move_randomly()

        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

class Fox(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((12, 12))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=(random.randint(0, WIDTH, ), random.randint(0, HEIGHT)))
        self.time_since_food = 0
        self.age = 0
        self.direction = (random.uniform(-1, 1), random.uniform(-1, 1))
        self.change_dir_timer = 0

    def move_randomly(self):
        self.change_dir_timer += 1
        if self.change_dir_timer > 60:
            self.direction = (random.uniform(-1, 1), random.uniform(-1, 1))
            self.change_dir_timer = 0

        dx, dy = self.direction
        self.rect.x += int(dx * FOX_SPEED)
        self.rect.y += int(dy * FOX_SPEED)
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))


    def update(self, rabbits):
        self.age += 1
        self.time_since_food += 1

        target = None
        min_dist = VISION_RADIUS ** 2
        for rabbit in rabbits:
            dist = (self.rect.centerx - rabbit.rect.centerx) ** 2 + (self.rect.centery - rabbit.rect.centery) ** 2
            if dist < min_dist:
                min_dist = dist
                target = rabbit

        if target:
            dx = target.rect.centerx - self.rect.centerx
            dy = target.rect.centery - self.rect.centery
            dist = max((dx**2 + dy**2) ** 0.5, 1)
            self.rect.x += int(FOX_SPEED * dx / dist)
            self.rect.y += int(FOX_SPEED * dy / dist)
        else:
            self.move_randomly()

        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

# Grupos
all_sprites = pygame.sprite.Group()
rabbits = pygame.sprite.Group()
foxes = pygame.sprite.Group()
foods = pygame.sprite.Group()

reproduced_pairs_rabbits = set()
reproduced_pairs_foxes = set()

# Inicializar
for _ in range(10):
    r = Rabbit()
    rabbits.add(r)
    all_sprites.add(r)

for _ in range(3):
    f = Fox()
    foxes.add(f)
    all_sprites.add(f)

food_timer = 0
running = True

while running:
    clock.tick(FPS)
    food_timer += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Respawn de comida
    if food_timer >= FOOD_RESPAWN_TIME:
        food = Food()
        foods.add(food)
        all_sprites.add(food)
        food_timer = 0

    # Actualizar conejos
    reproduced_pairs_rabbits = set()
    rabbits_to_add = []

    for rabbit in rabbits:
        rabbit.update(foods)

        # Conejos mueren si no comen en STARVATION_TIME
        if rabbit.time_since_food > STARVATION_TIME_RABBIT:
            rabbits.remove(rabbit)
            all_sprites.remove(rabbit)
            continue

        # Reproducción con probabilidad y edad mínima (ej. 20 frames)
        if rabbit.age > 20:
            for other in rabbits:
                if other != rabbit:
                    pair = tuple(sorted([id(rabbit), id(other)]))
                    if (pair not in reproduced_pairs_rabbits and
                        rabbit.rect.colliderect(other.rect.inflate(REPRODUCE_DISTANCE, REPRODUCE_DISTANCE))):
                        if len(rabbits) + len(rabbits_to_add) < MAX_RABBITS and random.random() < REPRODUCE_PROBABILITY_RABBIT:
                            baby = Rabbit()
                            # Posición aleatoria cercana al padre
                            new_x = min(max(rabbit.rect.centerx + random.randint(-10, 10), 0), WIDTH)
                            new_y = min(max(rabbit.rect.centery + random.randint(-10, 10), 0), HEIGHT)
                            baby.rect.center = (new_x, new_y)
                            rabbits_to_add.append(baby)
                            reproduced_pairs_rabbits.add(pair)

    for baby in rabbits_to_add:
        rabbits.add(baby)
        all_sprites.add(baby)

    # Actualizar zorros
    reproduced_pairs_foxes = set()
    foxes_to_add = []

    for fox in foxes:
        fox.update(rabbits)

        # Zorros mueren si no comen en STARVATION_TIME
        if fox.time_since_food > STARVATION_TIME_FOX:
            foxes.remove(fox)
            all_sprites.remove(fox)
            continue

        # Reproducción con probabilidad y edad mínima (ej. 20 frames)
        if fox.age > 20:
            for other in foxes:
                if other != fox:
                    pair = tuple(sorted([id(fox), id(other)]))
                    if (pair not in reproduced_pairs_foxes and
                        fox.rect.colliderect(other.rect.inflate(REPRODUCE_DISTANCE, REPRODUCE_DISTANCE))):
                        if len(foxes) + len(foxes_to_add) < MAX_FOXES and random.random() < REPRODUCE_PROBABILITY_FOX:
                            baby = Fox()
                            new_x = min(max(fox.rect.centerx + random.randint(-10, 10), 0), WIDTH)
                            new_y = min(max(fox.rect.centery + random.randint(-10, 10), 0), HEIGHT)
                            baby.rect.center = (new_x, new_y)
                            foxes_to_add.append(baby)
                            reproduced_pairs_foxes.add(pair)

    for baby in foxes_to_add:
        foxes.add(baby)
        all_sprites.add(baby)

    # Zorros comen conejos
    for fox in foxes:
        hits = pygame.sprite.spritecollide(fox, rabbits, dokill=True)
        if hits:
            fox.time_since_food = 0
            for hit in hits:
                all_sprites.remove(hit)

    # Conejos comen comida
    for rabbit in rabbits:
        hits = pygame.sprite.spritecollide(rabbit, foods, dokill=True)
        if hits:
            rabbit.time_since_food = 0
            for hit in hits:
                all_sprites.remove(hit)

    # Dibujar
    screen.fill(BLACK)
    all_sprites.draw(screen)
    pygame.display.set_caption(f"Rabbits: {len(rabbits)} | Foxes: {len(foxes)} | Food: {len(foods)}")

    pygame.display.flip()

pygame.quit()
