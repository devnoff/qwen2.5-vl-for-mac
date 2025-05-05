#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
from PIL import Image
from inspect import signature

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # 모델 경로 설정
    model_path = "models/mlx_models/qwen2.5-vl-7B-mlx"
    abs_model_path = os.path.abspath(model_path)
    
    logger.info(f"Python 버전: {sys.version}")
    logger.info(f"모델 경로: {abs_model_path}")
    
    # mlx-vlm 패키지에서 load 함수 가져오기
    try:
        from mlx_vlm import load
        logger.info("mlx_vlm 패키지 로드 성공")
    except ImportError as e:
        logger.error(f"mlx_vlm 패키지 로드 실패: {e}")
        sys.exit(1)
    
    # 모델 로드
    try:
        logger.info("모델 로드 시작...")
        start_time = time.time()
        model, processor = load(abs_model_path)
        load_time = time.time() - start_time
        logger.info(f"모델 로드 완료 (소요 시간: {load_time:.2f}초)")
        logger.info(f"모델 타입: {type(model)}")
        logger.info(f"프로세서 타입: {type(processor)}")
    except Exception as e:
        logger.error(f"모델 로드 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    # Generate 함수 가져오기 및 시그니처 확인
    try:
        from mlx_vlm import generate
        logger.info(f"generate 함수 타입: {type(generate)}")
        logger.info(f"generate 함수 시그니처: {signature(generate)}")
    except ImportError as e:
        logger.error(f"generate 함수 로드 실패: {e}")
        sys.exit(1)
    
    # 텍스트 생성 테스트
    try:
        logger.info("텍스트 생성 테스트 시작...")
        prompt = "안녕하세요. 오늘 날씨 어때요?"
        logger.info(f"프롬프트: {prompt}")
        
        start_time = time.time()
        output = generate(
            model, 
            processor, 
            prompt, 
            max_tokens=100,
            temperature=0.7,
            verbose=True
        )
        generation_time = time.time() - start_time
        
        logger.info(f"생성 결과 (소요 시간: {generation_time:.2f}초):")
        logger.info(f"OUTPUT: {output}")
    except Exception as e:
        logger.error(f"텍스트 생성 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # 방법 1: mlx_vlm.generate 모듈 직접 사용
    try:
        logger.info("\n=== 방법 1: mlx_vlm.generate 모듈 사용 ===")
        image_path = "tests/test_images/test.png"
        abs_image_path = os.path.abspath(image_path)
        
        if os.path.exists(abs_image_path):
            logger.info(f"이미지 파일 경로: {abs_image_path}")
            logger.info(f"이미지 파일 존재 여부: {os.path.exists(abs_image_path)}")
            
            # 이미지 정보 확인
            img = Image.open(abs_image_path)
            logger.info(f"이미지 크기: {img.size}, 모드: {img.mode}")
            
            # mlx_vlm.generate 모듈 사용
            import mlx_vlm.generate as gen_module
            
            prompt = "이 이미지에 대해 설명해 주세요."
            logger.info(f"프롬프트: {prompt}")
            
            start_time = time.time()
            output = gen_module.generate(
                model,
                processor,
                prompt,
                image=[abs_image_path],
                max_tokens=100,
                temperature=0.7,
                verbose=True
            )
            generation_time = time.time() - start_time
            
            logger.info(f"이미지 포함 생성 결과 (방법 1, 소요 시간: {generation_time:.2f}초):")
            logger.info(f"OUTPUT: {output}")
        else:
            logger.warning(f"이미지 파일이 존재하지 않습니다: {abs_image_path}")
    except Exception as e:
        logger.error(f"방법 1 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # 방법 2: generate 함수 직접 호출
    try:
        logger.info("\n=== 방법 2: generate 함수 직접 호출 ===")
        image_path = "tests/test_images/test.png"
        abs_image_path = os.path.abspath(image_path)
        
        if os.path.exists(abs_image_path):
            logger.info(f"이미지 파일 경로: {abs_image_path}")
            
            # 프롬프트 설정
            from mlx_vlm.utils import load_config
            from mlx_vlm.prompt_utils import apply_chat_template
            
            try:
                config = load_config(abs_model_path)
            except:
                config = {"chat_template": "simple"}
                
            prompt_text = "이 이미지에 대해 설명해 주세요."
            formatted_prompt = apply_chat_template(
                processor, config, prompt_text, num_images=1
            )
            
            logger.info(f"원본 프롬프트: {prompt_text}")
            logger.info(f"포맷된 프롬프트: {formatted_prompt[:100]}..." if len(formatted_prompt) > 100 else f"포맷된 프롬프트: {formatted_prompt}")
            
            start_time = time.time()
            output = generate(
                model, 
                processor, 
                formatted_prompt, 
                image=[abs_image_path],  # 이미지 경로를 리스트로 전달하고 명시적으로 image= 파라미터 사용
                max_tokens=100,
                temperature=0.7,
                verbose=True
            )
            generation_time = time.time() - start_time
            
            logger.info(f"이미지 포함 생성 결과 (방법 2, 소요 시간: {generation_time:.2f}초):")
            logger.info(f"OUTPUT: {output}")
        else:
            logger.warning(f"이미지 파일이 존재하지 않습니다: {abs_image_path}")
    except Exception as e:
        logger.error(f"방법 2 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # 방법 3: PIL 이미지 객체 전달
    try:
        logger.info("\n=== 방법 3: PIL 이미지 객체 전달 ===")
        image_path = "tests/test_images/test.png"
        abs_image_path = os.path.abspath(image_path)
        
        if os.path.exists(abs_image_path):
            # 이미지 로드 및 전처리
            image = Image.open(abs_image_path)
            logger.info(f"이미지 크기: {image.size}, 모드: {image.mode}")
            
            # RGB 모드로 변환 (필요한 경우)
            if image.mode != "RGB":
                image = image.convert("RGB")
                logger.info("이미지를 RGB 모드로 변환했습니다")
            
            # 프롬프트 설정
            prompt_text = "이 이미지에 대해 설명해 주세요."
            logger.info(f"프롬프트: {prompt_text}")
            
            start_time = time.time()
            output = generate(
                model, 
                processor, 
                prompt_text, 
                image=[image],  # PIL 이미지 객체를 리스트로 감싸서 전달
                max_tokens=100,
                temperature=0.7,
                verbose=True
            )
            generation_time = time.time() - start_time
            
            logger.info(f"이미지 포함 생성 결과 (방법 3, 소요 시간: {generation_time:.2f}초):")
            logger.info(f"OUTPUT: {output}")
        else:
            logger.warning(f"이미지 파일이 존재하지 않습니다: {abs_image_path}")
    except Exception as e:
        logger.error(f"방법 3 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 