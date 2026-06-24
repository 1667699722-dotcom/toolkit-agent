import os
import sys
import json
import random
import pygame
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

BLACK = (10, 10, 10)
WHITE = (245, 245, 245)
GOLD = (212, 175, 55)

def get_chinese_font(size=24):
    fonts = [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/SFNS.ttc',
        '/Library/Fonts/Microsoft/SimHei.ttf',
        '/Library/Fonts/Microsoft/SimSun.ttf',
    ]
    for font_path in fonts:
        if os.path.exists(font_path):
            try:
                return pygame.font.Font(font_path, size)
            except:
                continue
    return pygame.font.Font(None, size)

class PixelFont:
    def __init__(self):
        pygame.font.init()
        self.font_small = get_chinese_font(18)
        self.font_medium = get_chinese_font(22)
        self.font_large = get_chinese_font(28)
    
    def render(self, text, color=WHITE, size='medium'):
        if size == 'small':
            return self.font_small.render(text, True, color)
        elif size == 'large':
            return self.font_large.render(text, True, color)
        return self.font_medium.render(text, True, color)

class Maze:
    def __init__(self, rows, cols):
        self.rows = rows if rows % 2 == 1 else rows + 1
        self.cols = cols if cols % 2 == 1 else cols + 1
        self.grid = [[1 for _ in range(self.cols)] for _ in range(self.rows)]
        self.start = (1, 1)
        self.end = (self.rows - 2, self.cols - 2)
        self.generate_maze()
    
    def generate_maze(self):
        self._dfs_generate()
        self._braid_maze(0.35)
    
    def _dfs_generate(self):
        stack = [self.start]
        self.grid[self.start[0]][self.start[1]] = 0
        
        directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        
        while stack:
            current = stack[-1]
            row, col = current
            
            neighbors = []
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                
                if 1 <= new_row < self.rows - 1 and 1 <= new_col < self.cols - 1:
                    if self.grid[new_row][new_col] == 1:
                        neighbors.append((new_row, new_col, dr, dc))
            
            if neighbors:
                idx = random.randint(0, len(neighbors) - 1)
                new_row, new_col, dr, dc = neighbors[idx]
                
                wall_row = row + dr // 2
                wall_col = col + dc // 2
                
                self.grid[wall_row][wall_col] = 0
                self.grid[new_row][new_col] = 0
                
                stack.append((new_row, new_col))
            else:
                stack.pop()
        
        self.grid[self.end[0]][self.end[1]] = 0
    
    def _braid_maze(self, probability):
        dead_ends = []
        
        for row in range(1, self.rows - 1):
            for col in range(1, self.cols - 1):
                if self.grid[row][col] == 0:
                    open_neighbors = 0
                    if self.grid[row - 1][col] == 0:
                        open_neighbors += 1
                    if self.grid[row + 1][col] == 0:
                        open_neighbors += 1
                    if self.grid[row][col - 1] == 0:
                        open_neighbors += 1
                    if self.grid[row][col + 1] == 0:
                        open_neighbors += 1
                    
                    if open_neighbors == 1:
                        dead_ends.append((row, col))
        
        random.shuffle(dead_ends)
        
        for row, col in dead_ends:
            if random.random() < probability:
                walls = []
                if row > 1 and self.grid[row - 1][col] == 1:
                    walls.append((row - 1, col))
                if row < self.rows - 2 and self.grid[row + 1][col] == 1:
                    walls.append((row + 1, col))
                if col > 1 and self.grid[row][col - 1] == 1:
                    walls.append((row, col - 1))
                if col < self.cols - 2 and self.grid[row][col + 1] == 1:
                    walls.append((row, col + 1))
                
                if walls:
                    wr, wc = random.choice(walls)
                    if wr > 0 and wr < self.rows - 1 and wc > 0 and wc < self.cols - 1:
                        self.grid[wr][wc] = 0
    
    def get_cell(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        return 1
    
    def get_cell_info(self, x, y):
        z = self.get_cell(y, x)
        return {"x": x, "y": y, "z": z}
    
    def get_all_cells(self):
        cells = []
        for y in range(self.rows):
            for x in range(self.cols):
                cells.append(self.get_cell_info(x, y))
        return cells
    
    def detect_surroundings(self, x, y):
        surroundings = {}
        
        directions = {
            "up": (x, y - 1),
            "down": (x, y + 1),
            "left": (x - 1, y),
            "right": (x + 1, y)
        }
        
        for direction, (nx, ny) in directions.items():
            surroundings[direction] = self.get_cell_info(nx, ny)
        
        return surroundings
    
    def save_to_json(self, filename="maze_data.json"):
        data = {
            "rows": self.rows,
            "cols": self.cols,
            "start": {"x": self.start[1], "y": self.start[0]},
            "end": {"x": self.end[1], "y": self.end[0]},
            "cells": self.get_all_cells()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return filename
    
    def reset(self):
        self.grid = [[1 for _ in range(self.cols)] for _ in range(self.rows)]
        self.generate_maze()

class MazeGame:
    def __init__(self):
        pygame.init()
        self.cell_size = 25
        self.maze_rows = 21
        self.maze_cols = 21
        
        self.screen_width = self.maze_cols * self.cell_size + 40
        self.screen_height = self.maze_rows * self.cell_size + 60
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("迷宫游戏")
        
        self.font = PixelFont()
        self.maze = Maze(self.maze_rows, self.maze_cols)
        self.player_pos = self.maze.start
        self.path = [self.maze.start]
        self.running = True
        
        self.WALL_COLOR = (50, 30, 15)
        self.PATH_COLOR = (240, 230, 210)
        self.START_COLOR = (50, 200, 50)
        self.END_COLOR = (200, 50, 50)
        self.PLAYER_COLOR = (50, 100, 200)
        self.BG_COLOR = (90, 51, 32)
        self.PATH_TRAIL = (200, 180, 160)
        
        self.detected_cells = {}
        self.init_json_file()
        self.detect_and_record()
        self.save_detected_data()
    
    def init_json_file(self):
        data = {
            "__metadata": {
                "description": "迷宫游戏数据，用于AI操控角色探索迷宫",
                "coordinate_system": "平面直角坐标系，(0,0)在左上角，x轴向右，y轴向下",
                "cell_states": {
                    "0": "可通行路径，角色可以移动到此位置",
                    "1": "墙壁/障碍，角色无法通过"
                },
                "movement_directions": {
                    "up": "y-1，向上移动",
                    "down": "y+1，向下移动",
                    "left": "x-1，向左移动",
                    "right": "x+1，向右移动"
                },
                "goal": "到达红色终点 (x="+str(self.maze.end[1])+", y="+str(self.maze.end[0])+")"
            },
            "player_position": {
                "__description": "玩家当前位置坐标",
                "x": self.player_pos[1],
                "y": self.player_pos[0]
            },
            "detected_cells": [],
            "total_detected": 0
        }
        
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maze_detected.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return filename
    
    def save_detected_data(self):
        data = {
            "__metadata": {
                "description": "迷宫游戏数据，用于AI操控角色探索迷宫",
                "coordinate_system": "平面直角坐标系，(0,0)在左上角，x轴向右，y轴向下",
                "cell_states": {
                    "0": "可通行路径，角色可以移动到此位置",
                    "1": "墙壁/障碍，角色无法通过"
                },
                "movement_directions": {
                    "up": "y-1，向上移动",
                    "down": "y+1，向下移动",
                    "left": "x-1，向左移动",
                    "right": "x+1，向右移动"
                },
                "goal": "到达红色终点 (x="+str(self.maze.end[1])+", y="+str(self.maze.end[0])+")"
            },
            "player_position": {
                "__description": "玩家当前位置坐标",
                "x": self.player_pos[1],
                "y": self.player_pos[0]
            },
            "detected_cells": list(self.detected_cells.values()),
            "total_detected": len(self.detected_cells)
        }
        
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maze_detected.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return filename
    
    def detect_and_record(self):
        y, x = self.player_pos
        surroundings = self.maze.detect_surroundings(x, y)
        
        z_val = self.maze.get_cell(y, x)
        self.detected_cells[(x, y)] = {
            "x": x,
            "y": y,
            "z": z_val,
            "__description": "当前玩家位置" + ("，可通行" if z_val == 0 else "，障碍")
        }
        
        for direction, cell in surroundings.items():
            cx, cy, cz = cell["x"], cell["y"], cell["z"]
            self.detected_cells[(cx, cy)] = {
                "x": cx,
                "y": cy,
                "z": cz,
                "__description": direction + "方向，" + ("可通行" if cz == 0 else "障碍")
            }
    
    def move_player(self, dx, dy):
        new_row = self.player_pos[0] + dy
        new_col = self.player_pos[1] + dx
        
        if 0 <= new_row < self.maze_rows and 0 <= new_col < self.maze_cols:
            if self.maze.get_cell(new_row, new_col) == 0:
                self.player_pos = (new_row, new_col)
                if self.player_pos not in self.path:
                    self.path.append(self.player_pos)
                
                self.detect_and_record()
                self.save_detected_data()
                return True
        
        return False
    
    def draw(self):
        self.screen.fill(self.BG_COLOR)
        
        start_x = 20
        start_y = 40
        
        for row in range(self.maze.rows):
            for col in range(self.maze.cols):
                cell_x = start_x + col * self.cell_size
                cell_y = start_y + row * self.cell_size
                
                if self.maze.get_cell(row, col) == 1:
                    pygame.draw.rect(self.screen, self.WALL_COLOR,
                                    (cell_x, cell_y, self.cell_size - 1, self.cell_size - 1))
                else:
                    pygame.draw.rect(self.screen, self.PATH_COLOR,
                                    (cell_x, cell_y, self.cell_size - 1, self.cell_size - 1))
        
        for pos in self.path:
            trail_x = start_x + pos[1] * self.cell_size + 2
            trail_y = start_y + pos[0] * self.cell_size + 2
            pygame.draw.rect(self.screen, self.PATH_TRAIL,
                            (trail_x, trail_y, self.cell_size - 5, self.cell_size - 5))
        
        start_x_draw = start_x + self.maze.start[1] * self.cell_size
        start_y_draw = start_y + self.maze.start[0] * self.cell_size
        pygame.draw.rect(self.screen, self.START_COLOR,
                        (start_x_draw + 2, start_y_draw + 2, self.cell_size - 5, self.cell_size - 5))
        
        end_x_draw = start_x + self.maze.end[1] * self.cell_size
        end_y_draw = start_y + self.maze.end[0] * self.cell_size
        pygame.draw.rect(self.screen, self.END_COLOR,
                        (end_x_draw + 2, end_y_draw + 2, self.cell_size - 5, self.cell_size - 5))
        
        player_x_draw = start_x + self.player_pos[1] * self.cell_size
        player_y_draw = start_y + self.player_pos[0] * self.cell_size
        pygame.draw.circle(self.screen, self.PLAYER_COLOR,
                         (player_x_draw + self.cell_size // 2, player_y_draw + self.cell_size // 2),
                         self.cell_size // 3)
        
        title_surface = self.font.render("迷宫游戏", GOLD, 'large')
        self.screen.blit(title_surface, (self.screen_width // 2 - title_surface.get_width() // 2, 8))
        
        hint_surface = self.font.render("方向键移动 | R重置", GOLD, 'small')
        self.screen.blit(hint_surface, (self.screen_width // 2 - hint_surface.get_width() // 2, self.screen_height - 25))
        
        pygame.display.flip()
    
    def reset(self):
        self.maze.reset()
        self.player_pos = self.maze.start
        self.path = [self.maze.start]
        self.detected_cells = {}
        self.detect_and_record()
        self.save_detected_data()
    
    def check_command_file(self):
        cmd_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maze_command.json")
        if os.path.exists(cmd_file):
            try:
                with open(cmd_file, 'r', encoding='utf-8') as f:
                    cmd = json.load(f)
                
                if cmd.get("command") == "move":
                    direction = cmd.get("direction", "")
                    if direction == "up":
                        self.move_player(0, -1)
                    elif direction == "down":
                        self.move_player(0, 1)
                    elif direction == "left":
                        self.move_player(-1, 0)
                    elif direction == "right":
                        self.move_player(1, 0)
                
                elif cmd.get("command") == "reset":
                    self.reset()
                
                elif cmd.get("command") == "stop":
                    self.init_json_file()
                    self.running = False
                
                os.remove(cmd_file)
            except Exception as e:
                print(f"Error reading command: {e}")
                try:
                    os.remove(cmd_file)
                except:
                    pass
    
    def run(self):
        clock = pygame.time.Clock()
        self.detect_and_record()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.init_json_file()
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.init_json_file()
                        self.running = False
                    elif event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_UP:
                        self.move_player(0, -1)
                    elif event.key == pygame.K_DOWN:
                        self.move_player(0, 1)
                    elif event.key == pygame.K_LEFT:
                        self.move_player(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.move_player(1, 0)
            
            self.check_command_file()
            
            if self.player_pos == self.maze.end:
                self.reset()
            
            self.draw()
            clock.tick(30)
        
        pygame.quit()

if __name__ == "__main__":
    game = MazeGame()
    game.run()
