#!/usr/bin/env python3
import sys
import os
import time
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Qwen-2.5-VL 모델을 MLX 형식으로 변환")
    parser.add_argument("--input-dir", type=str, required=True, help="입력 모델 디렉토리")
    parser.add_argument("--output-dir", type=str, required=True, help="출력 MLX 모델 디렉토리")
    parser.add_argument("--quantize", action="store_true", help="모델 양자화 여부")
    args = parser.parse_args()
    
    input_dir = args.input_dir
    output_dir = args.output_dir
    quantize = args.quantize
    
    print(f"입력 디렉토리: {input_dir}")
    print(f"출력 디렉토리: {output_dir}")
    print(f"양자화: {quantize}")
    
    # 출력 디렉토리 준비
    os.makedirs(output_dir, exist_ok=True)
    
    # mlx_lm 모듈 임포트
    try:
        from mlx_lm.convert import convert as mlx_convert
        
        # 직접 모듈 함수 호출 (subprocess 없이)
        mlx_convert(
            hf_path=input_dir,
            mlx_path=output_dir,
            quantize=quantize,
            model_key_or_path=None,
            vocab_key_or_path=None,
            repo_id=None,
            access_token=None,
        )
        
        # 성공 여부 확인
        if os.path.exists(os.path.join(output_dir, "config.json")):
            print("변환 성공!")
            return 0
        else:
            print("변환 실패 - 출력 디렉토리에 config.json이 없습니다.")
            return 1
            
    except Exception as e:
        print(f"변환 중 오류 발생: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
