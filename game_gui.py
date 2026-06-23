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
        self.pixel_art = self._load_character_image()
        self.font = PixelFont()
        self.is_thinking = False
        self.think_timer = 0
    
    def _load_character_image(self):
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "olivia.png")
        
        if os.path.exists(image_path):
            try:
                img = pygame.image.load(image_path).convert_alpha()
                img_width, img_height = img.get_size()
                
                scale_w = self.width / img_width
                scale_h = self.height / img_height
                scale = min(scale_w, scale_h)
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                return pygame.transform.smoothscale(img, (new_width, new_height))
            except Exception as e:
                print(f"加载图片失败: {e}")
        
        return self._create_fallback_art()
    
    def _create_fallback_art(self):
        img = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        img.fill((0, 0, 0, 0))
        
        center_x = self.width // 2
        center_y = self.height // 2
        
        pygame.draw.circle(img, (255, 235, 220), (center_x, center_y), 60)
        
        pygame.draw.rect(img, (30, 25, 35), (center_x - 80, center_y - 50, 160, 120))
        
        pygame.draw.rect(img, (240, 245, 255), (center_x - 35, center_y - 15, 12, 10))
        pygame.draw.rect(img, (240, 245, 255), (center_x + 23, center_y - 15, 12, 10))
        pygame.draw.rect(img, (60, 70, 90), (center_x - 32, center_y - 12, 6, 6))
        pygame.draw.rect(img, (60, 70, 90), (center_x + 26, center_y - 12, 6, 6))
        
        pygame.draw.rect(img, (255, 185, 195), (center_x - 40, center_y + 10, 8, 5))
        pygame.draw.rect(img, (255, 185, 195), (center_x + 32, center_y + 10, 8, 5))
        
        pygame.draw.rect(img, (230, 130, 150), (center_x - 8, center_y + 25, 16, 4))
        
        pygame.draw.rect(img, (245, 240, 235), (center_x - 50, center_y + 45, 100, 80))
        pygame.draw.rect(img, (150, 155, 165), (center_x - 80, center_y + 45, 30, 80))
        pygame.draw.rect(img, (150, 155, 165), (center_x + 50, center_y + 45, 30, 80))
        
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

def check_environment():
    errors = []
    
    if not API_KEY:
        errors.append("❌ API_KEY 未设置，请在 run.sh 中配置")
    
    packages = ["openai", "pygame", "numpy", "magenta_rt"]
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            errors.append(f"❌ 缺少 Python 包: {pkg} (请运行: pip install {pkg})")
    
    magenta_path = os.path.expanduser("~/Documents/Magenta/magenta-rt-v2")
    if not os.path.exists(magenta_path):
        errors.append(f"❌ Magenta 模型目录不存在: {magenta_path}")
    else:
        model_path = os.path.join(magenta_path, "models", "mrt2_small")
        if not os.path.exists(model_path):
            errors.append(f"❌ mrt2_small 模型不存在: {model_path}")
    
    return errors

if __name__ == "__main__":
    errors = check_environment()
    
    if errors:
        print("环境检查失败，缺少以下组件：")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    
    gui = GameGUI()
    gui.run()
