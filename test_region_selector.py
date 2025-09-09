#!/usr/bin/env python3
"""测试区域选择器的脚本"""

import sys
import os
import tempfile
import json
from region_selector import RegionSelector

def create_test_layout_file():
    """创建测试用的布局文件"""
    layout = [
        ['1', '2', '3', '4', '5'],
        ['q', 'w', 'e', 'r', 't'],
        ['a', 's', 'd', 'f', 'g'],
        ['z', 'x', 'c', 'v', 'b']
    ]
    
    temp_dir = tempfile.gettempdir()
    layout_file = os.path.join(temp_dir, "test_layout.tmp")
    coords_file = os.path.join(temp_dir, "test_coords.tmp")
    
    with open(layout_file, 'w', encoding='utf-8') as f:
        json.dump(layout, f)
    
    print(f"布局文件创建于: {layout_file}")
    print(f"坐标文件将输出到: {coords_file}")
    
    return layout_file, coords_file

def main():
    print("开始测试区域选择器...")
    
    # 创建测试文件
    layout_file, coords_file = create_test_layout_file()
    
    try:
        # 启动区域选择器
        app = RegionSelector(
            [
                ['1', '2', '3', '4', '5'],
                ['q', 'w', 'e', 'r', 't'],
                ['a', 's', 'd', 'f', 'g'],
                ['z', 'x', 'c', 'v', 'b']
            ],
            coords_file
        )
        
        print("区域选择器已启动。按任意布局上的键来选择区域...")
        print("第一级：选择大区域（数字1-5或字母q-t等）")
        print("第二级：选择精确位置")
        print("按ESC或点击空白区域退出")
        
        app.mainloop()
        
        # 检查结果
        if os.path.exists(coords_file):
            with open(coords_file, 'r', encoding='utf-8') as f:
                coords = f.read().strip()
            if coords:
                print(f"选择的坐标: {coords}")
            else:
                print("没有选择任何坐标")
            os.remove(coords_file)
        else:
            print("没有生成坐标文件")
            
    finally:
        # 清理
        if os.path.exists(layout_file):
            os.remove(layout_file)

if __name__ == "__main__":
    main()