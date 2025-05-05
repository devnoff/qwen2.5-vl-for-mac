#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import base64
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'mlx_api_server.log'))
    ]
)
logger = logging.getLogger(__name__)

# 필요한 라이브러리 임포트 체크
required_libs = ["fastapi", "PIL", "uvicorn", "transformers"]
missing_libs = []

for lib in required_libs:
    try:
        __import__(lib)
    except ImportError:
        missing_libs.append(lib)
        logger.error(f"필수 라이브러리 {lib}가 설치되어 있지 않습니다.")

# MLX 라이브러리 체크
mlx_installed = True
try:
    import mlx.core
    import mlx.nn
except ImportError:
    mlx_installed = False
    logger.error("MLX 라이브러리가 설치되어 있지 않습니다. 실행 전 MLX를 설치하세요.")
    logger.error("설치 명령어: pip install mlx")
    missing_libs.append("mlx")

if missing_libs:
    logger.error(f"다음 라이브러리가 설치되어 있지 않습니다: {', '.join(missing_libs)}")
    logger.error("설치 명령어: pip install " + " ".join(missing_libs))
    sys.exit(1)

# 라이브러리 정상적으로 로드된 경우
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from PIL import Image
from fastapi.responses import JSONResponse

# 스크립트 실행 경로 계산
script_path = Path(__file__).resolve().parent
project_root = script_path.parent
MLX_MODELS_DIR = project_root / "models" / "mlx_models"

# MLX 모델 목록 (가용한 모델)
AVAILABLE_MODELS = {
    "Qwen-2.5-VL-3B-mlx": str(MLX_MODELS_DIR / "Qwen-2.5-VL-3B"),
    "qwen-2.5-vl-7b-mlx": str(MLX_MODELS_DIR / "qwen-2.5-vl-7b"),
    "qwen-2.5-vl-32b-mlx": str(MLX_MODELS_DIR / "qwen-2.5-vl-32b")
}

logger.info(f"모델 디렉토리: {MLX_MODELS_DIR}")
logger.info(f"가용한 모델: {list(AVAILABLE_MODELS.keys())}")

# 모델 체크
available_model_list = []
for model_name, model_path in AVAILABLE_MODELS.items():
    if os.path.exists(model_path):
        available_model_list.append(model_name)
        logger.info(f"모델 확인됨: {model_name} at {model_path}")
    else:
        logger.warning(f"모델을 찾을 수 없음: {model_name} at {model_path}")

if not available_model_list:
    logger.error("사용 가능한 모델이 없습니다! 먼저 모델을 다운로드하고 MLX 형식으로 변환하세요.")
    logger.error("./download_model.sh 및 ./convert_to_mlx.sh 스크립트를 실행하세요.")

# 기본 모델 설정
DEFAULT_MODEL = available_model_list[0] if available_model_list else None
CURRENT_MODEL = None
MODEL_INSTANCE = None

# 서버 시작 시 모델 로드 (기본 모델 또는 첫 번째 사용 가능한 모델)
def load_model(model_name):
    global CURRENT_MODEL, MODEL_INSTANCE
    
    if model_name not in AVAILABLE_MODELS:
        raise ValueError(f"요청된 모델 '{model_name}'는 지원되지 않습니다. 지원되는 모델: {list(AVAILABLE_MODELS.keys())}")
    
    model_path = AVAILABLE_MODELS[model_name]
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"모델 경로를 찾을 수 없습니다: {model_path}")

    try:
        logger.info(f"모델 '{model_name}' 로드 중...")
        # MLX를 사용하여 모델 로드 (MLX 설치에만 사용 가능)
        from transformers import AutoProcessor, TextStreamer
        from mlx_lm.utils import get_model

        processor = AutoProcessor.from_pretrained(model_path)
        model = get_model(model_path)
        
        MODEL_INSTANCE = {
            "model": model,
            "processor": processor,
            "streamer": TextStreamer(processor.tokenizer)
        }
        CURRENT_MODEL = model_name
        logger.info(f"모델 '{model_name}' 로드 완료")
        return True
    except Exception as e:
        logger.error(f"모델 로드 실패: {str(e)}")
        raise e

# API 서버 설정
app = FastAPI(title="Qwen-2.5-VL MLX API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 모델 
class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512

class ModelsResponse(BaseModel):
    data: List[Dict[str, str]]

# 루트 경로
@app.get("/")
async def root():
    return {
        "name": "Qwen-2.5-VL MLX API",
        "version": "1.0.0",
        "description": "Apple Silicon M4 Pro에서 실행되는 Qwen-2.5-VL MLX API",
        "models": available_model_list
    }

# 모델 목록 엔드포인트 (OpenAI 호환)
@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    models_data = []
    for model_name in available_model_list:
        models_data.append({
            "id": model_name,
            "object": "model",
            "created": 0,
            "owned_by": "user"
        })
    
    return {"data": models_data}

# 채팅 완성 엔드포인트 (OpenAI 호환)
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    try:
        if not mlx_installed:
            return JSONResponse(
                status_code=500,
                content={"error": "MLX 라이브러리가 설치되어 있지 않습니다. setup_environment.sh를 실행하여 설치하세요."}
            )
            
        if not available_model_list:
            return JSONResponse(
                status_code=500,
                content={"error": "사용 가능한 모델이 없습니다. download_model.sh 및 convert_to_mlx.sh 스크립트를 실행하세요."}
            )
        
        # 모델이 로드되어 있는지 확인하고, 필요하면 로드
        if CURRENT_MODEL != request.model and request.model in available_model_list:
            load_model(request.model)
        elif CURRENT_MODEL is None and DEFAULT_MODEL:
            load_model(DEFAULT_MODEL)
        elif CURRENT_MODEL is None:
            return JSONResponse(
                status_code=500,
                content={"error": "모델이 로드되지 않았습니다. 사용 가능한 모델이 없습니다."}
            )
        
        # 메시지 준비
        messages = request.messages
        
        # 이미지가 있는지 확인
        images = []
        prompt = ""
        
        for msg in messages:
            if msg["role"] == "user":
                content = msg["content"]
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "image_url":
                            image_url = item.get("image_url", {})
                            if isinstance(image_url, dict) and "url" in image_url:
                                # base64 이미지 처리
                                img_data = image_url["url"]
                                if img_data.startswith("data:image/"):
                                    base64_data = img_data.split(",")[1]
                                    img_bytes = base64.b64decode(base64_data)
                                    import io
                                    img = Image.open(io.BytesIO(img_bytes))
                                    images.append(img)
                        elif isinstance(item, dict) and item.get("type") == "text":
                            prompt += item.get("text", "")
                else:
                    prompt += content
            # 다른 역할의 메시지 처리
            elif msg["role"] in ["system", "assistant"]:
                if prompt:
                    prompt += "\n"
                prompt += f"{msg['role'].upper()}: {msg['content']}\n"
        
        if prompt:
            prompt += "\nASSISTANT: "
        
        # 모델 추론 실행
        processor = MODEL_INSTANCE["processor"]
        model = MODEL_INSTANCE["model"]
        
        # 이미지가 있는 경우와 없는 경우 처리 구분
        if images:
            inputs = processor(text=prompt, images=images, return_tensors="np")
        else:
            inputs = processor(text=prompt, return_tensors="np")
        
        # 온도와 최대 토큰 설정
        generation_args = {
            "max_new_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        # 모델 추론
        logger.info(f"모델 추론 시작: max_tokens={request.max_tokens}, temperature={request.temperature}")
        outputs = model.generate(**inputs, **generation_args)
        generated_text = processor.batch_decode(outputs, skip_special_tokens=True)[0]
        
        # 프롬프트 제거
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):]
        
        logger.info(f"생성된 텍스트 길이: {len(generated_text)}")
        
        # OpenAI API 호환 응답 형식
        response = {
            "id": f"chatcmpl-{hash(prompt)}",
            "object": "chat.completion",
            "created": 0,
            "model": CURRENT_MODEL,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": generated_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt),
                "completion_tokens": len(generated_text),
                "total_tokens": len(prompt) + len(generated_text)
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"채팅 완성 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# 이미지 업로드 처리 엔드포인트
@app.post("/v1/uploads")
async def upload_image(file: UploadFile = File(...)):
    try:
        # 임시 파일 저장 및 PIL로 이미지 열기
        img_content = await file.read()
        import io
        img = Image.open(io.BytesIO(img_content))
        
        # base64 인코딩
        buffered = io.BytesIO()
        img.save(buffered, format=img.format if img.format else "JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return {
            "url": f"data:image/{img.format.lower() if img.format else 'jpeg'};base64,{img_str}",
            "file_id": file.filename
        }
    except Exception as e:
        logger.error(f"이미지 업로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 서버 실행 함수
def start_server(host="0.0.0.0", port=8000):
    # 시작 시 모델 로드 시도
    if DEFAULT_MODEL and mlx_installed:
        try:
            load_model(DEFAULT_MODEL)
        except Exception as e:
            logger.error(f"기본 모델 로드 실패: {str(e)}")
            logger.warning("API는 작동하지만 모델은 요청 시 로드됩니다.")
    
    logger.info(f"MLX API 서버 시작 - http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server() 