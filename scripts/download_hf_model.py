import os
import argparse
from huggingface_hub import snapshot_download

def main():
    parser = argparse.ArgumentParser(description="Hugging Face 모델 다운로드")
    parser.add_argument("--model_name", type=str, required=True,
                       help="다운로드할 모델 이름 (예: Qwen/Qwen2.5-VL-7B-Instruct)")
    parser.add_argument("--output_dir", type=str, required=True,
                       help="모델을 저장할 디렉토리")
    args = parser.parse_args()
    
    print(f"다운로드 시작: {args.model_name}")
    
    # 환경 변수에서 토큰 확인
    token = os.environ.get("HUGGING_FACE_HUB_TOKEN")
    
    # 다운로드
    model_path = snapshot_download(
        repo_id=args.model_name,
        token=token,
        local_dir=args.output_dir,
        local_dir_use_symlinks=False
    )
    
    print(f"다운로드 완료: {model_path}")

if __name__ == "__main__":
    main()
