
import os
import sys
import time
import math
import random
import copy
from typing import List, Tuple, Callable

# --- Configuration ---
WIDTH = 60
HEIGHT = 30
POPULATION_SIZE = 20
MUTATION_RATE = 0.1
MUTATION_STRENGTH = 0.5
ELITISM_COUNT = 2
MAX_GENERATIONS = 100
FPS = 60

# --- Colors ---
class Color:
    RESET = "\033[0m"
    WALL = "\033[48;5;235m"
    AGENT = "\033[38;5;46m"  # Green text
    AGENT_DEAD = "\033[38;5;196m" # Red text
    RAY = "\033[38;5;240m"   # Grey rays

# --- Math Library (No Numpy) ---
class Matrix:
    def __init__(self, rows, cols, data=None):
        self.rows = rows
        self.cols = cols
        if data:
            self.data = data
        else:
            self.data = [[0.0 for _ in range(cols)] for _ in range(rows)]

    @staticmethod
    def random(rows, cols):
        data = [[random.uniform(-1, 1) for _ in range(cols)] for _ in range(rows)]
        return Matrix(rows, cols, data)

    def to_list(self):
        return [item for row in self.data for item in row]

    def add(self, n):
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                val = n.data[i][j] if isinstance(n, Matrix) else n
                result.data[i][j] = self.data[i][j] + val
        return result

    def multiply(self, n):
        # Element-wise or Scalar
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                val = n.data[i][j] if isinstance(n, Matrix) else n
                result.data[i][j] = self.data[i][j] * val
        return result

    @staticmethod
    def dot(m1, m2):
        if m1.cols != m2.rows:
            raise ValueError("Matrix dimensions mismatch for dot product")
        result = Matrix(m1.rows, m2.cols)
        for i in range(result.rows):
            for j in range(result.cols):
                sum_val = 0
                for k in range(m1.cols):
                    sum_val += m1.data[i][k] * m2.data[k][j]
                result.data[i][j] = sum_val
        return result

    def map(self, func):
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[i][j] = func(self.data[i][j])
        return result

# --- Neural Network ---
def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def tanh(x):
    return math.tanh(x)

class NeuralNetwork:
    def __init__(self, input_nodes, hidden_nodes, output_nodes):
        self.input_nodes = input_nodes
        self.hidden_nodes = hidden_nodes
        self.output_nodes = output_nodes

        self.weights_ih = Matrix.random(hidden_nodes, input_nodes)
        self.weights_ho = Matrix.random(output_nodes, hidden_nodes)
        
        self.bias_h = Matrix.random(hidden_nodes, 1)
        self.bias_o = Matrix.random(output_nodes, 1)

    def predict(self, input_array):
        # Input -> Hidden
        inputs = Matrix(len(input_array), 1, [[x] for x in input_array])
        hidden = Matrix.dot(self.weights_ih, inputs)
        hidden = hidden.add(self.bias_h)
        hidden = hidden.map(tanh)

        # Hidden -> Output
        output = Matrix.dot(self.weights_ho, hidden)
        output = output.add(self.bias_o)
        output = output.map(tanh) # Output range [-1, 1] for steering/speed

        return output.to_list()

    def copy(self):
        new_net = NeuralNetwork(self.input_nodes, self.hidden_nodes, self.output_nodes)
        new_net.weights_ih = copy.deepcopy(self.weights_ih)
        new_net.weights_ho = copy.deepcopy(self.weights_ho)
        new_net.bias_h = copy.deepcopy(self.bias_h)
        new_net.bias_o = copy.deepcopy(self.bias_o)
        return new_net

    def mutate(self):
        def mutate_val(val):
            if random.random() < MUTATION_RATE:
                return val + random.gauss(0, MUTATION_STRENGTH)
            return val

        self.weights_ih = self.weights_ih.map(mutate_val)
        self.weights_ho = self.weights_ho.map(mutate_val)
        self.bias_h = self.bias_h.map(mutate_val)
        self.bias_o = self.bias_o.map(mutate_val)

# --- Physics & Agent ---
class Ray:
    def __init__(self, angle_offset, length=15):
        self.angle_offset = angle_offset
        self.length = length
        self.reading = 0.0 # 0.0 (far) to 1.0 (touching)

class Agent:
    def __init__(self, brain=None):
        self.x = 5.0
        self.y = HEIGHT / 2
        self.angle = 0.0 # Radians
        self.vel_linear = 0.0
        self.vel_angular = 0.0
        self.radius = 0.8
        self.alive = True
        self.fitness = 0.0
        self.distance_traveled = 0.0
        
        # Sensors: 5 rays spreading front
        self.rays = [
            Ray(-math.pi/3), Ray(-math.pi/6), Ray(0), Ray(math.pi/6), Ray(math.pi/3)
        ]
        
        if brain:
            self.brain = brain
        else:
            # Inputs: 5 rays + current velocity + bias = 7 inputs
            # Outputs: Linear force, Angular force
            self.brain = NeuralNetwork(len(self.rays) + 1, 8, 2)

    def update(self, dt, track_map):
        if not self.alive: return
        
        # 1. Sense
        inputs = []
        for ray in self.rays:
            ray.reading = self.cast_ray(ray, track_map)
            inputs.append(ray.reading)
        inputs.append(self.vel_linear / 2.0) # Normalize approximate max speed

        # 2. Think
        outputs = self.brain.predict(inputs)
        
        # 3. Act
        linear_force = outputs[0] * 15.0 # Max accel
        angular_force = outputs[1] * 5.0 # Max turn speed
        
        self.vel_linear += linear_force * dt
        self.vel_angular = angular_force # Direct control of turn speed feels better for this simple sim
        
        # Friction
        self.vel_linear *= 0.95
        
        # Move
        self.angle += self.vel_angular * dt
        self.x += math.cos(self.angle) * self.vel_linear * dt
        self.y += math.sin(self.angle) * self.vel_linear * dt
        
        # Fitness Logic
        if self.vel_linear > 0.1:
            self.distance_traveled += self.vel_linear * dt
            self.fitness = self.distance_traveled
            # Bonus for staying alive? No, pure distance is a good localized metric
        
        # 4. Collision
        if self.check_collision(track_map):
            self.alive = False

    def cast_ray(self, ray, track_map):
        ray_angle = self.angle + ray.angle_offset
        dx = math.cos(ray_angle)
        dy = math.sin(ray_angle)
        
        for i in range(1, int(ray.length * 2)): # Step size 0.5
            dist = i * 0.5
            tx = int(self.x + dx * dist)
            ty = int(self.y + dy * dist)
            
            if tx < 0 or tx >= WIDTH or ty < 0 or ty >= HEIGHT or track_map[ty][tx] == 1:
                # Hit wall
                return 1.0 - (dist / ray.length)
        return 0.0

    def check_collision(self, track_map):
        # Circle collision check against integer grid walls
        buffer = 0.5
        check_x = int(self.x)
        check_y = int(self.y)
        
        if check_x < 0 or check_x >= WIDTH or check_y < 0 or check_y >= HEIGHT:
            return True
            
        if track_map[check_y][check_x] == 1:
            return True
            
        return False

# --- Simulation & Visualization ---
class NeuroEvoSim:
    def __init__(self):
        self.generation = 1
        self.agents = [Agent() for _ in range(POPULATION_SIZE)]
        self.track_map = self.generate_track()
        self.best_fitness_history = []
        os.system('') # Enable VT100

    def generate_track(self):
        # Create a simple loop or winding path
        grid = [[1 for _ in range(WIDTH)] for _ in range(HEIGHT)]
        
        # Carve path - parameterized sine wave tunnel
        points = []
        for x in range(0, WIDTH):
            # Main path
            center_y = int(HEIGHT/2 + math.sin(x * 0.15) * (HEIGHT/3 - 2))
            
            # Wideness
            w = 3 + int((math.cos(x * 0.1) + 1)) 
            
            for y in range(center_y - w, center_y + w):
                if 0 < y < HEIGHT - 1:
                    grid[y][x] = 0
                    
        # Force start area clear
        for x in range(0, 10):
            for y in range(int(HEIGHT/2)-3, int(HEIGHT/2)+3):
                grid[y][x] = 0
                
        return grid

    def next_generation(self):
        # Sort by fitness
        self.agents.sort(key=lambda x: x.fitness, reverse=True)
        self.best_fitness_history.append(self.agents[0].fitness)
        print(f"\nGeneration {self.generation} Complete. Best Fitness: {self.agents[0].fitness:.2f}")
        
        new_agents = []
        
        # Elitism
        for i in range(ELITISM_COUNT):
            new_agents.append(Agent(self.agents[i].brain.copy()))
            
        # Selection & Crossover
        while len(new_agents) < POPULATION_SIZE:
            parent = self.select_parent()
            child_brain = parent.brain.copy()
            child_brain.mutate()
            new_agents.append(Agent(child_brain))
            
        self.agents = new_agents
        self.generation += 1
        
        # Reset Agents
        for a in self.agents:
            a.x = 5.0
            a.y = HEIGHT / 2
            a.alive = True
            a.fitness = 0.0
            a.distance_traveled = 0.0
            a.vel_linear = 0.0

    def select_parent(self):
        # Tournament Selection
        tournament = random.sample(self.agents[:10], 3) # Pick from top half
        return max(tournament, key=lambda x: x.fitness)

    def run(self):
        try:
            while self.generation <= MAX_GENERATIONS:
                # Run Generation loop
                frames = 0
                max_frames = 600 # 10 seconds max per gen to prevent stalling
                
                while any(a.alive for a in self.agents) and frames < max_frames:
                    # Update Logic
                    dt = 1.0 / FPS
                    for a in self.agents:
                        a.update(dt, self.track_map)
                    
                    # Render every k frames
                    if frames % 2 == 0:
                        self.render()
                    
                    frames += 1
                    time.sleep(1/FPS)
                
                self.next_generation()
                time.sleep(1) # Pause between gens
                
        except KeyboardInterrupt:
            print("Simulation Stopped.")

    def render(self):
        buffer = []
        buffer.append("\033[H")
        
        # Draw Map & Agents
        # We'll use a string buffer strategy for speed
        output_grid = [[' ' for _ in range(WIDTH)] for _ in range(HEIGHT)]
        
        # Draw Walls
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if self.track_map[y][x] == 1:
                    output_grid[y][x] = f"{Color.WALL} {Color.RESET}"
                else:
                    output_grid[y][x] = " "

        # Draw Agents
        alive_count = 0
        for a in self.agents:
            gx, gy = int(a.x), int(a.y)
            if 0 <= gx < WIDTH and 0 <= gy < HEIGHT:
                char = ">"
                color = Color.AGENT if a.alive else Color.AGENT_DEAD
                if a.alive: alive_count += 1
                
                # Simple direction char
                if -math.pi/4 <= a.angle <= math.pi/4: char = ">"
                elif math.pi/4 < a.angle <= 3*math.pi/4: char = "v"
                elif -3*math.pi/4 <= a.angle < -math.pi/4: char = "^"
                else: char = "<"
                
                output_grid[gy][gx] = f"{color}{char}{Color.RESET}"

        # Combine
        for row in output_grid:
            buffer.append("".join(row))
        
        # Stats Overlay
        stats = f" Gen: {self.generation} | Alive: {alive_count}/{POPULATION_SIZE} | Best: {max((a.fitness for a in self.agents), default=0):.1f} "
        print("\033[H" + stats) # HACK: Print top left
        
        sys.stdout.write("\n".join(buffer))
        sys.stdout.flush()

if __name__ == "__main__":
    # Windows VT100 fix
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Initializing Neuro-Evolution Demo...")
    time.sleep(1)
    
    sim = NeuroEvoSim()
    sim.run()
