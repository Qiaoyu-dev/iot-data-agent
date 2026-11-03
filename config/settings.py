# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()  # 从 .env 读入环境变量

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")