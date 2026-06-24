#!/usr/bin/env python3
"""
迷宫游戏API使用示例 - 简化版
"""

import time
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from maze_game import (
    init_game,
    move_up,
    move_down,
    move_left,
    move_right,
    save_json,
    exit_game
)

def ai_control():
    """AI控制示例"""
    time.sleep(1.5)
    
    print("向右移动...")
    move_right()
    time.sleep(0.5)
    
    print("向下移动...")
    move_down()
    time.sleep(0.5)
    
    print("向右移动...")
    move_right()
    time.sleep(0.5)
    
    print("保存数据...")
    save_json()
    print("数据已保存")
    
    time.sleep(2)
    
    print("退出游戏...")
    exit_game()

def main():
    print("=== 迷宫游戏API ===")
    print()
    print("可用API函数：")
    print("  init_game()    - 初始化并运行游戏（阻塞调用）")
    print("  move_up()      - 向上移动")
    print("  move_down()    - 向下移动")
    print("  move_left()    - 向左移动")
    print("  move_right()   - 向右移动")
    print("  save_json()    - 保存数据到JSON")
    print("  exit_game()    - 退出游戏")
    print()
    
    print("说明：")
    print("  - 必须先在主线程调用 init_game()")
    print("  - 其他控制函数可以在另一个线程中调用")
    print()
    
    print("运行示例...")
    print()
    
    # 在另一个线程中运行AI控制
    control_thread = threading.Thread(target=ai_control)
    control_thread.daemon = True
    control_thread.start()
    
    # 在主线程中运行游戏
    init_game()

if __name__ == "__main__":
    main()
