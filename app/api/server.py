#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import uuid
import json
import logging
import traceback
from typing import List, Dict, Any, Optional, Union
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn

# 모델 및 유틸리티 임포트
# MLX-VLM 임포트 - simple_openai_api_server.py 방식으로 변경
try:
    from mlx_vlm import load as load_vlm
    from mlx_vlm import generate
    from mlx_vlm.prompt_utils import apply_chat_template
    try:
        from mlx_vlm.utils import load_config
    except ImportError:
        load_config = None
    
    HAS_GENERATE = True
    logger = logging.getLogger(__name__)
    logger.info("mlx_vlm 패키지가 generate 기능과 함께 로드되었습니다.")
except ImportError:
    from mlx_vlm import load as load_vlm
    HAS_GENERATE = False
    load_config = None
    logger = logging.getLogger(__name__)
    logger.warning("mlx_vlm 패키지가 generate 기능 없이 로드되었습니다.")

from app.api.models import (
    ChatMessage, 
    ChatCompletionRequest, 
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ModelList
)
from app.utils.image_utils import process_image_from_data_url, create_empty_image

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 전역 변수
MODEL = None
PROCESSOR = None
MODEL_ID = None
MODEL_DIR = os.environ.get("MODEL_DIR", os.path.join(os.getcwd(), "models"))

# FastAPI 앱 생성
app = FastAPI(title="Qwen-VL OpenAI Compatible API Server")

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def load_model_func():
    """모델과 프로세서를 로드하는 함수"""
    global MODEL, PROCESSOR, MODEL_ID
    
    # 모델 디렉토리 확인
    if not os.path.exists(MODEL_DIR):
        logger.error(f"모델 디렉토리가 존재하지 않습니다: {MODEL_DIR}")
        raise FileNotFoundError(f"모델 디렉토리가 존재하지 않습니다: {MODEL_DIR}")
    
    try:
        # MODEL_ID가 환경 변수로 설정된 경우
        model_id = os.environ.get("MODEL_ID", None)
        if model_id:
            MODEL_ID = model_id
            
            # 먼저 모델 디렉토리 내에서 직접 확인
            model_path = os.path.join(MODEL_DIR, MODEL_ID)
            
            # 모델 경로가 존재하지 않으면 mlx_models 디렉토리 내에서 확인
            if not os.path.exists(model_path):
                mlx_models_dir = os.path.join(MODEL_DIR, "mlx_models")
                if os.path.exists(mlx_models_dir):
                    model_path = os.path.join(mlx_models_dir, MODEL_ID)
                    logger.info(f"mlx_models 디렉토리에서 모델 확인: {model_path}")
            
            # 그래도 모델 경로가 존재하지 않으면 대체 모델 찾기
            if not os.path.exists(model_path):
                logger.warning(f"지정된 모델 경로가 존재하지 않습니다: {model_path}")
                
                # 먼저 mlx_models 디렉토리에서 찾기
                mlx_models_dir = os.path.join(MODEL_DIR, "mlx_models")
                if os.path.exists(mlx_models_dir):
                    mlx_models = [d for d in os.listdir(mlx_models_dir) 
                                if os.path.isdir(os.path.join(mlx_models_dir, d)) and d.endswith("-mlx")]
                    
                    if mlx_models:
                        MODEL_ID = mlx_models[0]  # 첫 번째 발견된 모델 사용
                        model_path = os.path.join(mlx_models_dir, MODEL_ID)
                        logger.info(f"mlx_models 디렉토리에서 대체 모델을 찾았습니다: {MODEL_ID}")
                        logger.info(f"대체 모델 경로: {model_path}")
                        
                # mlx_models에서 찾지 못한 경우 모델 디렉토리 전체에서 검색
                if not os.path.exists(model_path):
                    # 사용 가능한 모델 디렉토리 찾기
                    models = [d for d in os.listdir(MODEL_DIR) 
                             if os.path.isdir(os.path.join(MODEL_DIR, d)) and d.endswith("-mlx")]
                    
                    if models:
                        MODEL_ID = models[0]  # 첫 번째 발견된 모델 사용
                        model_path = os.path.join(MODEL_DIR, MODEL_ID)
                        logger.info(f"대체 모델을 사용합니다: {MODEL_ID}")
                    else:
                        logger.error(f"사용 가능한 모델이 없습니다.")
                        raise FileNotFoundError("사용 가능한 모델이 없습니다.")
        else:
            # 모델 ID가 지정되지 않은 경우 자동 검색
            logger.info("모델 ID가 지정되지 않았습니다. 자동으로 모델을 검색합니다.")
            
            # 먼저 mlx_models 디렉토리에서 검색
            mlx_models_dir = os.path.join(MODEL_DIR, "mlx_models")
            if os.path.exists(mlx_models_dir):
                mlx_models = [d for d in os.listdir(mlx_models_dir) 
                            if os.path.isdir(os.path.join(mlx_models_dir, d)) and d.endswith("-mlx")]
                
                if mlx_models:
                    MODEL_ID = mlx_models[0]  # 첫 번째 발견된 모델 사용
                    model_path = os.path.join(mlx_models_dir, MODEL_ID)
                    logger.info(f"mlx_models 디렉토리에서 모델을 찾았습니다: {MODEL_ID}")
                    logger.info(f"모델 경로: {model_path}")
            
            # mlx_models에서 찾지 못한 경우
            if not MODEL_ID:
                # 사용 가능한 모델 디렉토리 찾기
                models = [d for d in os.listdir(MODEL_DIR) 
                         if os.path.isdir(os.path.join(MODEL_DIR, d)) and d.endswith("-mlx")]
                
                if models:
                    MODEL_ID = models[0]  # 첫 번째 발견된 모델 사용
                    model_path = os.path.join(MODEL_DIR, MODEL_ID)
                    logger.info(f"첫 번째 발견된 모델을 사용합니다: {MODEL_ID}")
                else:
                    logger.error(f"사용 가능한 모델이 없습니다.")
                    raise FileNotFoundError("사용 가능한 모델이 없습니다.")
        
        # 절대 경로로 변환
        abs_model_path = os.path.abspath(model_path)
        logger.info(f"절대 경로: {abs_model_path}")
        
        # Python 환경 정보 출력
        logger.info(f"Python 실행 경로: {sys.executable}")
        logger.info(f"Python 버전: {sys.version}")
        logger.info(f"작업 디렉토리: {os.getcwd()}")
        
        # 모델 디렉토리 확인
        if os.path.isdir(abs_model_path):
            logger.info(f"모델 디렉토리 존재함: {abs_model_path}")
            # 디렉토리 내용 확인
            try:
                files = os.listdir(abs_model_path)
                logger.info(f"디렉토리 파일: {files[:10]} ..." if len(files) > 10 else f"디렉토리 파일: {files}")
            except Exception as e:
                logger.warning(f"디렉토리 내용 확인 실패: {e}")
        else:
            logger.warning(f"모델 경로가 디렉토리가 아님: {abs_model_path}")
        
        # 모델 로드
        logger.info(f"모델 로드 중: {abs_model_path}")
        
        try:
            # MLX-VLM 패키지 버전 확인
            try:
                import pkg_resources
                mlx_vlm_version = pkg_resources.get_distribution("mlx-vlm").version
                logger.info(f"MLX-VLM 버전: {mlx_vlm_version}")
            except Exception as e:
                logger.warning(f"MLX-VLM 버전 확인 실패: {e}")
            
            result = load_vlm(abs_model_path)
            
            if not isinstance(result, tuple) or len(result) < 2:
                logger.error(f"모델 로드 실패: 예상한 튜플이 아닙니다. 반환 타입: {type(result)}")
                raise ValueError(f"모델 로드 오류: 예상 타입이 아닙니다.")
            
            MODEL, PROCESSOR = result
            logger.info(f"모델 로드 완료: {MODEL_ID}")
            logger.info(f"모델 타입: {type(MODEL)}")
            logger.info(f"프로세서 타입: {type(PROCESSOR)}")
            
            if MODEL is None or PROCESSOR is None:
                logger.error("모델 또는 프로세서가 None입니다.")
                raise ValueError("모델 또는 프로세서가 None입니다.")
            
            # 모델 로드 성공
            logger.info("모델과 프로세서가 성공적으로 로드되었습니다.")
            return True
        
        except Exception as e:
            logger.error(f"모델 로드 오류: {e}")
            logger.error(traceback.format_exc())
            raise
        
    except Exception as e:
        logger.error(f"모델 로드 중 오류 발생: {e}")
        logger.error(traceback.format_exc())
        raise

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 이벤트 핸들러"""
    global MODEL_ID
    
    try:
        logger.info("서버 시작: 모델 로드 중...")
        await load_model_func()
        logger.info(f"서버 준비 완료. 모델 ID: {MODEL_ID}")
    except Exception as e:
        logger.error(f"서버 시작 오류: {e}")
        logger.error(traceback.format_exc())

@app.get("/", response_class=JSONResponse)
async def root():
    """루트 엔드포인트 - 서버 상태 확인"""
    return {"status": "online", "model": MODEL_ID or "로드되지 않음"}

@app.get("/v1/models", response_model=ModelList, response_class=JSONResponse)
async def list_models():
    """OpenAI API와 호환되는 모델 목록 엔드포인트"""
    global MODEL_ID
    
    if not MODEL_ID:
        try:
            await load_model_func()
        except Exception as e:
            logger.error(f"모델 로드 오류: {e}")
            raise HTTPException(status_code=500, detail=f"모델 로드 오류: {str(e)}")
    
    try:
        # 모델 정보 구성
        models_data = []
        models_data.append({
            "id": MODEL_ID,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "user"
        })
        
        return {"object": "list", "data": models_data}
    except Exception as e:
        logger.error(f"모델 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"모델 목록 조회 오류: {str(e)}")

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse, response_class=JSONResponse)
async def chat_completions(request: ChatCompletionRequest, raw_request: Request):
    """OpenAI API와 호환되는 채팅 완료 엔드포인트"""
    global MODEL, PROCESSOR, MODEL_ID
    
    logger.info(f"채팅 완료 요청. 모델: {request.model}, 메시지 수: {len(request.messages)}, 스트림: {request.stream}")
    
    try:
        if not MODEL or not PROCESSOR:
            logger.info("모델이 로드되지 않았습니다. 로드를 시도합니다.")
            await load_model_func()
        
        # 사용자 메시지 추출
        last_user_msg = None
        
        for msg in reversed(request.messages):
            if msg.role == "user":
                last_user_msg = msg
                break
        
        if not last_user_msg:
            raise HTTPException(status_code=400, detail="사용자 메시지가 없습니다")
        
        # 이미지 처리 로직
        img = None
        text_prompt = ""
        
        # 메시지 형식에 따라 처리
        if isinstance(last_user_msg.content, list):
            for content_item in last_user_msg.content:
                if isinstance(content_item, dict):
                    if content_item.get("type") == "text":
                        text_prompt += content_item.get("text", "")
                    elif content_item.get("type") == "image_url":
                        image_url = content_item.get("image_url", {}).get("url", "")
                        if image_url:
                            logger.info(f"이미지 URL 처리 중: {image_url[:100]}...")
                            try:
                                img = process_image_from_data_url(image_url)
                                if img is None:
                                    logger.warning("이미지 처리 실패, 빈 이미지 생성")
                                    img = create_empty_image()
                            except Exception as img_err:
                                logger.error(f"이미지 처리 오류: {img_err}")
                                img = create_empty_image()
                else:
                    text_prompt += str(content_item)
        else:
            text_prompt = last_user_msg.content
        
        # 모델을 통한 텍스트 생성
        logger.info(f"프롬프트: {text_prompt[:100]}{'...' if len(text_prompt) > 100 else ''}")
        
        # 스트리밍 모드 처리
        if request.stream:
            logger.info("스트리밍 모드로 응답 생성")
            
            async def generate_stream():
                # 필요한 헤더와 함께 응답 시작 부분 생성
                completion_id = f"chatcmpl-{str(uuid.uuid4())}"
                created = int(time.time())
                
                try:
                    # 시스템 프롬프트 처리
                    system_prompt = None
                    for msg in request.messages:
                        if isinstance(msg, dict) and msg.get("role") == "system":
                            system_prompt = msg.get("content")
                            break
                        elif hasattr(msg, "role") and msg.role == "system":
                            system_prompt = msg.content
                            break
                    
                    # 설정 로드 시도
                    config = None
                    if load_config:
                        try:
                            # Qwen 모델 설정 파일 로드
                            abs_model_path = os.path.abspath(os.path.join(MODEL_DIR, "mlx_models", MODEL_ID))
                            config = load_config(abs_model_path)
                        except Exception as e:
                            logger.warning(f"모델 설정 로드 실패: {e}")
                            config = {"chat_template": "simple"}
                    else:
                        config = {"chat_template": "simple"}
                    
                    # 포맷된 프롬프트 생성
                    try:
                        formatted_prompt = apply_chat_template(
                            PROCESSOR, 
                            config, 
                            text_prompt, 
                            system=system_prompt, 
                            num_images=1 if img is not None else 0
                        )
                    except Exception as e:
                        logger.warning(f"포맷된 프롬프트 생성 실패: {e}, 원본 프롬프트 사용")
                        formatted_prompt = text_prompt
                    
                    logger.info(f"스트리밍 포맷된 프롬프트: {formatted_prompt[:100]}..." if len(formatted_prompt) > 100 else f"포맷된 프롬프트: {formatted_prompt}")
                    
                    # 전체 텍스트를 한 번에 생성
                    try:
                        logger.info("전체 텍스트 생성 시작...")
                        start_time = time.time()
                        
                        if img is not None:
                            response_text = generate(
                                MODEL, 
                                PROCESSOR, 
                                formatted_prompt, 
                                [img],
                                max_tokens=request.max_tokens,
                                temperature=request.temperature,
                                top_p=request.top_p if hasattr(request, 'top_p') and request.top_p is not None else 0.95,
                                verbose=False
                            )
                        else:
                            response_text = generate(
                                MODEL, 
                                PROCESSOR, 
                                formatted_prompt,
                                max_tokens=request.max_tokens,
                                temperature=request.temperature,
                                top_p=request.top_p if hasattr(request, 'top_p') and request.top_p is not None else 0.95,
                                verbose=False
                            )
                        
                        # 리스트 반환값 처리
                        if isinstance(response_text, list) and len(response_text) > 0:
                            response_text = response_text[0]
                        
                        end_time = time.time()
                        logger.info(f"전체 텍스트 생성 완료: {end_time - start_time:.2f}초")
                        logger.info(f"생성된 텍스트 길이: {len(response_text)} 문자, {len(response_text.split())} 토큰")
                        logger.info(f"응답: {response_text[:100]}..." if len(response_text) > 100 else f"응답: {response_text}")
                        
                        # 계속 질문 추가 여부 확인
                        tokens_used = len(response_text.split())
                        add_continue_question = tokens_used >= int(request.max_tokens * 0.8)
                        
                        if add_continue_question:
                            # 문장 끝 찾기
                            last_sentence_end = max(
                                response_text.rfind('.'), 
                                response_text.rfind('!'), 
                                response_text.rfind('?')
                            )
                            
                            # 적절한 위치에 질문 추가
                            if last_sentence_end > 0 and last_sentence_end < len(response_text) - 10:
                                # 문장 끝 다음부터의 텍스트 제거
                                response_text = response_text[:last_sentence_end+1]
                                response_text += "\n\n계속해서 더 들려드릴까요?"
                                logger.info("계속 질문이 추가됨")
                        
                        # 첫 글자에 role 추가
                        if response_text:
                            # 첫 글자만 전송 (role 포함)
                            yield f"data: {json.dumps({'id': completion_id, 'object': 'chat.completion.chunk', 'created': created, 'model': MODEL_ID, 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': response_text[0]}, 'finish_reason': None}]})}\n\n"
                            
                            # 나머지 글자들 한 글자씩 전송 (적절한 지연 적용)
                            for char in response_text[1:]:
                                yield f"data: {json.dumps({'id': completion_id, 'object': 'chat.completion.chunk', 'created': created, 'model': MODEL_ID, 'choices': [{'index': 0, 'delta': {'content': char}, 'finish_reason': None}]})}\n\n"
                                # 매우 짧은 지연으로 자연스러운 타이핑 효과 제공
                                time.sleep(0.01)
                    
                    except Exception as e:
                        logger.error(f"텍스트 생성 실패: {e}")
                        logger.error(traceback.format_exc())
                        yield f"data: {json.dumps({'id': completion_id, 'object': 'chat.completion.chunk', 'created': created, 'model': MODEL_ID, 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': f'텍스트 생성 중 오류가 발생했습니다: {str(e)}'}, 'finish_reason': None}]})}\n\n"
                    
                    # 종료 청크 전송
                    yield f"data: {json.dumps({'id': completion_id, 'object': 'chat.completion.chunk', 'created': created, 'model': MODEL_ID, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"스트리밍 생성 오류: {e}")
                    logger.error(traceback.format_exc())
                    # 오류 발생 시 오류 메시지 전송
                    yield f"data: {json.dumps({'id': completion_id, 'object': 'chat.completion.chunk', 'created': created, 'model': MODEL_ID, 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': f'스트리밍 처리 중 오류가 발생했습니다: {str(e)}'}, 'finish_reason': 'error'}]})}\n\n"
                    yield "data: [DONE]\n\n"
            
            return StreamingResponse(generate_stream(), media_type="text/event-stream")
        
        # 일반 모드 (스트리밍 아닌 경우)
        else:
            start_time = time.time()
            
            try:
                # 시스템 프롬프트 처리
                system_prompt = None
                for msg in request.messages:
                    if isinstance(msg, dict) and msg.get("role") == "system":
                        system_prompt = msg.get("content")
                        break
                    elif hasattr(msg, "role") and msg.role == "system":
                        system_prompt = msg.content
                        break
                
                # 텍스트 생성
                if img is not None:
                    try:
                        # 설정 로드 시도
                        config = None
                        if load_config:
                            try:
                                # Qwen 모델 설정 파일 로드
                                abs_model_path = os.path.abspath(os.path.join(MODEL_DIR, "mlx_models", MODEL_ID))
                                config = load_config(abs_model_path)
                                logger.info(f"모델 설정 로드됨: {config.get('model_type', 'unknown')}")
                            except Exception as e:
                                logger.warning(f"모델 설정 로드 실패: {e}")
                                config = {"chat_template": "simple"}
                        else:
                            config = {"chat_template": "simple"}
                            
                        # 포맷된 프롬프트 생성
                        try:
                            formatted_prompt = apply_chat_template(
                                PROCESSOR, 
                                config, 
                                text_prompt, 
                                system=system_prompt, 
                                num_images=1
                            )
                            logger.info(f"스트리밍 모드 포맷된 프롬프트: {formatted_prompt[:100]}..." if len(formatted_prompt) > 100 else f"포맷된 프롬프트: {formatted_prompt}")
                            
                            # 생성 매개변수 정확히 설정
                            response_text = generate(
                                MODEL, 
                                PROCESSOR, 
                                formatted_prompt, 
                                [img],
                                max_tokens=request.max_tokens,
                                temperature=request.temperature,
                                top_p=request.top_p if hasattr(request, 'top_p') and request.top_p is not None else 0.95,
                                verbose=False
                            )
                        except Exception as e:
                            logger.warning(f"스트리밍 모드에서 포맷된 프롬프트 처리 실패: {e}, 직접 프롬프트 전달")
                            response_text = generate(
                                MODEL, 
                                PROCESSOR, 
                                text_prompt, 
                                [img],
                                max_tokens=request.max_tokens,
                                temperature=request.temperature
                            )
                    except Exception as e:
                        logger.error(f"스트리밍 모드에서 이미지와 텍스트 생성 실패: {e}")
                        response_text = generate(
                            MODEL, 
                            PROCESSOR, 
                            text_prompt,
                            max_tokens=request.max_tokens,
                            temperature=request.temperature
                        )
                else:
                    try:
                        # 설정 로드 시도
                        config = None
                        if load_config:
                            try:
                                # Qwen 모델 설정 파일 로드
                                abs_model_path = os.path.abspath(os.path.join(MODEL_DIR, "mlx_models", MODEL_ID))
                                config = load_config(abs_model_path)
                                logger.info(f"모델 설정 로드됨: {config.get('model_type', 'unknown')}")
                            except Exception as e:
                                logger.warning(f"모델 설정 로드 실패: {e}")
                                config = {"chat_template": "simple"}
                        else:
                            config = {"chat_template": "simple"}
                            
                        # 포맷된 프롬프트 생성
                        try:
                            formatted_prompt = apply_chat_template(
                                PROCESSOR, 
                                config, 
                                text_prompt, 
                                system=system_prompt, 
                                num_images=0
                            )
                            logger.info(f"스트리밍 모드 포맷된 프롬프트: {formatted_prompt[:100]}..." if len(formatted_prompt) > 100 else f"포맷된 프롬프트: {formatted_prompt}")
                            
                            # 생성 매개변수 정확히 설정
                            response_text = generate(
                                MODEL, 
                                PROCESSOR, 
                                formatted_prompt,
                                max_tokens=request.max_tokens,
                                temperature=request.temperature,
                                top_p=request.top_p if hasattr(request, 'top_p') and request.top_p is not None else 0.95,
                                verbose=False
                            )
                        except Exception as e:
                            logger.warning(f"스트리밍 모드에서 포맷된 프롬프트 처리 실패: {e}, 직접 프롬프트 전달")
                            response_text = generate(
                                MODEL, 
                                PROCESSOR, 
                                text_prompt,
                                max_tokens=request.max_tokens,
                                temperature=request.temperature
                            )
                        except Exception as e:
                            logger.error(f"스트리밍 모드에서 텍스트 생성 실패: {e}")
                            # 오류 발생 시 간단한 방식 시도
                            response_text = generate(
                                MODEL, 
                                PROCESSOR, 
                                text_prompt,
                                max_tokens=request.max_tokens,
                                temperature=request.temperature
                            )
                    except Exception as e:
                        logger.error(f"스트리밍 모드에서 텍스트 생성 실패: {e}")
                        # 오류 발생 시 간단한 방식 시도
                        response_text = generate(
                            MODEL, 
                            PROCESSOR, 
                            text_prompt,
                            max_tokens=request.max_tokens,
                            temperature=request.temperature
                        )
                
                # 리스트 반환값 처리
                if isinstance(response_text, list) and len(response_text) > 0:
                    response_text = response_text[0]
                
                logger.info(f"생성 완료: {response_text[:100]}..." if len(response_text) > 100 else f"생성 완료: {response_text}")
            except Exception as e:
                logger.error(f"채팅 완료 처리 오류: {e}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"채팅 완료 오류: {str(e)}")
            
            end_time = time.time()
            logger.info(f"생성 시간: {end_time - start_time:.2f}초")
            logger.info(f"응답: {response_text[:100]}{'...' if len(response_text) > 100 else ''}")
            
            # 응답 구성
            completion_id = f"chatcmpl-{str(uuid.uuid4())}"
            input_tokens = len(text_prompt.split())
            output_tokens = len(response_text.split())
            
            response = ChatCompletionResponse(
                id=completion_id,
                object="chat.completion",
                created=int(time.time()),
                model=MODEL_ID,
                choices=[
                    ChatCompletionResponseChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=response_text
                        ),
                        finish_reason="stop"
                    )
                ],
                usage={
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                }
            )
            
            return response
        
    except Exception as e:
        logger.error(f"채팅 완료 오류: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"채팅 완료 오류: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Qwen-VL OpenAI 호환 API 서버")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="서버 호스트")
    parser.add_argument("--port", type=int, default=8000, help="서버 포트")
    parser.add_argument("--model-dir", type=str, default="models", help="모델 디렉토리")
    parser.add_argument("--model-id", type=str, help="사용할 모델 ID")
    
    args = parser.parse_args()
    
    # 환경 변수 설정
    os.environ["MODEL_DIR"] = args.model_dir
    if args.model_id:
        os.environ["MODEL_ID"] = args.model_id
    
    logger.info(f"API 서버 시작: {args.host}:{args.port}")
    logger.info(f"모델 디렉토리: {args.model_dir}")
    if args.model_id:
        logger.info(f"모델 ID: {args.model_id}")
    
    uvicorn.run(app, host=args.host, port=args.port) 