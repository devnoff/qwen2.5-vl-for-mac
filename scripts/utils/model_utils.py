#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import glob

logger = logging.getLogger(__name__)

def get_available_models(models_dir):
    """
    지정된 디렉토리에서 사용 가능한 MLX 모델 목록을 찾습니다.
    
    Args:
        models_dir (str): 모델이 저장된 디렉토리 경로
        
    Returns:
        list: 발견된 모델 경로 목록
    """
    if not os.path.exists(models_dir):
        logger.warning(f"모델 디렉토리가 존재하지 않습니다: {models_dir}")
        return []
    
    # MLX 모델 디렉토리 패턴 검색
    model_dirs = []
    
    # -mlx로 끝나는 디렉토리 찾기
    mlx_dirs = [d for d in os.listdir(models_dir) 
               if os.path.isdir(os.path.join(models_dir, d)) and d.endswith("-mlx")]
    
    for mlx_dir in mlx_dirs:
        model_path = os.path.join(models_dir, mlx_dir)
        # 모델 파일 확인 (tokenizer.json, model.safetensors 등이 있는지)
        if (os.path.exists(os.path.join(model_path, "tokenizer.json")) and 
            (os.path.exists(os.path.join(model_path, "model.safetensors")) or 
             os.path.exists(os.path.join(model_path, "weights.safetensors")))):
            model_dirs.append(model_path)
    
    return model_dirs

def get_model_name(model_path):
    """
    모델 경로에서 모델 이름을 추출합니다.
    
    Args:
        model_path (str): 모델 경로
        
    Returns:
        str: 모델 이름
    """
    # 경로에서 마지막 디렉토리 이름을 가져옴
    model_name = os.path.basename(model_path)
    return model_name

def check_model_compatibility(model_path):
    """
    모델이 MLX-VLM과 호환되는지 확인합니다.
    
    Args:
        model_path (str): 모델 경로
        
    Returns:
        bool: 호환성 여부
    """
    required_files = ["tokenizer.json", "config.json"]
    model_files = ["model.safetensors", "weights.safetensors"]
    
    # 필수 파일 확인
    for req_file in required_files:
        if not os.path.exists(os.path.join(model_path, req_file)):
            logger.warning(f"필수 파일이 없습니다: {req_file}")
            return False
    
    # 모델 파일 확인 (둘 중 하나는 있어야 함)
    has_model_file = False
    for model_file in model_files:
        if os.path.exists(os.path.join(model_path, model_file)):
            has_model_file = True
            break
    
    if not has_model_file:
        logger.warning(f"모델 가중치 파일이 없습니다: model.safetensors 또는 weights.safetensors")
        return False
    
    # vision 모델인지 확인 (qwen-vl인 경우)
    config_path = os.path.join(model_path, "config.json")
    
    # TODO: 모델 유형에 따른 추가 확인 로직 구현
    
    return True

def get_model_metadata(model_path):
    """
    모델의 메타데이터 정보를 가져옵니다.
    
    Args:
        model_path (str): 모델 경로
        
    Returns:
        dict: 모델 메타데이터
    """
    metadata = {
        "id": get_model_name(model_path),
        "path": model_path,
        "created": None,
        "object": "model",
        "owned_by": "user"
    }
    
    # 모델 크기 계산
    model_size = 0
    for root, _, files in os.walk(model_path):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.exists(file_path):
                model_size += os.path.getsize(file_path)
    
    metadata["size"] = model_size
    
    return metadata

def format_openai_model_list(model_paths):
    """
    모델 경로 목록을 OpenAI API 형식의 모델 목록으로 변환합니다.
    
    Args:
        model_paths (list): 모델 경로 목록
        
    Returns:
        dict: OpenAI API 형식의 모델 목록
    """
    models_data = []
    
    for model_path in model_paths:
        metadata = get_model_metadata(model_path)
        models_data.append(metadata)
    
    return {
        "object": "list",
        "data": models_data
    } 