#!/usr/bin/env python3
import sys
import os
import shutil
import subprocess
from pathlib import Path

def main():
    # 스크립트 경로를 기준으로 상대 경로 구성
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    # 상대 경로 사용
    input_dir = os.path.join(project_root, "models", "Qwen2.5-VL-32B-original")
    output_dir = os.path.join(project_root, "models", "mlx_models", "qwen-2.5-vl-32b_20250502_162607")
    quantize = False  # 문자열이 아니라 Python 불리언으로 전달
    
    print(f"입력 디렉토리: {input_dir}")
    print(f"출력 디렉토리: {output_dir}")
    print(f"양자화: {quantize}")
    
    # 출력 디렉토리가 존재하는지 확인
    if os.path.exists(output_dir):
        print(f"출력 디렉토리가 이미 존재합니다: {output_dir}")
        # 확실하게 디렉토리 삭제
        try:
            shutil.rmtree(output_dir)
            print(f"디렉토리 삭제 완료: {output_dir}")
        except Exception as e:
            print(f"디렉토리 삭제 실패: {e}")
            # 권한 오류인 경우 sudo 시도
            try:
                subprocess.run(["sudo", "rm", "-rf", output_dir], check=True)
                print("sudo로 디렉토리 삭제 완료")
            except:
                print("sudo로도 삭제 실패")
                new_output_dir = f"{output_dir}_{os.getpid()}"
                print(f"대체 디렉토리 사용: {new_output_dir}")
                output_dir = new_output_dir
                
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 변환 명령 구성
    cmd = ["python", "-m", "mlx_lm", "convert", 
           "--hf-path", input_dir, 
           "--mlx-path", output_dir]
           
    if quantize:
        cmd.append("--quantize")
    
    # 명령 실행
    print(f"실행 명령: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    # 성공 확인
    if os.path.exists(os.path.join(output_dir, "config.json")):
        print("변환 성공!")
        return 0
    else:
        print("변환 실패 - 출력 디렉토리에 config.json이 없습니다")
        return 1

if __name__ == "__main__":
    sys.exit(main())
