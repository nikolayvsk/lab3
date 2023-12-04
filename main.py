import random
from itertools import groupby


class Class:
    def __init__(self, subject, teacher, group, time, audience):
        self.Subject = subject
        self.Teacher = teacher
        self.Group = group
        self.Time = time
        self.Audience = audience

class GeneticScheduler:
    def __init__(self, subjects, teachers, groups, classes_per_day, teacher_subjects, audiences, teacher_max_hours, groups_subjects):
        self.subjects = subjects
        self.teachers = teachers
        self.groups = groups
        self.classes_per_day = classes_per_day
        self.teacher_subjects = teacher_subjects
        self.audiences = audiences
        self.teacher_max_hours = teacher_max_hours
        self.groups_subjects = groups_subjects

    # Генерація одного представника популяції (одного розкладу)
    def generate_random_schedule(self): 
        return [Class(
            subject=random.choice(self.subjects),
            teacher=random.choice(self.teachers),
            group=random.choice(self.groups),
            time=random.randint(1, self.classes_per_day),
            audience=random.choice(self.audiences)
        ) for _ in self.subjects]

    # Генерація  популяції (розкладів)
    def generate_random_population(self, population_size):
        return [self.generate_random_schedule() for _ in range(population_size)]

    # Розрахунок оцінки розкладу, те на скільки він підходить
    def calculate_fitness(self, schedule):
        conflicts = sum(
            1 for i, c1 in enumerate(schedule) for c2 in schedule[i + 1:]
            if c1.Time == c2.Time and c1.Group == c2.Group
            or c1.Teacher == c2.Teacher and c1.Time == c2.Time
            or c1.Time == c2.Time and c1.Audience == c2.Audience
        )

        conflicts += sum(1 for c in schedule if c.Subject not in self.teacher_subjects[c.Teacher])
        conflicts += sum(1 for c in schedule if c.Subject not in self.groups_subjects[c.Group])

        teaching_hours = {teacher: sum(c.Time for c in group) for teacher, group in groupby(schedule, key=lambda x: x.Teacher)}
        conflicts += sum(1 for teacher, hours in teaching_hours.items() if teacher in self.teacher_max_hours and hours > self.teacher_max_hours[teacher])

        return 1.0 / (1.0 + conflicts)

    # Мутація гену, тобто розкладу. Рандомно змінюються параметри в розкладі
    def mutate(self, schedule):
        mutation_probability = 0.1
        return [
            Class(
                subject=c.Subject,
                teacher=random.choice(self.teachers) if random.random() < mutation_probability else c.Teacher,
                group=random.choice(self.groups) if random.random() < mutation_probability else c.Group,
                time=random.randint(1, self.classes_per_day) if random.random() < mutation_probability else c.Time,
                audience=random.choice(self.audiences) if random.random() < mutation_probability else c.Audience
            ) for c in schedule
        ]

    # Двоточковий кросовер для отримування двох нащадків
    def crossover(self, schedule1, schedule2):
        crossover_point1 = random.randint(1, len(self.subjects) - 1)
        crossover_point2 = random.randint(crossover_point1 + 1, len(self.subjects))

        child1 = schedule1[:crossover_point1] + schedule2[crossover_point1:crossover_point2] + schedule1[crossover_point2:]
        child2 = schedule2[:crossover_point1] + schedule1[crossover_point1:crossover_point2] + schedule2[crossover_point2:]

        return child1, child2

    # Реалізація генетичного алгоритму. 
    def solve(self, population_size, generations):
        population = self.generate_random_population(population_size)
        best_fitness_score = 0
        best_schedule = None

        crossover_probability = 0.8
        mutation_probability = 0.1
        mutation_decay = 0.995 

        for generation in range(generations):
            fitness_scores = [self.calculate_fitness(schedule) for schedule in population]
            best_index = fitness_scores.index(max(fitness_scores))
            best_fitness_score = fitness_scores[best_index]
            best_schedule = population[best_index]

            print(f"Generation {generation + 1}: Best rating = {best_fitness_score}")
            print()

            elites = sorted(population, key=lambda x: self.calculate_fitness(x), reverse=True)[:int(0.1 * population_size)]

            new_population = []
            while len(new_population) < population_size:
                parent1 = random.choice(population)
                parent2 = random.choice(population)

                if random.random() < crossover_probability:
                    child1, child2 = self.crossover(parent1, parent2)
                    
                    child1 = self.resolve_conflicts(child1)
                    child2 = self.resolve_conflicts(child2)

                    new_population.extend([child1, child2])
                else:
                    new_population.extend([parent1, parent2])

                average_fitness = sum(fitness_scores) / len(population)
                mutation_probability *= mutation_decay ** average_fitness

                if random.random() < mutation_probability:
                    offspring = random.choice(new_population)
                    new_population.append(self.mutate(offspring))

            population = self.fitness_sharing(elites + new_population)

        return best_schedule, best_fitness_score

    # Вирішує конфлікти в розкладі
    def resolve_conflicts(self, schedule):
        for i, c1 in enumerate(schedule):
            for c2 in schedule[i + 1:]:
                if c1.Time == c2.Time and c1.Group == c2.Group:
                    c1.Group, c2.Group = c2.Group, c1.Group
                    
                elif c1.Teacher == c2.Teacher and c1.Time == c2.Time:
                    c1.Time, c2.Time = c2.Time, c1.Time

        return schedule
    
    # Подільний фітнес
    def fitness_sharing(self, population):
        shared_population = []
        for individual in population:
            niche_count = 0
            for other in population:
                niche_count += 1 - self.calculate_distance(individual, other)

            shared_population.append((individual, self.calculate_fitness(individual) / niche_count))
        return [i for i, _ in sorted(shared_population, key=lambda x: x[1], reverse=True)][:len(population)]

    # Оцінка схожості двох розкладів в подільному фітнесі
    def calculate_distance(self, individual1, individual2):
        distance = 0
        for i in range(len(individual1)):
            if individual1[i] != individual2[i]:
                distance += 1
        return distance / len(individual1)


if __name__ == "__main__":
    # Вхідні обмеження, тобто обмеження який викладач що може вести, скільки годин, навантаження на групу і вільні аудиторії
    subjects = ["Математичний аналiз", "Програмування", "Ядерна фiзика", "Алгебра та геометрiя", "Механiка", "Управлiння проектами"]
    teachers = ["Миколенко", "Зiнченко", "Мудрик", "Забарний", "Довбик", "Циганков"]
    groups = ["МАТ-21", "ФIЗ-32", "МАТ-22", "ФIЗ-31", "ПРОГ-41", "ПРОГ-42"]
    teacher_subjects = {
        "Миколенко": ["Математичний аналiз", "Алгебра та геометрiя"],
        "Зiнченко": ["Програмування", "Управлiння проектами"],
        "Мудрик": ["Ядерна фiзика"],
        "Забарний": ["Механiка"],
        "Довбик": ["Програмування"],
        "Циганков": ["Управлiння проектами", "Алгебра та геометрiя"],
    }
    groups_subjects = {
        "МАТ-21": ["Математичний аналiз", "Алгебра та геометрiя"],
        "МАТ-22": ["Математичний аналiз", "Алгебра та геометрiя"],
        "ПРОГ-41": ["Програмування", "Управлiння проектами"],
        "ФIЗ-31": ["Ядерна фiзика"],
        "ФIЗ-32": ["Механiка"],
        "ПРОГ-42": ["Програмування"],
    }
    teacher_max_hours = {
        "Миколенко": 20,
        "Зiнченко": 30,
        "Мудрик": 20,
        "Забарний": 10,
        "Довбик": 30,
        "Циганков": 20,
    }
    audiences = ["01", "02", "03", "04", "05", "06"]
    classes_per_day = 5

    # запуск генетичного алгоритму
    scheduler = GeneticScheduler(subjects, teachers, groups, classes_per_day, teacher_subjects, audiences, teacher_max_hours, groups_subjects)
    best_schedule, fitness = scheduler.solve(500, 50) # розмір популяції, кількість генерації (тобто поколінь)

    print("Best schedule:")
    for lesson in best_schedule:
        print(f"{lesson.Subject} - {lesson.Teacher} - {lesson.Group} - {lesson.Time} - {lesson.Audience}")
    print(f"Rating: {fitness}")