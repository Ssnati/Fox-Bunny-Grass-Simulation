import pygame
import random
import math
import numpy as np
from enum import Enum
from collections import deque
from dataclasses import dataclass

# Configuración inicial
pygame.init()
pygame.font.init()

# Constantes
WIDTH, HEIGHT = 1000, 700
FPS = 60
FONT = pygame.font.SysFont('Arial', 14)
LARGE_FONT = pygame.font.SysFont('Arial', 24)

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 100, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)


# Enums para mejor organización
class Gender(Enum):
    MALE = 1
    FEMALE = 2


class Season(Enum):
    SPRING = 1
    SUMMER = 2
    AUTUMN = 3
    WINTER = 4


@dataclass
class SimulationParams:
    rabbit_speed: float = 1.5
    fox_speed: float = 2.5
    food_respawn_rate: int = 5
    reproduce_distance: int = 20
    rabbit_reproduce_prob: float = 0.08
    fox_reproduce_prob: float = 0.03
    rabbit_starvation_time: int = 400
    fox_starvation_time: int = 500
    max_rabbits: int = 300
    max_foxes: int = 50
    vision_radius: int = 150
    rabbit_litter_size: tuple = (2, 8)
    fox_litter_size: tuple = (1, 4)
    initial_rabbits: int = 50
    initial_foxes: int = 10
    initial_food: int = 100
    day_length: int = 300  # frames
    season_length: int = 1200  # frames


class Food(pygame.sprite.Sprite):
    def __init__(self, x=None, y=None):
        super().__init__()
        self.size = random.randint(3, 8)
        self.nutrition = self.size * 2
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)

        # Variedad de colores para la comida
        food_color = random.choice([
            (0, 200, 0),
            (50, 150, 50),
            (100, 200, 100),
            (150, 200, 150)
        ])
        pygame.draw.circle(self.image, food_color, (self.size // 2, self.size // 2), self.size // 2)

        if x is None or y is None:
            x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.rect = self.image.get_rect(center=(x, y))
        self.age = 0
        self.lifespan = random.randint(500, 1000)

    def update(self):
        self.age += 1
        if self.age > self.lifespan:
            self.kill()


class Animal(pygame.sprite.Sprite):
    def __init__(self, x, y, gender, color_male, color_female, size, speed):
        super().__init__()
        self.gender = gender
        self.age = 0
        self.energy = 100
        self.time_since_food = 0
        self.size = size
        self.speed = speed
        self.direction = [random.uniform(-1, 1), random.uniform(-1, 1)]
        self.change_dir_timer = 0
        self.memory = deque(maxlen=5)  # Memoria de ubicaciones recientes
        self.fear = 0  # Nivel de miedo (afecta comportamiento)

        # Crear imagen con forma más orgánica
        self.image = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        color = color_male if gender == Gender.MALE else color_female
        pygame.draw.ellipse(self.image, color, (0, 0, size * 2, size * 1.5))

        # Ojos
        eye_color = (255, 255, 255)
        pygame.draw.circle(self.image, eye_color, (size // 1.5, size // 2), size // 4)
        pygame.draw.circle(self.image, (0, 0, 0), (size // 1.5, size // 2), size // 8)

        self.rect = self.image.get_rect(center=(x, y))
        self.original_image = self.image.copy()

    def rotate_towards_direction(self):
        if self.direction[0] != 0 or self.direction[1] != 0:
            angle = math.degrees(math.atan2(-self.direction[1], self.direction[0])) - 90
            self.image = pygame.transform.rotate(self.original_image, angle)
            self.rect = self.image.get_rect(center=self.rect.center)

    def move_randomly(self):
        self.change_dir_timer += 1
        if self.change_dir_timer > 30 or random.random() < 0.05:
            # Cambio de dirección más suave
            self.direction[0] += random.uniform(-0.5, 0.5)
            self.direction[1] += random.uniform(-0.5, 0.5)

            # Normalizar dirección
            length = math.sqrt(self.direction[0] ** 2 + self.direction[1] ** 2)
            if length > 0:
                self.direction[0] /= length
                self.direction[1] /= length

            self.change_dir_timer = 0

        # Movimiento con inercia
        self.rect.x += int(self.direction[0] * self.speed * (1 + 0.5 * random.random()))
        self.rect.y += int(self.direction[1] * self.speed * (1 + 0.5 * random.random()))

        # Rebote en bordes con cambio de dirección
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.direction[0] *= -1
        if self.rect.top < 0 or self.rect.bottom > HEIGHT:
            self.direction[1] *= -1

        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        self.rotate_towards_direction()

    def move_towards(self, target):
        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        dist = max(math.sqrt(dx ** 2 + dy ** 2), 1)

        # Suavizar el movimiento
        self.direction[0] = self.direction[0] * 0.7 + (dx / dist) * 0.3
        self.direction[1] = self.direction[1] * 0.7 + (dy / dist) * 0.3

        # Normalizar dirección
        length = math.sqrt(self.direction[0] ** 2 + self.direction[1] ** 2)
        if length > 0:
            self.direction[0] /= length
            self.direction[1] /= length

        self.rect.x += int(self.direction[0] * self.speed)
        self.rect.y += int(self.direction[1] * self.speed)
        self.rotate_towards_direction()

    def avoid(self, targets, safe_distance=50):
        avg_x, avg_y = 0, 0
        count = 0

        for target in targets:
            dist_sq = (self.rect.centerx - target.rect.centerx) ** 2 + (self.rect.centery - target.rect.centery) ** 2
            if dist_sq < safe_distance ** 2:
                avg_x += self.rect.centerx - target.rect.centerx
                avg_y += self.rect.centery - target.rect.centery
                count += 1

        if count > 0:
            avg_x /= count
            avg_y /= count
            length = max(math.sqrt(avg_x ** 2 + avg_y ** 2), 1)
            self.direction[0] = avg_x / length
            self.direction[1] = avg_y / length
            self.rect.x += int(self.direction[0] * self.speed * 1.5)
            self.rect.y += int(self.direction[1] * self.speed * 1.5)
            self.rotate_towards_direction()
            return True
        return False

    def update_energy(self):
        self.energy -= 0.1
        self.time_since_food += 1
        if self.energy <= 0:
            self.kill()
            return False
        return True


class Rabbit(Animal):
    def __init__(self, x=None, y=None, gender=None):
        gender = gender or random.choice(list(Gender))
        x = x or random.randint(0, WIDTH)
        y = y or random.randint(0, HEIGHT)
        color_male = (255, 255, 150)  # Amarillo claro para machos
        color_female = (255, 220, 150)  # Crema para hembras
        super().__init__(x, y, gender, color_male, color_female, 8, SimulationParams.rabbit_speed)
        self.maturity_age = 100
        self.reproduction_cooldown = 0
        self.fear = 0

    def update(self, foods, foxes):
        if not self.update_energy():
            return

        self.age += 1
        self.reproduction_cooldown = max(0, self.reproduction_cooldown - 1)
        self.fear = max(0, self.fear - 0.5)

        # Comportamiento basado en el miedo
        if self.fear > 50:
            # Comportamiento de huida
            if not self.avoid(foxes, SimulationParams.vision_radius * 1.5):
                self.move_randomly()
        else:
            # Buscar comida si la energía es baja o hay comida cerca
            closest_food = None
            min_food_dist = float('inf')

            for food in foods:
                dist_sq = (self.rect.centerx - food.rect.centerx) ** 2 + (self.rect.centery - food.rect.centery) ** 2
                if dist_sq < SimulationParams.vision_radius ** 2 and dist_sq < min_food_dist:
                    min_food_dist = dist_sq
                    closest_food = food

            if closest_food and (self.energy < 70 or min_food_dist < SimulationParams.vision_radius ** 2 // 4):
                self.move_towards(closest_food)
            else:
                self.move_randomly()

        # Detección de depredadores cercanos
        for fox in foxes:
            dist_sq = (self.rect.centerx - fox.rect.centerx) ** 2 + (self.rect.centery - fox.rect.centery) ** 2
            if dist_sq < SimulationParams.vision_radius ** 2:
                self.fear = min(100, self.fear + 30 * (1 - dist_sq / SimulationParams.vision_radius ** 2))


class Fox(Animal):
    def __init__(self, x=None, y=None, gender=None):
        gender = gender or random.choice(list(Gender))
        x = x or random.randint(0, WIDTH)
        y = y or random.randint(0, HEIGHT)
        color_male = (200, 50, 50)  # Rojo oscuro para machos
        color_female = (150, 50, 50)  # Rojo más claro para hembras
        super().__init__(x, y, gender, color_male, color_female, 12, SimulationParams.fox_speed)
        self.maturity_age = 200
        self.reproduction_cooldown = 0

    def update(self, rabbits):
        if not self.update_energy():
            return

        self.age += 1
        self.reproduction_cooldown = max(0, self.reproduction_cooldown - 1)

        # Buscar presas
        closest_rabbit = None
        min_rabbit_dist = float('inf')

        for rabbit in rabbits:
            dist_sq = (self.rect.centerx - rabbit.rect.centerx) ** 2 + (self.rect.centery - rabbit.rect.centery) ** 2
            if dist_sq < SimulationParams.vision_radius ** 2 and dist_sq < min_rabbit_dist:
                min_rabbit_dist = dist_sq
                closest_rabbit = rabbit

        if closest_rabbit and (self.energy < 80 or min_rabbit_dist < SimulationParams.vision_radius ** 2 // 4):
            self.move_towards(closest_rabbit)
        else:
            self.move_randomly()


class Simulation:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        self.show_stats = True
        self.day_night_cycle = 0
        self.season = Season.SPRING
        self.season_timer = 0
        self.params = SimulationParams()

        # Grupos de sprites
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.rabbits = pygame.sprite.Group()
        self.foxes = pygame.sprite.Group()
        self.foods = pygame.sprite.Group()

        # Historial para gráficos
        self.rabbit_pop_history = []
        self.fox_pop_history = []
        self.food_pop_history = []

        # Inicializar población
        self.initialize_population()

    def initialize_population(self):
        for _ in range(self.params.initial_rabbits):
            self.add_rabbit()

        for _ in range(self.params.initial_foxes):
            self.add_fox()

        for _ in range(self.params.initial_food):
            self.add_food()

    def add_rabbit(self, x=None, y=None, gender=None):
        rabbit = Rabbit(x, y, gender)
        self.rabbits.add(rabbit)
        self.all_sprites.add(rabbit)
        return rabbit

    def add_fox(self, x=None, y=None, gender=None):
        fox = Fox(x, y, gender)
        self.foxes.add(fox)
        self.all_sprites.add(fox)
        return fox

    def add_food(self, x=None, y=None):
        food = Food(x, y)
        self.foods.add(food)
        self.all_sprites.add(food)
        return food

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_s:
                    self.show_stats = not self.show_stats
                elif event.key == pygame.K_r:
                    self.reset_simulation()
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    self.params.rabbit_speed = min(5, self.params.rabbit_speed + 0.1)
                    self.params.fox_speed = min(6, self.params.fox_speed + 0.1)
                elif event.key == pygame.K_MINUS:
                    self.params.rabbit_speed = max(0.5, self.params.rabbit_speed - 0.1)
                    self.params.fox_speed = max(0.5, self.params.fox_speed - 0.1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Click izquierdo - añadir conejo
                    self.add_rabbit(*event.pos)
                elif event.button == 3:  # Click derecho - añadir zorro
                    self.add_fox(*event.pos)
                elif event.button == 2:  # Click medio - añadir comida
                    self.add_food(*event.pos)

    def reset_simulation(self):
        self.all_sprites.empty()
        self.rabbits.empty()
        self.foxes.empty()
        self.foods.empty()
        self.rabbit_pop_history = []
        self.fox_pop_history = []
        self.food_pop_history = []
        self.day_night_cycle = 0
        self.season = Season.SPRING
        self.season_timer = 0
        self.initialize_population()

    def update_season(self):
        self.season_timer += 1
        if self.season_timer > self.params.season_length:
            self.season_timer = 0
            seasons = list(Season)
            current_idx = seasons.index(self.season)
            self.season = seasons[(current_idx + 1) % len(seasons)]

            # Ajustar parámetros según la estación
            if self.season == Season.SPRING:
                self.params.rabbit_reproduce_prob = 0.1
                self.params.food_respawn_rate = 5
            elif self.season == Season.SUMMER:
                self.params.rabbit_reproduce_prob = 0.08
                self.params.food_respawn_rate = 8
            elif self.season == Season.AUTUMN:
                self.params.rabbit_reproduce_prob = 0.05
                self.params.food_respawn_rate = 3
            elif self.season == Season.WINTER:
                self.params.rabbit_reproduce_prob = 0.02
                self.params.food_respawn_rate = 1

    def update_day_night_cycle(self):
        self.day_night_cycle = (self.day_night_cycle + 0.5) % 360
        night_light = max(0.3, math.sin(math.radians(self.day_night_cycle)) * 0.7 + 0.3)

    def handle_reproduction(self):
        # Reproducción de conejos
        reproduced_pairs = set()
        rabbits_list = list(self.rabbits)

        for i, rabbit1 in enumerate(rabbits_list):
            if (rabbit1.age < rabbit1.maturity_age or rabbit1.reproduction_cooldown > 0 or
                    rabbit1.energy < 60 or len(self.rabbits) >= self.params.max_rabbits):
                continue

            for j, rabbit2 in enumerate(rabbits_list[i + 1:], i + 1):
                if (rabbit2.age < rabbit2.maturity_age or rabbit2.reproduction_cooldown > 0 or
                        rabbit2.energy < 60 or rabbit1.gender == rabbit2.gender):
                    continue

                pair = frozenset({id(rabbit1), id(rabbit2)})
                if pair in reproduced_pairs:
                    continue

                dist_sq = (rabbit1.rect.centerx - rabbit2.rect.centerx) ** 2 + (
                            rabbit1.rect.centery - rabbit2.rect.centery) ** 2
                if dist_sq < self.params.reproduce_distance ** 2:
                    if random.random() < self.params.rabbit_reproduce_prob:
                        litter_size = random.randint(*self.params.rabbit_litter_size)
                        for _ in range(litter_size):
                            if len(self.rabbits) < self.params.max_rabbits:
                                x = (rabbit1.rect.centerx + rabbit2.rect.centerx) // 2 + random.randint(-10, 10)
                                y = (rabbit1.rect.centery + rabbit2.rect.centery) // 2 + random.randint(-10, 10)
                                gender = random.choice(list(Gender))
                                self.add_rabbit(x, y, gender)

                        rabbit1.reproduction_cooldown = 100
                        rabbit2.reproduction_cooldown = 100
                        rabbit1.energy -= 20
                        rabbit2.energy -= 20
                        reproduced_pairs.add(pair)
                        break

        # Reproducción de zorros
        reproduced_pairs = set()
        foxes_list = list(self.foxes)

        for i, fox1 in enumerate(foxes_list):
            if (fox1.age < fox1.maturity_age or fox1.reproduction_cooldown > 0 or
                    fox1.energy < 70 or len(self.foxes) >= self.params.max_foxes):
                continue

            for j, fox2 in enumerate(foxes_list[i + 1:], i + 1):
                if (fox2.age < fox2.maturity_age or fox2.reproduction_cooldown > 0 or
                        fox2.energy < 70 or fox1.gender == fox2.gender):
                    continue

                pair = frozenset({id(fox1), id(fox2)})
                if pair in reproduced_pairs:
                    continue

                dist_sq = (fox1.rect.centerx - fox2.rect.centerx) ** 2 + (fox1.rect.centery - fox2.rect.centery) ** 2
                if dist_sq < self.params.reproduce_distance ** 2:
                    if random.random() < self.params.fox_reproduce_prob:
                        litter_size = random.randint(*self.params.fox_litter_size)
                        for _ in range(litter_size):
                            if len(self.foxes) < self.params.max_foxes:
                                x = (fox1.rect.centerx + fox2.rect.centerx) // 2 + random.randint(-10, 10)
                                y = (fox1.rect.centery + fox2.rect.centery) // 2 + random.randint(-10, 10)
                                gender = random.choice(list(Gender))
                                self.add_fox(x, y, gender)

                        fox1.reproduction_cooldown = 200
                        fox2.reproduction_cooldown = 200
                        fox1.energy -= 30
                        fox2.energy -= 30
                        reproduced_pairs.add(pair)
                        break

    def handle_feeding(self):
        # Zorros comen conejos
        for fox in self.foxes:
            for rabbit in pygame.sprite.spritecollide(fox, self.rabbits, dokill=False):
                if rabbit.rect.colliderect(fox.rect.inflate(-5, -5)):
                    rabbit.kill()
                    fox.energy = min(100, fox.energy + 30)
                    fox.time_since_food = 0

        # Conejos comen comida
        for rabbit in self.rabbits:
            for food in pygame.sprite.spritecollide(rabbit, self.foods, dokill=False):
                if food.rect.colliderect(rabbit.rect.inflate(-5, -5)):
                    rabbit.energy = min(100, rabbit.energy + food.nutrition)
                    rabbit.time_since_food = 0
                    food.kill()

    def spawn_food(self):
        if random.random() < self.params.food_respawn_rate / 100:
            # Añadir comida en grupos durante la primavera/verano
            if self.season in (Season.SPRING, Season.SUMMER) and random.random() < 0.3:
                cluster_size = random.randint(3, 10)
                center_x, center_y = random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50)
                for _ in range(cluster_size):
                    x = center_x + random.randint(-40, 40)
                    y = center_y + random.randint(-40, 40)
                    if 0 <= x <= WIDTH and 0 <= y <= HEIGHT:
                        self.add_food(x, y)
            else:
                self.add_food()

    def update_stats(self):
        self.rabbit_pop_history.append(len(self.rabbits))
        self.fox_pop_history.append(len(self.foxes))
        self.food_pop_history.append(len(self.foods))

        # Mantener un tamaño razonable para el historial
        if len(self.rabbit_pop_history) > 500:
            self.rabbit_pop_history.pop(0)
            self.fox_pop_history.pop(0)
            self.food_pop_history.pop(0)

    def draw_stats(self):
        # Fondo semitransparente para los textos
        s = pygame.Surface((300, 150), pygame.SRCALPHA)
        s.fill((0, 0, 0, 128))
        self.screen.blit(s, (10, 10))

        # Textos informativos
        texts = [
            f"Cones: {len(self.rabbits)}",
            f"Zorros: {len(self.foxes)}",
            f"Comida: {len(self.foods)}",
            f"Estación: {self.season.name}",
            f"Día/Noche: {'Día' if math.sin(math.radians(self.day_night_cycle)) > 0 else 'Noche'}",
            f"Velocidad: {self.params.rabbit_speed:.1f}/{self.params.fox_speed:.1f}",
            "[ESPACIO] Pausa  [S] Estadísticas",
            "[R] Reiniciar  [+/-] Velocidad",
            "Click: Añadir conejo/zorro/comida"
        ]

        for i, text in enumerate(texts):
            text_surface = FONT.render(text, True, WHITE)
            self.screen.blit(text_surface, (20, 20 + i * 20))

        # Gráfico de población
        if len(self.rabbit_pop_history) > 10:
            graph_width, graph_height = 280, 100
            graph_x, graph_y = WIDTH - graph_width - 20, 20

            # Fondo del gráfico
            s = pygame.Surface((graph_width, graph_height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 128))
            self.screen.blit(s, (graph_x, graph_y))

            # Escalar datos para que quepan en el gráfico
            max_pop = max(max(self.rabbit_pop_history), max(self.fox_pop_history), max(self.food_pop_history), 1)

            # Dibujar líneas de referencia
            for i in range(0, max_pop + 1, max(1, max_pop // 5)):
                y_pos = graph_y + graph_height - (i / max_pop) * graph_height
                pygame.draw.line(self.screen, (100, 100, 100, 150),
                                 (graph_x, y_pos), (graph_x + graph_width, y_pos), 1)
                text = FONT.render(str(i), True, WHITE)
                self.screen.blit(text, (graph_x - 25, y_pos - 8))

            # Dibujar las series
            points_r = []
            points_f = []
            points_food = []

            for i in range(len(self.rabbit_pop_history)):
                x = graph_x + (i / len(self.rabbit_pop_history)) * graph_width
                y_r = graph_y + graph_height - (self.rabbit_pop_history[i] / max_pop) * graph_height
                y_f = graph_y + graph_height - (self.fox_pop_history[i] / max_pop) * graph_height
                y_food = graph_y + graph_height - (self.food_pop_history[i] / max_pop) * graph_height

                points_r.append((x, y_r))
                points_f.append((x, y_f))
                points_food.append((x, y_food))

            if len(points_r) > 1:
                pygame.draw.lines(self.screen, YELLOW, False, points_r, 2)
                pygame.draw.lines(self.screen, RED, False, points_f, 2)
                pygame.draw.lines(self.screen, GREEN, False, points_food, 2)

            # Leyenda
            pygame.draw.rect(self.screen, YELLOW, (graph_x + 10, graph_y + 10, 10, 10))
            pygame.draw.rect(self.screen, RED, (graph_x + 10, graph_y + 30, 10, 10))
            pygame.draw.rect(self.screen, GREEN, (graph_x + 10, graph_y + 50, 10, 10))

            self.screen.blit(FONT.render("Cones", True, WHITE), (graph_x + 25, graph_y + 8))
            self.screen.blit(FONT.render("Zorros", True, WHITE), (graph_x + 25, graph_y + 28))
            self.screen.blit(FONT.render("Comida", True, WHITE), (graph_x + 25, graph_y + 48))

    def draw_environment(self):
        # Fondo con gradiente según la estación
        if self.season == Season.SPRING:
            top_color = (144, 238, 144)  # Verde claro
            bottom_color = (34, 139, 34)  # Verde bosque
        elif self.season == Season.SUMMER:
            top_color = (173, 216, 230)  # Azul claro
            bottom_color = (0, 100, 0)  # Verde oscuro
        elif self.season == Season.AUTUMN:
            top_color = (255, 215, 0)  # Oro
            bottom_color = (139, 69, 19)  # Marrón
        else:  # WINTER
            top_color = (240, 255, 255)  # Azul muy claro
            bottom_color = (211, 211, 211)  # Gris claro

        # Aplicar ciclo día/noche
        night_factor = max(0.3, 1 - abs(math.sin(math.radians(self.day_night_cycle))) * 0.7)
        top_color = tuple(int(c * night_factor) for c in top_color)
        bottom_color = tuple(int(c * night_factor) for c in bottom_color)

        # Dibujar gradiente vertical
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))

    def run(self):
        while self.running:
            self.handle_events()

            if not self.paused:
                self.update_day_night_cycle()
                self.update_season()

                # Actualizar entidades
                for rabbit in self.rabbits:
                    rabbit.update(self.foods, self.foxes)

                for fox in self.foxes:
                    fox.update(self.rabbits)

                self.foods.update()

                # Manejar interacciones
                self.handle_feeding()
                self.handle_reproduction()
                self.spawn_food()
                self.update_stats()

            # Dibujar
            self.draw_environment()
            self.all_sprites.draw(self.screen)

            if self.show_stats:
                self.draw_stats()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    sim = Simulation()
    sim.run()