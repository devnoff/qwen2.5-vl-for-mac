#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
from mlx_lm import load, convert

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_args():
    """커맨드 라인 인수 설정"""
    parser = argparse.ArgumentParser(description="Hugging Face 모델을 MLX 형식으로 변환")
    parser.add_argument(
        "--model_path", 
        type=str, 
        required=True,
        help="Hugging Face 모델 경로 (로컬 경로 또는 Hugging Face Hub ID)"
    )
    parser.add_argument(
        "--mlx_model_path", 
        type=str, 
        help="변환된 MLX 모델을 저장할 경로 (기본값: {model_path}-mlx)"
    )
    parser.add_argument(
        "--trust_remote_code", 
        action="store_true",
        help="원격 코드 신뢰 여부 (일부 모델에 필요)"
    )
    parser.add_argument(
        "--torch_dtype", 
        type=str, 
        default="auto",
        choices=["auto", "float16", "bfloat16"],
        help="PyTorch 데이터 타입 (auto, float16, bfloat16)"
    )
    parser.add_argument(
        "--vision", 
        action="store_true",
        help="vision 모델인지 여부"
    )
    return parser.parse_args()

def main():
    """메인 함수"""
    args = setup_args()
    
    # 기본 MLX 모델 경로 설정
    if not args.mlx_model_path:
        args.mlx_model_path = f"{args.model_path}-mlx"
    
    logger.info(f"변환 시작: {args.model_path} → {args.mlx_model_path}")
    
    # Torch 데이터 타입 설정
    if args.torch_dtype == "auto":
        torch_dtype = "auto"
    elif args.torch_dtype == "float16":
        torch_dtype = torch.float16
    elif args.torch_dtype == "bfloat16":
        torch_dtype = torch.bfloat16
    else:
        torch_dtype = "auto"
    
    try:
        # 일반 모델과 비전 모델 구분하여 로드 및 변환
        if not args.vision:
            logger.info("일반 텍스트 모델 로드 중...")
            
            # 모델 설정 로드
            config = AutoConfig.from_pretrained(
                args.model_path,
                trust_remote_code=args.trust_remote_code
            )
            
            # 토크나이저 로드
            tokenizer = AutoTokenizer.from_pretrained(
                args.model_path,
                trust_remote_code=args.trust_remote_code
            )
            
            # 모델 로드
            model = AutoModelForCausalLM.from_pretrained(
                args.model_path,
                torch_dtype=torch_dtype,
                trust_remote_code=args.trust_remote_code
            )
            
            # MLX 형식으로 변환
            convert.convert_model(
                model_path=args.model_path,
                save_path=args.mlx_model_path,
                trust_remote_code=args.trust_remote_code,
                torch_dtype=torch_dtype
            )
        else:
            logger.info("비전 모델 로드 중...")
            
            # MLX-VLM의 convert 함수 사용
            from mlx_vlm.convert import convert_hf_vl_model
            
            # 비전 모델 변환
            logger.info(f"Qwen-VL 모델을 MLX 형식으로 변환 중: {args.model_path}")
            convert_hf_vl_model(
                args.model_path,
                args.mlx_model_path,
                trust_remote_code=args.trust_remote_code
            )
        
        logger.info(f"모델 변환 완료: {args.mlx_model_path}")
    except Exception as e:
        logger.error(f"모델 변환 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 