
import os
import sys
import time
import random
import heapq
from enum import Enum
from typing import List, Tuple, Optional, Set

# --- Configuration ---
WIDTH = 41  # Must be odd
HEIGHT = 21 # Must be odd
DELAY = 0.02 # Seconds between animation frames

class Color:
    RESET = "\033[0m"
    WALL = "\033[48;5;235m"   # Dark Grey Background
    PATH = "\033[48;5;238m"   # Lighter Grey Background (Empty)
    GEN_HEAD = "\033[48;5;46m" # Green HEAD
    SOLVE_OPEN = "\033[48;5;51m" # Cyan (Searching)
    SOLVE_CLOSED = "\033[48;5;24m" # Dark Blue (Visited)
    FINAL_PATH = "\033[48;5;220m" # Gold
    START = "\033[48;5;196m"  # Red
    END = "\033[48;5;201m"    # Pink

class CellType(Enum):
    WALL = 0
    PATH = 1

class MazeDemo:
    def __init__(self, width, height):
        self.width = width if width % 2 else width + 1
        self.height = height if height % 2 else height + 1
        self.grid = [[CellType.WALL for _ in range(self.width)] for _ in range(self.height)]
        self.start = (1, 1)
        self.end = (self.width - 2, self.height - 2)
        
        # Enable VT100 emulation on Windows (for colors)
        os.system('') 

    def clear_screen(self):
        print("\033[H", end="") # Move cursor to top-left

    def print_grid(self, overrides=None):
        """
        Efficiently prints the grid.
        overrides: dict of (x, y) -> ColorString to temporarily draw specific cells (like heads/paths)
        """
        buffer = []
        buffer.append("\033[H") # Home cursor
        
        for y in range(self.height):
            row_str = []
            for x in range(self.width):
                color = ""
                # Priority 1: Overrides (Animation states)
                if overrides and (x, y) in overrides:
                    color = overrides[(x, y)]
                # Priority 2: Standard Grid State
                elif (x, y) == self.start:
                    color = Color.START
                elif (x, y) == self.end:
                    color = Color.END
                elif self.grid[y][x] == CellType.WALL:
                    color = Color.WALL
                else:
                    color = Color.PATH
                
                row_str.append(f"{color}  {Color.RESET}") # Double space for square-ish aspect ratio
            buffer.append("".join(row_str))
        
        sys.stdout.write("\n".join(buffer))
        sys.stdout.flush()

    def generate(self):
        """Recursive Backtracker to generate a maze."""
        stack = [self.start]
        self.grid[self.start[1]][self.start[0]] = CellType.PATH
        
        visited = {self.start}

        while stack:
            cx, cy = stack[-1]
            
            # Find unvisited neighbors (distance 2 away)
            neighbors = []
            for dx, dy in [(0, -2), (0, 2), (-2, 0), (2, 0)]:
                nx, ny = cx + dx, cy + dy
                if 1 <= nx < self.width - 1 and 1 <= ny < self.height - 1:
                    if (nx, ny) not in visited:
                        neighbors.append((nx, ny))
            
            if neighbors:
                nx, ny = random.choice(neighbors)
                # Remove wall between current and chosen
                wx, wy = (cx + nx) // 2, (cy + ny) // 2
                self.grid[wy][wx] = CellType.PATH
                self.grid[ny][nx] = CellType.PATH
                
                visited.add((nx, ny))
                stack.append((nx, ny))
                
                # Animate
                self.print_grid(overrides={(nx, ny): Color.GEN_HEAD, (wx, wy): Color.GEN_HEAD})
                time.sleep(DELAY / 2)
            else:
                stack.pop()
                # Backtracking animation (optional, subtle)
                # self.print_grid(overrides={(cx, cy): Color.GEN_HEAD})
                # time.sleep(DELAY / 4)

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def solve_a_star(self):
        """A* Pathfinding Algorithm."""
        start_node = self.start
        goal_node = self.end
        
        open_set = []
        heapq.heappush(open_set, (0, start_node))
        
        came_from = {}
        g_score = {start_node: 0}
        f_score = {start_node: self.heuristic(start_node, goal_node)}
        
        open_set_hash = {start_node}
        closed_set = set()

        while open_set:
            current = heapq.heappop(open_set)[1]
            open_set_hash.discard(current)
            closed_set.add(current)

            if current == goal_node:
                return self.reconstruct_path(came_from, current)

            # Neighbors (distance 1, strictly paths)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                if 0 <= neighbor[0] < self.width and 0 <= neighbor[1] < self.height:
                    if self.grid[neighbor[1]][neighbor[0]] == CellType.WALL:
                        continue
                    
                    tentative_g_score = g_score[current] + 1
                    
                    if tentative_g_score < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal_node)
                        
                        if neighbor not in open_set_hash:
                            heapq.heappush(open_set, (f_score[neighbor], neighbor))
                            open_set_hash.add(neighbor)
            
            # Animation: Show Open vs Closed sets
            overrides = {}
            for n in closed_set: overrides[n] = Color.SOLVE_CLOSED
            for n in open_set_hash: overrides[n] = Color.SOLVE_OPEN
            overrides[current] = Color.GEN_HEAD # Current head
            
            if len(closed_set) % 2 == 0: # Throttle rendering slightly for speed
               self.print_grid(overrides)
               time.sleep(DELAY)

        return None # No path found

    def reconstruct_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        total_path.reverse()
        
        # Animate Final Path
        for i in range(len(total_path)):
            path_subset = total_path[:i+1]
            overrides = {node: Color.FINAL_PATH for node in path_subset}
            self.print_grid(overrides)
            time.sleep(DELAY / 2)
            
        return total_path

def main():
    # Initial Clear
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Initializing Maze AI Demo...")
    time.sleep(1)
    
    maze = MazeDemo(WIDTH, HEIGHT)
    
    # 1. Generation
    maze.print_grid()
    print(f"{Color.RESET}\n Phase 1: Generating Maze (Recursive Backtracker)...")
    time.sleep(1)
    maze.generate()
    
    # 2. Solving
    print(f"{Color.RESET}\n Phase 2: Solving Maze (A* Algorithm)...       ")
    time.sleep(1)
    maze.solve_a_star()
    
    print(f"\n{Color.RESET}Demo Complete. The A* algorithm has found the optimal path.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Color.RESET}Demo interrupted by user.")
