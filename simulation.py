import math
import random
from collections import deque
from dataclasses import dataclass
from enums import *
from colors import *

import pygame

# Configuración inicial
pygame.init()
pygame.font.init()

# Constantes
WIDTH, HEIGHT = 1200, 800
FPS = 60
FONT = pygame.font.SysFont('Arial', 14)
LARGE_FONT = pygame.font.SysFont('Arial', 24)


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
    def __init__(self, x, y, gender, color_male, color_female, size, speed, params):
        super().__init__()
        self.gender = gender
        self.age = 0
        self.energy = 100
        self.health = 100
        self.sick = False
        self.time_since_food = 0
        self.size = size
        self.base_speed = speed
        self.params = params  # Añadimos params como atributo
        self.direction = [random.uniform(-1, 1), random.uniform(-1, 1)]
        self.change_dir_timer = 0
        self.memory = deque(maxlen=5)
        self.fear = 0
        self.reproduction_cooldown = 0

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

    @property
    def speed(self):
        """Velocidad afectada por la salud"""
        if self.health <= 30:
            return self.base_speed * 0.5
        elif self.health <= 50:
            return self.base_speed * 0.7
        elif self.health <= 80:
            return self.base_speed * 0.9
        return self.base_speed

    def rotate_towards_direction(self):
        if self.direction[0] != 0 or self.direction[1] != 0:
            angle = math.degrees(math.atan2(-self.direction[1], self.direction[0])) - 90
            self.image = pygame.transform.rotate(self.original_image, angle)
            self.rect = self.image.get_rect(center=self.rect.center)

    def update_health(self):
        """Actualiza el estado de salud del animal"""
        # Si está enfermo, pierde salud
        if self.sick:
            self.health -= 10
            # 50% de probabilidad de curarse
            if random.random() < 0.5:
                self.svick = False

        # Si no se alimentó, pierde salud
        if self.time_since_food >= SimulationParams.day_length:
            self.health -= 20
        # Si se alimentó, gana salud
        elif self.time_since_food == 0:
            self.health = min(100, self.health + 5)

        # Si la salud llega a cero, muere
        if self.health <= 0:
            self.kill()
            return False
        return True

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
        """Actualiza la energía considerando la salud"""
        # Animales enfermos pierden más energía
        energy_loss = 0.1 * (1.5 if self.sick else 1)
        self.energy -= energy_loss
        self.time_since_food += 1
        if self.energy <= 0:
            self.kill()
            return False
        return True

    def check_season_sickness(self, season_changed):
        """Verifica si el animal desarrolla enfermedad al cambiar de estación"""
        if season_changed and random.random() < 0.01:  # 1% de probabilidad
            self.sick = True


class Rabbit(Animal):
    def __init__(self, x=None, y=None, gender=None, params=None):
        gender = gender or random.choice(list(Gender))
        x = x or random.randint(0, WIDTH)
        y = y or random.randint(0, HEIGHT)
        color_male = (255, 255, 150)
        color_female = (255, 220, 150)
        super().__init__(x, y, gender, color_male, color_female, 8, params.rabbit_speed, params)
        self.maturity_age = 100

    def update(self, foods, foxes, all_rabbits):  # Acepta 3 parámetros
        if not self.update_energy() or not self.update_health():
            return

        self.age += 1
        self.reproduction_cooldown = max(0, self.reproduction_cooldown - 1)
        self.fear = max(0, self.fear - 0.5)

        # Comportamiento basado en salud
        if self.health > 70 and self.age >= self.maturity_age and self.reproduction_cooldown == 0:
            self.seek_mate(all_rabbits)
        elif self.health > 30:
            self.seek_food(foods, foxes)
        else:
            if not self.avoid_danger(foxes):
                self.move_randomly()

    def seek_mate(self, rabbits):
        """Busca una pareja para reproducirse"""
        closest_mate = None
        min_dist = float('inf')

        for rabbit in rabbits:
            # Solo considerar conejos del sexo opuesto, maduros y con buena salud
            if (rabbit.gender != self.gender and
                    rabbit.age >= rabbit.maturity_age and
                    rabbit.reproduction_cooldown == 0 and
                    rabbit.health > 50):

                dist_sq = (self.rect.centerx - rabbit.rect.centerx) ** 2 + \
                          (self.rect.centery - rabbit.rect.centery) ** 2

                if dist_sq < self.params.vision_radius ** 2 and dist_sq < min_dist:
                    min_dist = dist_sq
                    closest_mate = rabbit

        if closest_mate:
            self.move_towards(closest_mate)
        else:
            self.move_randomly()

    def seek_food(self, foods, foxes):
        """Busca comida mientras evita peligros"""
        # Primero verificar peligros cercanos
        if self.avoid_danger(foxes):
            return

        # Buscar comida
        closest_food = None
        min_food_dist = float('inf')

        for food in foods:
            dist_sq = (self.rect.centerx - food.rect.centerx) ** 2 + \
                      (self.rect.centery - food.rect.centery) ** 2
            if dist_sq < SimulationParams.vision_radius ** 2 and dist_sq < min_food_dist:
                min_food_dist = dist_sq
                closest_food = food

        if closest_food:
            self.move_towards(closest_food)
        else:
            self.move_randomly()

    def avoid_danger(self, foxes):
        """Evita depredadores y devuelve True si detectó peligro"""
        for fox in foxes:
            dist_sq = (self.rect.centerx - fox.rect.centerx) ** 2 + \
                      (self.rect.centery - fox.rect.centery) ** 2
            if dist_sq < SimulationParams.vision_radius ** 2:
                self.fear = min(100, self.fear + 30 * (1 - dist_sq / SimulationParams.vision_radius ** 2))

        if self.fear > 30:
            return self.avoid(foxes, SimulationParams.vision_radius * 1.5)
        return False


class Fox(Animal):
    def __init__(self, x=None, y=None, gender=None, params=None):
        gender = gender or random.choice(list(Gender))
        x = x or random.randint(0, WIDTH)
        y = y or random.randint(0, HEIGHT)
        color_male = (200, 50, 50)
        color_female = (150, 50, 50)
        super().__init__(x, y, gender, color_male, color_female, 12, params.fox_speed, params)
        self.maturity_age = 200

    def update(self, rabbits, all_foxes):  # Acepta 2 parámetros
        if not self.update_energy() or not self.update_health():
            return

        self.age += 1
        self.reproduction_cooldown = max(0, self.reproduction_cooldown - 1)

        # Comportamiento basado en salud
        if self.health > 70 and self.age >= self.maturity_age and self.reproduction_cooldown == 0:
            self.seek_mate(all_foxes)
        elif self.health > 40:
            self.hunt(rabbits)
        else:
            self.hunt_weak_prey(rabbits)

    def seek_mate(self, foxes):
        """Busca una pareja para reproducirse"""
        closest_mate = None
        min_dist = float('inf')

        for fox in foxes:
            # Solo considerar zorros del sexo opuesto, maduros y con buena salud
            if (fox.gender != self.gender and
                    fox.age >= fox.maturity_age and
                    fox.reproduction_cooldown == 0 and
                    fox.health > 50):

                dist_sq = (self.rect.centerx - fox.rect.centerx) ** 2 + \
                          (self.rect.centery - fox.rect.centery) ** 2

                if dist_sq < self.params.vision_radius ** 2 and dist_sq < min_dist:
                    min_dist = dist_sq
                    closest_mate = fox

        if closest_mate:
            self.move_towards(closest_mate)
        else:
            self.move_randomly()

    def hunt(self, rabbits):
        """Caza al conejo más cercano"""
        closest_rabbit = None
        min_dist = float('inf')

        for rabbit in rabbits:
            dist_sq = (self.rect.centerx - rabbit.rect.centerx) ** 2 + \
                      (self.rect.centery - rabbit.rect.centery) ** 2
            if dist_sq < self.params.vision_radius ** 2 and dist_sq < min_dist:
                min_dist = dist_sq
                closest_rabbit = rabbit

        if closest_rabbit:
            self.move_towards(closest_rabbit)
        else:
            self.move_randomly()

    def hunt_weak_prey(self, rabbits):
        """Busca conejos enfermos o débiles"""
        weakest_rabbit = None
        min_health = float('inf')
        min_dist = float('inf')

        for rabbit in rabbits:
            dist_sq = (self.rect.centerx - rabbit.rect.centerx) ** 2 + \
                      (self.rect.centery - rabbit.rect.centery) ** 2
            if dist_sq < self.params.vision_radius ** 2:
                # Prefiere conejos con menos salud y más cercanos
                health_score = rabbit.health * (dist_sq ** 0.5) / 100
                if health_score < min_health:
                    min_health = health_score
                    weakest_rabbit = rabbit

        if weakest_rabbit:
            self.move_towards(weakest_rabbit)
        else:
            # Si no encuentra presas débiles, cazar normalmente
            self.hunt(rabbits)


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
        self.params = SimulationParams()  # Asegurarse que esto está inicializado

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

    def add_food(self, x=None, y=None):  # Añadir este método si falta
        food = Food(x, y)
        self.foods.add(food)
        self.all_sprites.add(food)
        return food

    def add_rabbit(self, x=None, y=None, gender=None):
        rabbit = Rabbit(x, y, gender, self.params)  # Asegurar que pasamos self.params
        self.rabbits.add(rabbit)
        self.all_sprites.add(rabbit)
        return rabbit

    def add_fox(self, x=None, y=None, gender=None):
        fox = Fox(x, y, gender, self.params)  # Asegurar que pasamos self.params
        self.foxes.add(fox)
        self.all_sprites.add(fox)
        return fox

    def initialize_population(self):
        for _ in range(self.params.initial_rabbits):
            self.add_rabbit()

        for _ in range(self.params.initial_foxes):
            self.add_fox()

        for _ in range(self.params.initial_food):
            self.add_food()  # Usar add_food en lugar de crear Food directamente

    def add_rabbit(self, x=None, y=None, gender=None):
        rabbit = Rabbit(x, y, gender)
        self.rabbits.add(rabbit)
        self.all_sprites.add(rabbit)
        return rabbit

    def add_rabbit(self, x=None, y=None, gender=None):
        rabbit = Rabbit(x, y, gender, self.params)  # Pasamos self.params
        self.rabbits.add(rabbit)
        self.all_sprites.add(rabbit)
        return rabbit

    def add_fox(self, x=None, y=None, gender=None):
        fox = Fox(x, y, gender, self.params)  # Pasamos self.params
        self.foxes.add(fox)
        self.all_sprites.add(fox)
        return fox

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

    def handle_reproduction(self):
        # Ahora los animales ya buscan parejas activamente,
        # solo necesitamos manejar la reproducción cuando están cerca
        for animal in list(self.rabbits) + list(self.foxes):
            if animal.reproduction_cooldown > 0:
                continue

            # Buscar parejas cercanas del mismo tipo (rabbits o foxes)
            group = self.rabbits if isinstance(animal, Rabbit) else self.foxes
            min_dist = float('inf')
            mate = None

            for other in group:
                if (other != animal and
                        other.gender != animal.gender and
                        other.age >= other.maturity_age and
                        other.reproduction_cooldown == 0):

                    dist_sq = (animal.rect.centerx - other.rect.centerx) ** 2 + \
                              (animal.rect.centery - other.rect.centery) ** 2

                    if dist_sq < self.params.reproduce_distance ** 2 and dist_sq < min_dist:
                        min_dist = dist_sq
                        mate = other

            if mate:
                self.attempt_reproduction(animal, mate)

    def attempt_reproduction(self, animal1, animal2):
        """Intenta la reproducción entre dos animales"""
        # Calcular probabilidad basada en salud
        health_factor = (animal1.health + animal2.health) / 200
        base_prob = self.params.rabbit_reproduce_prob if isinstance(animal1, Rabbit) else self.params.fox_reproduce_prob
        prob = base_prob * health_factor

        if random.random() < prob:
            # Reproducción exitosa
            litter_size_range = self.params.rabbit_litter_size if isinstance(animal1,
                                                                             Rabbit) else self.params.fox_litter_size
            litter_size = random.randint(*litter_size_range)

            group = self.rabbits if isinstance(animal1, Rabbit) else self.foxes
            max_pop = self.params.max_rabbits if isinstance(animal1, Rabbit) else self.params.max_foxes

            for _ in range(litter_size):
                if len(group) < max_pop:
                    x = (animal1.rect.centerx + animal2.rect.centerx) // 2 + random.randint(-10, 10)
                    y = (animal1.rect.centery + animal2.rect.centery) // 2 + random.randint(-10, 10)
                    gender = random.choice(list(Gender))

                    if isinstance(animal1, Rabbit):
                        new_animal = self.add_rabbit(x, y, gender)
                    else:
                        new_animal = self.add_fox(x, y, gender)

                    # Heredar enfermedad si alguno de los padres está enfermo
                    if animal1.sick or animal2.sick:
                        new_animal.sick = True
                        new_animal.health = min(animal1.health, animal2.health) * 0.8

            # Configurar cooldown de reproducción
            animal1.reproduction_cooldown = 100 if isinstance(animal1, Rabbit) else 200
            animal2.reproduction_cooldown = 100 if isinstance(animal2, Rabbit) else 200

            # Reducir energía por reproducción
            animal1.energy -= 20
            animal2.energy -= 20

            # Contagio de enfermedades
            if animal1.sick and not animal2.sick:
                animal2.sick = True
            elif animal2.sick and not animal1.sick:
                animal1.sick = True
        # Reproducción de conejos
        reproduced_pairs = set()
        rabbits_list = list(self.rabbits)

        for i, rabbit1 in enumerate(rabbits_list):
            # Nueva condición: salud afecta reproducción
            health_factor = self.get_reproduction_probability(rabbit1.health)
            if (rabbit1.age < rabbit1.maturity_age or rabbit1.reproduction_cooldown > 0 or
                    rabbit1.energy < 60 or len(self.rabbits) >= self.params.max_rabbits or
                    health_factor <= 0):
                continue

            for j, rabbit2 in enumerate(rabbits_list[i + 1:], i + 1):
                health_factor2 = self.get_reproduction_probability(rabbit2.health)
                if (rabbit2.age < rabbit2.maturity_age or rabbit2.reproduction_cooldown > 0 or
                        rabbit2.energy < 60 or rabbit1.gender == rabbit2.gender or
                        health_factor2 <= 0):
                    continue

                pair = frozenset({id(rabbit1), id(rabbit2)})
                if pair in reproduced_pairs:
                    continue

                dist_sq = (rabbit1.rect.centerx - rabbit2.rect.centerx) ** 2 + (
                        rabbit1.rect.centery - rabbit2.rect.centery) ** 2
                if dist_sq < self.params.reproduce_distance ** 2:
                    # Probabilidad de reproducción afectada por salud
                    prob = self.params.rabbit_reproduce_prob * (health_factor + health_factor2) / 2
                    if random.random() < prob:
                        litter_size = random.randint(*self.params.rabbit_litter_size)
                        for _ in range(litter_size):
                            if len(self.rabbits) < self.params.max_rabbits:
                                x = (rabbit1.rect.centerx + rabbit2.rect.centerx) // 2 + random.randint(-10, 10)
                                y = (rabbit1.rect.centery + rabbit2.rect.centery) // 2 + random.randint(-10, 10)
                                gender = random.choice(list(Gender))
                                new_rabbit = self.add_rabbit(x, y, gender)
                                # Los hijos heredan la enfermedad de los padres
                                if rabbit1.sick or rabbit2.sick:
                                    new_rabbit.sick = True
                                    new_rabbit.health = min(rabbit1.health, rabbit2.health)

                        rabbit1.reproduction_cooldown = 100
                        rabbit2.reproduction_cooldown = 100
                        rabbit1.energy -= 20
                        rabbit2.energy -= 20
                        # La pareja se contagia si uno está enfermo
                        if rabbit1.sick and not rabbit2.sick:
                            rabbit2.sick = True
                        elif rabbit2.sick and not rabbit1.sick:
                            rabbit1.sick = True
                        reproduced_pairs.add(pair)
                        break

    def get_reproduction_probability(self, health):
        """Devuelve el factor de probabilidad de reproducción basado en la salud"""
        if health > 80:
            return 1.0  # 100% de probabilidad base
        elif health > 50:
            return 0.7  # 70% de probabilidad base
        elif health > 30:
            return 0.4  # 40% de probabilidad base
        elif health > 0:
            return 0.1  # 10% de probabilidad base
        return 0.0  # No se reproduce

    def update_season(self):
        season_changed = False
        self.season_timer += 1
        if self.season_timer > self.params.season_length:
            self.season_timer = 0
            seasons = list(Season)
            current_idx = seasons.index(self.season)
            self.season = seasons[(current_idx + 1) % len(seasons)]
            season_changed = True

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
        if season_changed:
            for animal in list(self.rabbits) + list(self.foxes):
                animal.check_season_sickness(season_changed)

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
            f"Conejos: {len(self.rabbits)}",
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

            self.screen.blit(FONT.render("Conejos", True, WHITE), (graph_x + 25, graph_y + 8))
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

                # Actualizar conejos con 3 parámetros
                for rabbit in self.rabbits:
                    rabbit.update(self.foods, self.foxes, self.rabbits)

                # Actualizar zorros con 2 parámetros
                for fox in self.foxes:
                    fox.update(self.rabbits, self.foxes)

                self.foods.update()
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
