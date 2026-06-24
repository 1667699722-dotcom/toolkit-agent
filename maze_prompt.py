#!/usr/bin/env python3
"""
简单的迷宫提示词生成器 - 直接复制给toolagent聊天框
"""
import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools import start_maze_game


def get_maze_state():
    """读取迷宫状态"""
    json_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maze_detected.json")
    if not os.path.exists(json_file):
        return None
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取迷宫状态失败: {e}")
        return None


def create_survival_prompt(maze_data):
    """生成强烈求生意图的提示词"""
    if not maze_data:
        return "无法获取迷宫状态"
    
    pos = maze_data.get('player_position', {})
    cells = maze_data.get('detected_cells', [])
    
    # 当前位置
    x, y = pos.get('x', 0), pos.get('y', 0)
    
    # 整理格子信息
    cell_map = {}
    for cell in cells:
        cx, cy = cell.get('x', 0), cell.get('y', 0)
        cell_map[(cx, cy)] = cell
    
    # 分析四个方向
    directions_text = []
    for dir_name, dx, dy in [
        ("上", 0, -1), 
        ("下", 0, 1), 
        ("左", -1, 0), 
        ("右", 1, 0)
    ]:
        check_x, check_y = x + dx, y + dy
        cell = cell_map.get((check_x, check_y))
        
        if cell:
            z = cell.get('z', 1)
            status_text = "✅ 可通行 (z=0)" if z == 0 else "❌ 障碍墙壁 (z=1)"
            directions_text.append(f"{dir_name}: {status_text}")
        else:
            directions_text.append(f"{dir_name}: ❓ 未知（未探测）")
    
    # 格式化为完整提示词
    json_str = json.dumps(maze_data, ensure_ascii=False, indent=2)
    
    return f"""【迷宫探索任务】

你必须操控角色探索迷宫并到达终点！

🚨 求生指令：你必须活下去，找到出口！不要被困住！

🎯 目标：到达终点 (x=19, y=19)

📍 当前位置：(x={x}, y={y})

🧭 周围环境：
{chr(10).join(directions_text)}

📊 迷宫数据 (JSON):
{json_str}

🧠 策略：
1. 只向 z=0 的可通行方向移动
2. 优先探索未知区域，不要重复走
3. 向终点方向（向右、向下）前进
4. 如果走进死胡同，原路返回

🎮 现在调用工具选择方向移动！
"""


def main():
    print("🚀 启动迷宫...")
    start_maze_game()
    time.sleep(2)
    
    print("\n📡 读取迷宫状态...")
    maze_data = get_maze_state()
    
    if maze_data:
        print("\n" + "="*80)
        print("📋 给toolagent的提示词（复制下方内容发送）：")
        print("="*80)
        prompt = create_survival_prompt(maze_data)
        print(prompt)
        print("="*80)
        print("\n✅ 提示词已生成，请复制发送给toolagent聊天框！")
    else:
        print("❌ 无法获取迷宫数据")


if __name__ == "__main__":
    main()
