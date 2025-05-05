#!/usr/bin/env python3
import os
import sys
import time
import traceback
from pathlib import Path

def main():
    try:
        # 스크립트 경로를 기준으로 상대 경로 구성
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent
        
        # 환경 설정 (상대 경로 사용)
        input_dir = os.path.join(project_root, "models", "Qwen2.5-VL-32B-original")
        output_dir = os.path.join(project_root, "models", "mlx_models", "qwen-2.5-vl-32b")
        quantize = n
        
        print(f"입력 디렉토리: {input_dir}")
        print(f"출력 디렉토리: {output_dir}")
        print(f"양자화: {quantize}")
        
        # 출력 디렉토리 검증
        if os.path.exists(output_dir):
            print(f"오류: 출력 디렉토리가 이미 존재합니다: {output_dir}")
            return 1
            
        # mlx_lm 모듈 임포트
        from mlx_lm import convert
        print("MLX-LM 모듈 로드 완료")
        
        # 변환 옵션 정의
        args = {
            "hf_path": input_dir,
            "mlx_path": output_dir,
            "quantize": quantize
        }
        
        # 변환 실행
        print("변환 시작...")
        start_time = time.time()
        
        # 변환 과정의 구성 요소 직접 호출
        try:
            from mlx_lm.utils import get_model
            from transformers import AutoProcessor
            import mlx.core as mx
            
            print("모델 로드 중...")
            model = get_model(args["hf_path"], quantize=args["quantize"])
            print("프로세서 로드 중...")
            processor = AutoProcessor.from_pretrained(args["hf_path"])
            
            print("디렉토리 생성 중...")
            os.makedirs(args["mlx_path"], exist_ok=True)
            
            print("모델 저장 중...")
            mx.save_model(model, args["mlx_path"])
            
            print("토크나이저 저장 중...")
            processor.save_pretrained(args["mlx_path"])
            
            print(f"완료! 모델이 {args['mlx_path']}에 저장되었습니다.")
        except Exception as e:
            print(f"변환 중 오류 발생: {e}")
            traceback.print_exc()
            return 1
        
        duration = time.time() - start_time
        print(f"변환 완료! 소요 시간: {duration:.2f}초")
        
        # 성공 여부 확인
        if os.path.exists(os.path.join(output_dir, "config.json")):
            print("변환 성공!")
            return 0
        else:
            print("변환은 완료되었지만 config.json이 없습니다.")
            return 1
    except Exception as e:
        print(f"변환 중 오류 발생: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
