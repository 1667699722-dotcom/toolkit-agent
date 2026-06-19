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
            "name": "add",
            "description": "Add two or more numbers together. Takes an array of numbers and returns their sum. Use this instead of calling add(a,b) repeatedly — one call with an array [1,2,3,4] is enough.",
            "parameters": {
                "type": "object",
                "properties": {
                    "arr": {
                        "type": "array",
                        "description": "Array of numbers to add together, e.g. [1, 2, 3] or [3.14, 2.71, 1.41]",
                        "items": {"type": "number"}
                    }
                },
                "required": ["arr"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sub",
            "description": "Subtract two numbers (a minus b)",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "The first number (minuend)"},
                    "b": {"type": "integer", "description": "The second number (subtrahend)"}
                },
                "required": ["a", "b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mul",
            "description": "Multiply two numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "The first number"},
                    "b": {"type": "integer", "description": "The second number"}
                },
                "required": ["a", "b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "div",
            "description": "Divide two numbers (a divided by b)",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "The dividend"},
                    "b": {"type": "number", "description": "The divisor (cannot be zero)"}
                },
                "required": ["a", "b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sqrt",
            "description": "Calculate the square root of a number",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "The number to square root"}
                },
                "required": ["a"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pow",
            "description": "Calculate a number raised to the power of another number",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "The base number"},
                    "b": {"type": "number", "description": "The exponent"}
                },
                "required": ["a", "b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log",
            "description": "Calculate the logarithm of a number",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "The number to log"}
                },
                "required": ["a"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sort_array",
            "description": "Sort an array of numbers in ascending or descending order. Returns the sorted array.",
            "parameters": {
                "type": "object",
                "properties": {
                    "arr": {
                        "type": "array",
                        "description": "The array of numbers to sort",
                        "items": {"type": "number"}
                    },
                    "descending": {
                        "type": "boolean",
                        "description": "If true, sort from largest to smallest. Default is false (ascending)."
                    }
                },
                "required": ["arr"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hash_string",
            "description": "Calculate hash of a string. Supports md5, sha1, sha256, sha512 (default is sha256).",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The string to hash"
                    },
                    "algorithm": {
                        "type": "string",
                        "description": "Hash algorithm to use (md5, sha1, sha256, sha512). Default: sha256",
                        "enum": ["md5", "sha1", "sha256", "sha512"]
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the workspace directory. If the file exists, it will be overwritten. Use this to save data, notes, or Python scripts. IMPORTANT: When writing Python code can import reusable functions from tools via 'from tools import <function_name>'. Pick appropriate functions from tools.FUNCTIONS — e.g. add, sub, mul, div, sqrt, pow, log, sort_array, write_file, read_file, run_python. Reuse them instead of reimplementing.",
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
    }
]


# ========== 工具实现 ==========
def add(arr: list) -> float:
    """Add two or more numbers together. Takes an array and returns their sum."""
    total = 0
    for x in arr:
        total += x
    return total

def sub(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b

def mul(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

def div(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        return "Error: division by zero"
    return a / b

def sqrt(a: float) -> float:
    """Calculate the square root of a number."""
    return math.sqrt(a)

def pow(a: float, b: float) -> float:
    """Calculate a number to the power of another number."""
    return a ** b

def log(a: float) -> float:
    """Calculate the natural logarithm of a number."""
    return math.log(a)

def sort_array(arr: list, descending: bool = False) -> list:
    """Sort an array of numbers in ascending (default) or descending order."""
    return sorted(arr, reverse=descending)

def hash_string(text: str, algorithm: str = "sha256") -> str:
    """Calculate hash of a string."""
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(text.encode("utf-8"))
    return hash_obj.hexdigest()

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


# 函数映射表：函数名 -> 函数对象（供动态调用）
FUNCTIONS = {
    "add": add,
    "sub": sub,
    "mul": mul,
    "div": div,
    "sqrt": sqrt,
    "pow": pow,
    "log": log,
    "sort_array": sort_array,
    "hash_string": hash_string,
    "write_file": write_file,
    "read_file": read_file,
    "run_python": run_python,
}