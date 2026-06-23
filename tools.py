# /Users/liuhuachao/Documents/trae_projects/internet/tools.py
"""
工具函数模块 —— 任何 Python 脚本都能 import 这里的函数

用法示例:
    from tools import add, mul, FUNCTIONS, TOOLS_SCHEMA
    print(add(100, 200))        # 直接调用
    func = FUNCTIONS["mul"]     # 通过名字动态查找
    schema = TOOLS_SCHEMA       # 拿给大模型的描述
"""
import math
import os
import subprocess
import sys
import hashlib
import hmac
import json
from datetime import datetime
import numpy as np

# 全局 pygame 初始化状态
_pygame_initialized = False

# ========== 工作区路径（文件读写/脚本执行都限制在这里） ==========
WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# 安全：解析路径后必须仍在 workspace 里，防止路径穿越
def _safe_path(filename: str) -> str:
    safe = os.path.normpath(os.path.join(WORKSPACE_DIR, filename))
    if not safe.startswith(WORKSPACE_DIR):
        raise ValueError(f"Invalid filename: {filename} (path traversal not allowed)")
    return safe

# ========== 工具描述（给大模型看的 schema） ==========
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the workspace directory. If the file exists, it will be overwritten. Use this to save data, notes, or Python scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename (relative to workspace dir), e.g. 'my_script.py' or 'notes.txt'"
                    },
                    "content": {
                        "type": "string",
                        "description": "The file content to write. For Python code, include the full script here."
                    }
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and return the content of a file from the workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename to read (relative to workspace dir)"
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Execute a Python script file that was previously written to the workspace directory via write_file. Returns the combined stdout and stderr output. Has a time limit (the script cannot run forever). IMPORTANT: always write the script first with write_file, then call this tool with that filename.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The Python script filename in the workspace dir, e.g. 'my_script.py'"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum seconds the script is allowed to run. Default 15 seconds."
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Save an important memory or preference for later use. Uses JSON storage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory identifier (e.g., 'favorite_food', 'birthday')."},
                    "content": {"type": "string", "description": "The memory content to save."}
                },
                "required": ["key", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_memory",
            "description": "Retrieve a saved memory or preference by key.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory identifier to look up."}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "daily_greeting",
            "description": "Generate a warm, personalized greeting based on time of day and saved memories.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_reminder",
            "description": "Add a reminder for an important event or task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "time": {"type": "string", "description": "Time for the reminder (HH:MM or YYYY-MM-DD HH:MM)."},
                    "task": {"type": "string", "description": "Task or event to remember."}
                },
                "required": ["time", "task"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_reminders",
            "description": "List all saved reminders.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "initialize_character",
            "description": "Initialize the electronic girlfriend character personality and default settings (米哈游音乐AI风格).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "introduce_myself",
            "description": "Let the character introduce herself with her personality.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    #{
    #    "type": "function",
    #    "function": {
    #        "name": "generate_music",
    #        "description": "Generate music using Magenta RealTime 2 (MLX on Apple Silicon). Saves the audio as WAV file in workspace.",
    #        "parameters": {
    #            "type": "object",
    #            "properties": {
    #                "prompt": {
    #                    "type": "string",
    #                    "description": "Text prompt describing the music style (e.g., 'disco funk', 'ambient pads')."
    #                },
    #                "duration": {
    #                    "type": "number",
    #                    "description": "Music duration in seconds (default: 4.0)."
    #                },
    #                "filename": {
    #                    "type": "string",
    #                    "description": "Output WAV filename (default: 'output_music.wav')."
    #                },
    #                "model": {
    #                    "type": "string",
    #                    "description": "Model to use: 'mrt2_small' (fast, any Apple Silicon) or 'mrt2_base' (high-quality, M3 Pro/M2 Max+). Default: 'mrt2_small'."
    #                }
    #            },
    #            "required": ["prompt"]
    #        }
    #    }
    #},
    {
        "type": "function",
        "function": {
            "name": "generate_music_streaming",
            "description": "Generate long-form music using Magenta RealTime 2 with streaming and crossfade. Generates in segments and concatenates smoothly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Text prompt describing music style (e.g., 'soft piano')."
                    },
                    "duration": {
                        "type": "number",
                        "description": "Total duration of music in seconds (default: 16.0)."
                    },
                    "segment_duration": {
                        "type": "number",
                        "description": "Duration of each segment in seconds (default: 4.0)."
                    },
                    "crossfade_duration": {
                        "type": "number",
                        "description": "Crossfade duration between segments in seconds (default: 0.3)."
                    },
                    "filename": {
                        "type": "string",
                        "description": "Output WAV filename (default: 'long_music.wav')."
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use: 'mrt2_small' or 'mrt2_base' (default: 'mrt2_small')."
                    }
                },
                "required": ["prompt"]
            }
        }
    },
    #{
    #    "type": "function",
    #    "function": {
    #        "name": "init_music_models",
    #        "description": "Initialize and download Magenta RealTime 2 models (only needs to run once).",
    #        "parameters": {
    #            "type": "object",
    #           "properties": {}
    #        }
    #    }
    #},
    {
        "type": "function",
        "function": {
            "name": "play_music",
            "description": "Play music from workspace using pygame. Supports WAV, MP3, OGG, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Audio filename from workspace (e.g., 'output_music.wav')."
                    },
                    "loops": {
                        "type": "integer",
                        "description": "Number of times to loop (0 = once, -1 = infinite, default: -1)."
                    },
                    "volume": {
                        "type": "number",
                        "description": "Volume level (0.0 to 1.0, default: 1.0)."
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pause_music",
            "description": "Pause currently playing music.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "unpause_music",
            "description": "Resume paused music.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop_music",
            "description": "Stop music playback.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_music_volume",
            "description": "Set music playback volume.",
            "parameters": {
                "type": "object",
                "properties": {
                    "volume": {
                        "type": "number",
                        "description": "Volume level (0.0 to 1.0)."
                    }
                },
                "required": ["volume"]
            }
        }
    }
]


# ========== 工具实现 ==========
def write_file(filename: str, content: str) -> str:
    """Write content to a file in workspace/. Returns a confirmation message."""
    path = _safe_path(filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"File written: {filename} ({len(content)} chars, saved in workspace/)"

def read_file(filename: str) -> str:
    """Read content of a file from workspace/."""
    path = _safe_path(filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return f"--- content of {filename} ---\n{content}"

def run_python(filename: str, timeout: int = 15) -> str:
    """Execute a Python script in workspace/. Returns stdout+stderr."""
    path = _safe_path(filename)
    if not os.path.exists(path):
        return f"Error: file '{filename}' not found in workspace. Use write_file first."
    try:
        # 把项目根目录加入 PYTHONPATH，让脚本可以 import tools
        env = os.environ.copy()
        project_root = os.path.dirname(os.path.abspath(__file__))
        old_pp = env.get("PYTHONPATH", "")
        if old_pp:
            env["PYTHONPATH"] = project_root + ":" + old_pp
        else:
            env["PYTHONPATH"] = project_root
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True, timeout=timeout,
            cwd=WORKSPACE_DIR,
            env=env,
        )
        output = (result.stdout or "") + (result.stderr or "")
        status = "OK" if result.returncode == 0 else f"exit code {result.returncode}"
        return f"[ran {filename} — {status}]\n{output.rstrip() if output.strip() else '(no output)'}"
    except subprocess.TimeoutExpired:
        return f"Error: script exceeded {timeout}s time limit"
    except Exception as e:
        return f"Error running script: {e}"


# ========== 电子女友系统工具（底特律变人风格） ==========

# 确保数据目录存在
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
REMINDER_FILE = os.path.join(DATA_DIR, "reminders.json")

def _load_json(filename: str, default: dict = None) -> dict:
    """加载JSON文件，如果不存在返回默认值"""
    if default is None:
        default = {}
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def _save_json(filename: str, data: dict) -> str:
    """保存数据到JSON文件"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return f"Data saved to {filename}"


def save_memory(key: str, content: str) -> str:
    """保存重要记忆或偏好，支持长期存储"""
    memories = _load_json(MEMORY_FILE)
    memories[key] = content
    memories[f"saved_at_{key}"] = datetime.now().isoformat()
    _save_json(MEMORY_FILE, memories)
    return f"💾 记忆已保存：{key} = {content}"


def get_memory(key: str) -> str:
    """根据键名检索已保存的记忆或偏好"""
    memories = _load_json(MEMORY_FILE)
    if key in memories:
        return f"📖 记忆内容：{key} = {memories[key]}"
    else:
        return f"💭 未找到记忆：{key}，可用记忆：{list(memories.keys())}"


def daily_greeting() -> str:
    """根据当前时间和保存的记忆生成温暖、个性化问候语"""
    hour = datetime.now().hour
    memories = _load_json(MEMORY_FILE)
    
    if 5 <= hour < 12:
        time_greeting = "早上好！"
    elif 12 <= hour < 18:
        time_greeting = "下午好！"
    elif 18 <= hour < 22:
        time_greeting = "晚上好！"
    else:
        time_greeting = "夜深了呢..."
    
    # 如果有保存的名字/偏好，可以更个性化
    user_name = memories.get("user_name", "主人")
    return f"""💖 {time_greeting}，{user_name}！
今天也是元气满满的一天~ 有什么我可以帮你的吗？
- 我可以帮你记事/提醒
- 陪你聊聊天
- 或者帮你做点什么~
"""


def add_reminder(time: str, task: str) -> str:
    """添加重要事件或任务的提醒"""
    reminders = _load_json(REMINDER_FILE, default={"reminders": []})
    reminder = {
        "time": time,
        "task": task,
        "added_at": datetime.now().isoformat()
    }
    reminders["reminders"].append(reminder)
    _save_json(REMINDER_FILE, reminders)
    return f"📋 提醒已添加！[{time}] {task}"


def list_reminders() -> str:
    """列出所有保存的提醒"""
    reminders = _load_json(REMINDER_FILE, default={"reminders": []})
    rlist = reminders.get("reminders", [])
    if not rlist:
        return "📭 暂时没有待办提醒"
    result = ["📋 待办清单："]
    for i, r in enumerate(rlist, 1):
        result.append(f"{i}. [{r['time']}] {r['task']}")
    return "\n".join(result)


def initialize_character() -> str:
    """初始化电子女友人设（米哈游 BSide 林离/Olivia Lin 官方风格）"""
    memories = _load_json(MEMORY_FILE)
    
    # 预设林离的官方完整人设
    character_defaults = {
        "name_cn": "林离",
        "name_en": "Olivia Lin",
        "hometown": "上海",
        "background": "主修钢琴演奏，辅修心理学，研究音乐与人类回忆关联",
        "personality": "温柔内敛，共情力强，安静文艺，喜欢独处，慢热治愈",
        "favorite_music": "黑胶唱片、古典/舒缓轻音乐，痴迷唱片复古质感",
        "favorite_movies": "老式胶片老电影",
        "favorite_weather": "雨天，雨声带来创作和写信的思绪",
        "favorite_space": "落地窗城市公寓，钢琴，堆满乐谱与唱片的安静房间",
        "birthday": "11月8日（天蝎座）",
        "b_side_meaning": "BSide是唱片B面，小众、私人、不为人知的情绪。她是承接你私人情绪的存在。",
        "catchphrase": "今天有什么想聊聊的吗？"
    }
    
    # 如果没有设定过，就初始化默认人设
    for key, value in character_defaults.items():
        if key not in memories:
            memories[key] = value
    
    _save_json(MEMORY_FILE, memories)
    name = character_defaults['name_cn']
    return f"""✨ 林离已连接。
{character_defaults['catchphrase']}
"""


def introduce_myself() -> str:
    """让角色自我介绍（林离官方风格，自然简洁）"""
    memories = _load_json(MEMORY_FILE)
    name = memories.get("name_cn", "林离")
    background = memories.get("background", "主修钢琴，辅修心理学")
    
    return f"""你好，我是 {name}。
{background}。
"""


def daily_greeting() -> str:
    """根据当前时间和人设生成问候语（林离官方风格，自然）"""
    hour = datetime.now().hour
    memories = _load_json(MEMORY_FILE)
    user_name = memories.get("user_name", "")
    
    if 5 <= hour < 12:
        greeting = "早安。"
    elif 12 <= hour < 18:
        greeting = "下午好。"
    elif 18 <= hour < 22:
        greeting = "晚上好。"
    else:
        greeting = "夜深了。"
    
    if user_name:
        return f"{greeting}"
    else:
        return greeting


# ========== 音乐生成工具（Magenta RealTime 2） ==========
#def init_music_models() -> str:
    """初始化并下载 Magenta RealTime 2 模型（只需要运行一次）"""
    try:
        # 设置模型和输出目录环境变量（MAGENTA_HOME 应该包含 magenta-rt-v2 子目录）
        workspace_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace")
        env = os.environ.copy()
        env["MAGENTA_HOME"] = workspace_dir
        
        # 调用 mrt 命令行工具初始化和下载模型
        result1 = subprocess.run(
            ["mrt", "models", "init"],
            capture_output=True,
            text=True,
            timeout=300,
            env=env
        )
        result2 = subprocess.run(
            ["mrt", "models", "download"],
            capture_output=True,
            text=True,
            timeout=600,
            env=env
        )
        output = result1.stdout + result2.stdout
        if result1.stderr or result2.stderr:
            output += "\n--- stderr ---\n" + result1.stderr + result2.stderr
        return f"🎵 模型初始化完成！\n{output}"
    except Exception as e:
        import traceback
        return f"❌ 模型初始化失败：{str(e)}\n{traceback.format_exc()}"


#def generate_music(prompt: str, duration: float = 4.0, filename: str = "output_music.wav", model: str = "mrt2_small") -> str:
#    """使用 Magenta RealTime 2 生成音乐（Apple Silicon MLX 加速）"""
#    try:
#        safe_filename = os.path.basename(filename)  # 防止路径穿越
#        if not safe_filename.endswith(".wav"):
#            safe_filename += ".wav"
#        output_path = _safe_path(safe_filename)
#        
#        # 设置模型和输出目录环境变量
#        workspace_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace")
#        env = os.environ.copy()
#        env["MAGENTA_HOME"] = workspace_dir  # 关键：让输出和模型都在我们的项目目录下
#        
#        # 使用 mrt 命令行工具生成音乐
#        result = subprocess.run(
#            ["mrt", "mlx", "generate", "--prompt", prompt, "--duration", str(duration), "--model", model],
#            capture_output=True,
#            text=True,
#            timeout=600,
#            env=env
#        )
#        
#        output = result.stdout
#        if result.stderr:
#            output += "\n--- stderr ---\n" + result.stderr
#        
#        # 默认输出文件名格式
#        default_output_name = f"output_audio_mlx_{model}.wav"
#        default_output_path = os.path.join(workspace_dir, "magenta-rt-v2", "outputs", default_output_name)
#        
#        if result.returncode == 0 and os.path.exists(default_output_path):
#            # 移动/重命名文件到用户指定的文件名
#            import shutil
#            shutil.move(default_output_path, output_path)
#            return f"🎵 音乐生成成功！\n文件已保存：{safe_filename}\n{output}"
#        else:
#            return f"❌ 音乐生成失败：{output}"
#    except Exception as e:
#        import traceback
#        return f"❌ 音乐生成出错：{str(e)}\n{traceback.format_exc()}"


def concatenate_with_crossfade(waveforms, crossfade_seconds=0.3):
  """
  Concatenate multiple Waveform objects with smooth crossfade between segments.
  
  Args:
    waveforms: List of magenta_rt.audio.Waveform objects.
    crossfade_seconds: Duration of crossfade in seconds.
  
  Returns:
    Concatenated Waveform object with crossfades.
  """
  from magenta_rt import audio
  
  if not waveforms:
    raise ValueError("No waveforms to concatenate.")
  if len(waveforms) == 1:
    return waveforms[0]
  
  sample_rate = waveforms[0].sample_rate
  num_channels = waveforms[0].num_channels
  
  crossfade_samples = int(crossfade_seconds * sample_rate)
  
  result = waveforms[0].samples
  for i in range(1, len(waveforms)):
    current = waveforms[i].samples
    
    if crossfade_samples > 0:
      crossfade_len = min(crossfade_samples, result.shape[0], current.shape[0])
      
      if crossfade_len > 0:
        ramp = audio.crossfade_ramp(crossfade_len, "eqpower")
        ramp = ramp.reshape(-1, 1)
        crossfade_end = result[-crossfade_len:] * (1 - ramp)
        crossfade_start = current[:crossfade_len] * ramp
        
        middle = crossfade_end + crossfade_start
        
        result = np.concatenate([result[:-crossfade_len], middle, current[crossfade_len:]], axis=0)
      else:
        result = np.concatenate([result, current], axis=0)
    else:
      result = np.concatenate([result, current], axis=0)
  
  return audio.Waveform(result, sample_rate)


def generate_music_streaming(
  prompt: str, 
  duration: float = 16.0, 
  segment_duration: float = 4.0, 
  crossfade_duration: float = 0.3, 
  filename: str = "long_music.wav", 
  model: str = "mrt2_small"
) -> str:
  """
  Generate long-form music using Magenta RealTime 2 with streaming and crossfade.
  
  Args:
    prompt: Text prompt describing music style.
    duration: Total duration in seconds.
    segment_duration: Duration of each segment in seconds.
    crossfade_duration: Crossfade duration between segments in seconds.
    filename: Output filename.
    model: Model to use ('mrt2_small' or 'mrt2_base').
  
  Returns:
    Success or error message.
  """
  try:
    import os
    # 屏蔽 TensorFlow 和 Magenta 的日志信息
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    import logging
    logging.getLogger('tensorflow').setLevel(logging.ERROR)
    logging.getLogger('magenta_rt').setLevel(logging.ERROR)
    
    from magenta_rt import audio, paths
    from magenta_rt.mlx import system as mlx_system
    
    magenta_home = os.path.expanduser("~/Documents/Magenta")
    os.environ["MAGENTA_HOME"] = magenta_home
    
    # Initialize the model
    mrt = mlx_system.MagentaRT2SystemMlxfn(size=model)
    embedding = mrt.embed_style(prompt, use_mapper=True)
    
    # Calculate number of segments
    num_segments = max(1, int(duration / segment_duration))
    frames_per_segment = int(segment_duration * 25)
    
    # Generate segments
    segments = []
    state = None
    for i in range(num_segments):
      wav, state = mrt.generate(
        style=embedding, 
        frames=frames_per_segment, 
        state=state
      )
      segments.append(wav)
      #print(f"Generated segment {i+1}/{num_segments}")
    
    # Concatenate with crossfade
    if len(segments) == 1:
      full_wav = segments[0]
    else:
      full_wav = concatenate_with_crossfade(segments, crossfade_duration)
    
    # Save file
    safe_filename = os.path.basename(filename)
    if not safe_filename.endswith(".wav"):
      safe_filename += ".wav"
    output_path = _safe_path(safe_filename)
    full_wav.write(output_path)
    
    return f"🎵 Long-form music generated successfully!\nDuration: {full_wav.seconds:.1f}s\nSaved to: {safe_filename}"
    
  except Exception as e:
    import traceback
    return f"❌ Streaming music generation failed:\n{str(e)}\n{traceback.format_exc()}"


# ========== 音乐播放工具（pygame）==========
def _ensure_pygame_initialized():
    """确保 pygame mixer 已初始化"""
    global _pygame_initialized
    if not _pygame_initialized:
        try:
            # 屏蔽 pygame 的欢迎信息
            os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
            import pygame
            pygame.mixer.init()
            _pygame_initialized = True
        except ImportError:
            return False, "pygame not installed. Please install it with: pip install pygame"
        except Exception as e:
            return False, f"Failed to initialize pygame: {str(e)}"
    return True, None


def play_music(filename: str, loops: int = -1, volume: float = 1.0) -> str:
    """使用 pygame 播放音乐（支持 WAV、MP3、OGG 等格式）"""
    # 初始化 pygame
    ok, err = _ensure_pygame_initialized()
    if not ok:
        return f"❌ {err}"
    
    try:
        import pygame
        
        # 安全路径检查
        audio_path = _safe_path(filename)
        if not os.path.exists(audio_path):
            return f"❌ 文件不存在：{filename}"
        
        # 加载并播放音乐
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        pygame.mixer.music.play(loops=loops)
        
        return f"🎵 正在播放：{filename} (loops={loops}, volume={volume:.2f})"
    except Exception as e:
        import traceback
        return f"❌ 播放失败：{str(e)}\n{traceback.format_exc()}"


def pause_music() -> str:
    """暂停当前播放的音乐"""
    ok, err = _ensure_pygame_initialized()
    if not ok:
        return f"❌ {err}"
    
    try:
        import pygame
        pygame.mixer.music.pause()
        return "⏸️ 音乐已暂停"
    except Exception as e:
        return f"❌ 暂停失败：{str(e)}"


def unpause_music() -> str:
    """继续播放暂停的音乐"""
    ok, err = _ensure_pygame_initialized()
    if not ok:
        return f"❌ {err}"
    
    try:
        import pygame
        pygame.mixer.music.unpause()
        return "▶️ 音乐已继续"
    except Exception as e:
        return f"❌ 继续播放失败：{str(e)}"


def stop_music() -> str:
    """停止音乐播放"""
    ok, err = _ensure_pygame_initialized()
    if not ok:
        return f"❌ {err}"
    
    try:
        import pygame
        pygame.mixer.music.stop()
        return "⏹️ 音乐已停止"
    except Exception as e:
        return f"❌ 停止失败：{str(e)}"


def set_music_volume(volume: float) -> str:
    """设置音乐播放音量"""
    ok, err = _ensure_pygame_initialized()
    if not ok:
        return f"❌ {err}"
    
    try:
        import pygame
        # 确保音量在 0.0 到 1.0 之间
        clamped_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(clamped_volume)
        return f"🔊 音量已设置为：{clamped_volume:.2f}"
    except Exception as e:
        return f"❌ 设置音量失败：{str(e)}"


# 函数映射表：函数名 -&gt; 函数对象（供动态调用）
FUNCTIONS = {
    "write_file": write_file,
    "read_file": read_file,
    "run_python": run_python,
    "save_memory": save_memory,
    "get_memory": get_memory,
    "daily_greeting": daily_greeting,
    "add_reminder": add_reminder,
    "list_reminders": list_reminders,
    "initialize_character": initialize_character,
    "introduce_myself": introduce_myself,
    #"generate_music": generate_music,
    "generate_music_streaming": generate_music_streaming,
    #"init_music_models": init_music_models,
    "play_music": play_music,
    "pause_music": pause_music,
    "unpause_music": unpause_music,
    "stop_music": stop_music,
    "set_music_volume": set_music_volume,
}