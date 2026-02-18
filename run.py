"""
快速启动入口

使用方式:
    python run.py                           # 默认受众: fba_beginner
    python run.py --audience fba_operator   # 指定受众
    python run.py --audience all            # 所有受众
    python run.py --dry-run                 # 只抓取聚类，不生成内容
    python run.py -a ppc_specialist -f short_video,image_prompt
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()
