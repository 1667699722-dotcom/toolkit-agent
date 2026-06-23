import os
import sys
import json
import pygame
import threading
import time
from queue import Queue

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from toolkit_agent import chat, API_KEY, set_log_callback

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (64, 64, 64)
LIGHT_GRAY = (128, 128, 128)
DARK_GRAY = (32, 32, 32)
PINK = (255, 182, 193)
LIGHT_PINK = (255, 228, 225)
BLUE = (135, 206, 235)
LIGHT_BLUE = (176, 196, 222)
PURPLE = (148, 0, 211)
LIGHT_PURPLE = (221, 160, 221)

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
    
    def size(self, text, size='medium'):
        if size == 'small':
            return self.font_small.size(text)
        elif size == 'large':
            return self.font_large.size(text)
        return self.font_medium.size(text)
    
    def wrap_text(self, text, max_width, size='medium'):
        lines = []
        current_line = ""
        font = self.font_small if size == 'small' else (self.font_large if size == 'large' else self.font_medium)
        
        for char in text:
            test_line = current_line + char
            if font.size(test_line)[0] > max_width:
                lines.append(current_line)
                current_line = char
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
        return lines

class PixelPanel:
    def __init__(self, x, y, width, height, title="", color=DARK_GRAY):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title
        self.color = color
        self.border_color = LIGHT_GRAY
        self.border_width = 2
    
    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        
        pygame.draw.rect(screen, self.border_color, 
                        (self.x, self.y, self.width, self.border_width))
        pygame.draw.rect(screen, self.border_color, 
                        (self.x, self.y + self.height - self.border_width, self.width, self.border_width))
        pygame.draw.rect(screen, self.border_color, 
                        (self.x, self.y, self.border_width, self.height))
        pygame.draw.rect(screen, self.border_color, 
                        (self.x + self.width - self.border_width, self.y, self.border_width, self.height))
        
        if self.title:
            title_surface = font.render(self.title, LIGHT_BLUE, 'small')
            screen.blit(title_surface, (self.x + 8, self.y + 4))

class DialogBox:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.panel = PixelPanel(x, y, width, height, "对话")
        self.messages = []
        self.input_text = ""
        self.max_messages = 20
        self.font = PixelFont()
    
    def add_message(self, speaker, text):
        self.messages.append({"speaker": speaker, "text": text})
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def draw(self, screen):
        self.panel.draw(screen, self.font)
        
        y_offset = 30
        visible_messages = []
        
        for msg in reversed(self.messages):
            speaker_lines = [msg["speaker"] + ":"]
            text_lines = self.font.wrap_text(msg["text"], self.width - 24, 'small')
            
            total_lines = len(speaker_lines) + len(text_lines)
            total_height = total_lines * 22
            
            if y_offset + total_height <= self.height - 80:
                visible_messages.insert(0, {"speaker": msg["speaker"], "speaker_lines": speaker_lines, "text_lines": text_lines})
                y_offset += total_height
            else:
                break
        
        y_offset = 30
        for msg in visible_messages:
            color = PINK if msg["speaker"] == "林离" else BLUE
            
            for i, line in enumerate(msg["speaker_lines"]):
                speaker_surface = self.font.render(line, color, 'small')
                screen.blit(speaker_surface, (self.x + 8, self.y + y_offset))
                y_offset += 22
            
            for i, line in enumerate(msg["text_lines"]):
                text_surface = self.font.render(line, WHITE, 'small')
                screen.blit(text_surface, (self.x + 8, self.y + y_offset))
                y_offset += 22
        
        input_box_y = self.y + self.height - 50
        pygame.draw.rect(screen, GRAY, (self.x + 8, input_box_y, self.width - 16, 36))
        pygame.draw.rect(screen, LIGHT_GRAY, (self.x + 8, input_box_y, self.width - 16, 2))
        
        prompt_surface = self.font.render("你:", BLUE, 'small')
        screen.blit(prompt_surface, (self.x + 16, input_box_y + 8))
        
        input_surface = self.font.render(self.input_text, WHITE, 'small')
        screen.blit(input_surface, (self.x + 50, input_box_y + 8))
        
        cursor_x = self.x + 50 + self.font.size(self.input_text, 'small')[0]
        pygame.draw.rect(screen, WHITE, (cursor_x, input_box_y + 8, 2, 16))

class LogPanel:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.panel = PixelPanel(x, y, width, height, "日志")
        self.logs = []
        self.max_logs = 50
        self.font = PixelFont()
    
    def add_log(self, text, type="info"):
        self.logs.append({"text": text, "type": type})
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
    
    def draw(self, screen):
        self.panel.draw(screen, self.font)
        
        y_offset = self.height - 20
        
        for log in reversed(self.logs):
            if log["type"] == "tool":
                color = LIGHT_PURPLE
            elif log["type"] == "result":
                color = PINK
            elif log["type"] == "error":
                color = (255, 100, 100)
            else:
                color = LIGHT_GRAY
            
            lines = self.font.wrap_text(log['text'], self.width - 24, 'small')
            
            for line in reversed(lines):
                line_surface = self.font.render(line, color, 'small')
                screen.blit(line_surface, (self.x + 8, y_offset - 22))
                y_offset -= 22
                
                if y_offset < 30:
                    return

class CharacterSprite:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.panel = PixelPanel(x, y, width, height, "林离")
        self.pixel_art = self._create_pixel_art()
        self.font = PixelFont()
        self.is_thinking = False
        self.think_timer = 0
    
    def _create_pixel_art(self):
        img = pygame.Surface((240, 320), pygame.SRCALPHA)
        img.fill((0, 0, 0, 0))
        
        HAIR_DARK = (70, 45, 95)
        HAIR_MID = (100, 65, 130)
        HAIR_LIGHT = (130, 90, 165)
        SKIN = (255, 235, 220)
        SKIN_DARK = (240, 215, 195)
        EYES = (45, 30, 65)
        EYE_HIGHLIGHT = (255, 255, 255)
        BLUSH = (255, 185, 195)
        LIP = (230, 130, 150)
        DRESS_DARK = (100, 120, 160)
        DRESS_MID = (130, 155, 195)
        DRESS_LIGHT = (165, 190, 225)
        ACCENT = (180, 140, 200)
        
        # 背景光晕
        for i in range(20):
            alpha = max(0, 40 - i * 2)
            pygame.draw.circle(img, (100, 80, 120, alpha), (120, 160), 100 - i * 5)
        
        # 头发 - 左侧长发
        pygame.draw.rect(img, HAIR_DARK, (40, 80, 30, 180))
        pygame.draw.rect(img, HAIR_MID, (55, 80, 15, 180))
        pygame.draw.rect(img, HAIR_LIGHT, (65, 85, 10, 170))
        
        # 头发 - 右侧长发
        pygame.draw.rect(img, HAIR_DARK, (170, 80, 30, 180))
        pygame.draw.rect(img, HAIR_MID, (170, 80, 15, 180))
        pygame.draw.rect(img, HAIR_LIGHT, (170, 85, 8, 170))
        
        # 头发 - 头顶和刘海
        pygame.draw.rect(img, HAIR_DARK, (60, 40, 120, 70))
        pygame.draw.rect(img, HAIR_MID, (70, 50, 100, 50))
        pygame.draw.rect(img, HAIR_LIGHT, (80, 55, 80, 30))
        
        # 刘海细节
        pygame.draw.rect(img, HAIR_DARK, (75, 90, 8, 20))
        pygame.draw.rect(img, HAIR_DARK, (100, 95, 8, 18))
        pygame.draw.rect(img, HAIR_DARK, (125, 92, 8, 20))
        pygame.draw.rect(img, HAIR_DARK, (145, 88, 8, 22))
        
        # 脸部轮廓
        pygame.draw.rect(img, SKIN, (85, 80, 70, 80))
        
        # 脸部阴影
        pygame.draw.rect(img, SKIN_DARK, (85, 85, 8, 70))
        pygame.draw.rect(img, SKIN_DARK, (147, 85, 8, 70))
        
        # 眼睛 - 白色
        pygame.draw.rect(img, (240, 245, 255), (95, 95, 16, 12))
        pygame.draw.rect(img, (240, 245, 255), (129, 95, 16, 12))
        
        # 眼睛 - 瞳孔
        pygame.draw.rect(img, EYES, (100, 98, 8, 8))
        pygame.draw.rect(img, EYES, (134, 98, 8, 8))
        
        # 眼睛高光
        pygame.draw.rect(img, EYE_HIGHLIGHT, (101, 99, 3, 3))
        pygame.draw.rect(img, EYE_HIGHLIGHT, (135, 99, 3, 3))
        pygame.draw.rect(img, (200, 210, 230), (104, 102, 2, 2))
        pygame.draw.rect(img, (200, 210, 230), (138, 102, 2, 2))
        
        # 眉毛
        pygame.draw.rect(img, HAIR_DARK, (95, 88, 14, 3))
        pygame.draw.rect(img, HAIR_DARK, (131, 88, 14, 3))
        
        # 鼻子
        pygame.draw.rect(img, SKIN_DARK, (120, 112, 8, 6))
        
        # 嘴巴
        pygame.draw.rect(img, LIP, (112, 128, 16, 5))
        pygame.draw.rect(img, (255, 190, 200), (114, 128, 12, 3))
        
        # 腮红
        pygame.draw.rect(img, BLUSH, (90, 115, 8, 6))
        pygame.draw.rect(img, BLUSH, (142, 115, 8, 6))
        
        # 耳朵
        pygame.draw.rect(img, SKIN, (80, 100, 8, 15))
        pygame.draw.rect(img, SKIN, (152, 100, 8, 15))
        
        # 连衣裙 - 上身
        pygame.draw.rect(img, DRESS_DARK, (85, 160, 70, 60))
        
        # 连衣裙 - 褶皱
        pygame.draw.rect(img, DRESS_MID, (95, 165, 8, 50))
        pygame.draw.rect(img, DRESS_MID, (115, 165, 8, 50))
        pygame.draw.rect(img, DRESS_MID, (135, 165, 8, 50))
        
        # 连衣裙 - 领口
        pygame.draw.rect(img, DRESS_LIGHT, (105, 160, 30, 8))
        
        # 蝴蝶结装饰
        pygame.draw.rect(img, ACCENT, (115, 155, 10, 8))
        pygame.draw.rect(img, ACCENT, (110, 160, 6, 10))
        pygame.draw.rect(img, ACCENT, (124, 160, 6, 10))
        
        # 连衣裙 - 裙摆
        pygame.draw.rect(img, DRESS_DARK, (75, 220, 90, 80))
        
        # 裙摆波浪
        for i in range(5):
            pygame.draw.rect(img, DRESS_MID, (80 + i * 18, 220, 12, 5))
        
        # 裙摆褶皱
        pygame.draw.rect(img, DRESS_MID, (85, 230, 5, 60))
        pygame.draw.rect(img, DRESS_MID, (115, 230, 5, 60))
        pygame.draw.rect(img, DRESS_MID, (145, 230, 5, 60))
        
        # 手臂 - 左侧
        pygame.draw.rect(img, SKIN, (70, 170, 15, 60))
        pygame.draw.rect(img, SKIN_DARK, (70, 175, 6, 50))
        
        # 手臂 - 右侧
        pygame.draw.rect(img, SKIN, (155, 170, 15, 60))
        pygame.draw.rect(img, SKIN_DARK, (164, 175, 6, 50))
        
        # 手
        pygame.draw.rect(img, SKIN, (68, 225, 18, 10))
        pygame.draw.rect(img, SKIN, (154, 225, 18, 10))
        
        # 头发装饰 - 发夹
        pygame.draw.rect(img, ACCENT, (150, 60, 15, 8))
        pygame.draw.rect(img, (255, 240, 200), (152, 62, 11, 4))
        
        # 背景星星装饰
        stars = [
            (30, 50), (210, 60), (40, 280), (200, 290),
            (20, 180), (220, 170), (50, 120), (190, 130)
        ]
        for x, y in stars:
            pygame.draw.rect(img, (200, 180, 220, 100), (x, y, 3, 3))
        
        return img
    
    def update(self):
        if self.is_thinking:
            self.think_timer += 1
    
    def set_thinking(self, thinking):
        self.is_thinking = thinking
        self.think_timer = 0
    
    def draw(self, screen):
        self.panel.draw(screen, self.font)
        
        art_width, art_height = self.pixel_art.get_size()
        center_x = self.x + (self.width - art_width) // 2
        center_y = self.y + (self.height - art_height) // 2
        screen.blit(self.pixel_art, (center_x, center_y))
        
        if self.is_thinking:
            bubble_y = self.y + 30
            bubble_x = self.x + self.width // 2
            
            bubble_size = 20 + (self.think_timer // 5) % 10
            pygame.draw.circle(screen, WHITE, (bubble_x, bubble_y), bubble_size, 2)
            
            for i in range(3):
                dot_y = bubble_y + i * 8 - 8
                dot_size = 3 + (self.think_timer // 3 + i) % 4
                pygame.draw.circle(screen, WHITE, (bubble_x, dot_y), dot_size)

class GameGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("林离 - 你的专属陪伴者")
        
        self.font = PixelFont()
        
        self.character = CharacterSprite(20, 20, 680, 360)
        self.dialog_box = DialogBox(20, 400, 680, 340)
        self.log_panel = LogPanel(720, 20, 280, 720)
        
        self.running = True
        self.processing = False
        self.chat_queue = Queue()
        self.log_queue = Queue()
        
        self._setup_background()
        
        self.dialog_box.add_message("系统", "林离已连接。今天有什么想聊聊的吗？")
        
        set_log_callback(self._on_log)
        
        threading.Thread(target=self._chat_worker, daemon=True).start()
    
    def _setup_background(self):
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.background.fill(DARK_GRAY)
        
        for i in range(0, SCREEN_WIDTH, 64):
            for j in range(0, SCREEN_HEIGHT, 64):
                if (i // 64 + j // 64) % 2 == 0:
                    pygame.draw.rect(self.background, (30, 30, 35), (i, j, 64, 64))
        
        for i in range(0, SCREEN_WIDTH, 16):
            pygame.draw.line(self.background, (25, 25, 30), (i, 0), (i, SCREEN_HEIGHT))
        for j in range(0, SCREEN_HEIGHT, 16):
            pygame.draw.line(self.background, (25, 25, 30), (0, j), (SCREEN_WIDTH, j))
    
    def _on_log(self, msg, type="info"):
        self.log_queue.put((msg, type))
    
    def _chat_worker(self):
        while True:
            user_input = self.chat_queue.get()
            if user_input is None:
                break
            
            try:
                self.log_queue.put((f"用户输入: {user_input}", "info"))
                
                answer = chat(user_input)
                
                self.dialog_box.add_message("林离", answer)
                
                self.log_queue.put((f"林离回复: {answer[:50]}...", "info"))
                
                self.character.set_thinking(False)
                self.processing = False
            except Exception as e:
                self.log_queue.put((f"错误: {str(e)}", "error"))
                self.dialog_box.add_message("系统", f"抱歉，发生了一些问题：{str(e)}")
                self.character.set_thinking(False)
                self.processing = False
    
    def run(self):
        clock = pygame.time.Clock()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.chat_queue.put(None)
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        self.chat_queue.put(None)
                    
                    elif event.key == pygame.K_RETURN:
                        if self.dialog_box.input_text.strip() and not self.processing:
                            user_input = self.dialog_box.input_text.strip()
                            self.dialog_box.add_message("你", user_input)
                            self.dialog_box.input_text = ""
                            
                            self.processing = True
                            self.character.set_thinking(True)
                            self.chat_queue.put(user_input)
                    
                    elif event.key == pygame.K_BACKSPACE:
                        self.dialog_box.input_text = self.dialog_box.input_text[:-1]
                    
                    elif event.unicode and event.unicode.isprintable():
                        self.dialog_box.input_text += event.unicode
            
            while not self.log_queue.empty():
                msg, type = self.log_queue.get()
                self.log_panel.add_log(msg, type)
            
            self.character.update()
            
            self.screen.blit(self.background, (0, 0))
            
            self.character.draw(self.screen)
            self.dialog_box.draw(self.screen)
            self.log_panel.draw(self.screen)
            
            pygame.display.flip()
            clock.tick(30)
        
        pygame.quit()

if __name__ == "__main__":
    if not API_KEY:
        print("请先设置环境变量 API_KEY")
        print("示例: export API_KEY=sk-xxxxxxxxxxxxxxxx")
        sys.exit(1)
    
    gui = GameGUI()
    gui.run()
