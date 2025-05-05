try:
    import torch
    import mlx.core
    from fastapi import FastAPI
    from pydantic import BaseModel
    from transformers import AutoTokenizer
    from PIL import Image
    
    # 모든 라이브러리가 성공적으로 임포트되었음
    print("SUCCESS: 모든 라이브러리가 성공적으로 임포트되었습니다.")
    exit(0)
except ImportError as e:
    print(f"ERROR: 라이브러리 임포트 실패: {e}")
    exit(1)
