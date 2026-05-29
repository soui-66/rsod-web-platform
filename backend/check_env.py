import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print(f"DATABASE_URL from env: {os.getenv('DATABASE_URL')}")
