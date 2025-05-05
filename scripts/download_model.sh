#!/bin/bash

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # 색상 리셋

echo -e "${GREEN}Qwen-2.5-VL 모델 다운로드를 시작합니다...${NC}"

# 작업 디렉토리 설정 - 심볼릭 링크 처리를 위한 개선된 방법
REAL_SOURCE="${BASH_SOURCE[0]}"
while [ -L "$REAL_SOURCE" ]; do
    REAL_DIR="$(cd -P "$(dirname "$REAL_SOURCE")" && pwd)"
    REAL_SOURCE="$(readlink "$REAL_SOURCE")"
    [[ $REAL_SOURCE != /* ]] && REAL_SOURCE="$REAL_DIR/$REAL_SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$REAL_SOURCE")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WORK_DIR="$PROJECT_ROOT"
mkdir -p "$WORK_DIR/models"

echo "스크립트 디렉토리: $SCRIPT_DIR"
echo "프로젝트 루트: $PROJECT_ROOT"

# 가상 환경 확인
if [ ! -d "$WORK_DIR/venv" ]; then
    echo -e "${RED}가상 환경이 설정되어 있지 않습니다. 먼저 환경 설정을 실행하세요.${NC}"
    echo "./scripts/setup_environment.sh"
    exit 1
fi

# 가상 환경 활성화
source "$WORK_DIR/venv/bin/activate"

# Git LFS 확인
if ! command -v git-lfs &> /dev/null; then
    echo -e "${RED}Git LFS가 설치되어 있지 않습니다. 먼저, Git LFS를 설치해야 합니다.${NC}"
    echo "brew install git-lfs"
    exit 1
fi

# 파라미터 처리 추가
MODEL_SIZE=""  # 기본값 없음

# 인자 처리
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --model-size) MODEL_SIZE="$2"; shift ;;
        *) echo "알 수 없는 파라미터: $1"; exit 1 ;;
    esac
    shift
done

# 환경 변수에서 확인
if [ -n "$QWEN_MODEL_SIZE" ] && [ -z "$MODEL_SIZE" ]; then
    MODEL_SIZE="$QWEN_MODEL_SIZE"
    echo "환경 변수에서 모델 크기를 가져왔습니다: ${MODEL_SIZE}"
fi

# 파라미터나 환경 변수가 없으면 사용자에게 선택 요청
if [ -z "$MODEL_SIZE" ]; then
    echo "다운로드할 모델 크기를 선택하세요:"
    echo "1) Qwen-2.5-VL-3B (소형, 빠름, 가장 적은 메모리 필요)"
    echo "2) Qwen-2.5-VL-7B (중형, 균형적인 품질)"
    echo "3) Qwen-2.5-VL-32B (대형, 최고 품질, 많은 메모리 필요)"

    read -p "선택하세요 (1-3) [기본: 2]: " model_option
    model_option=${model_option:-2}

    case $model_option in
        1) MODEL_SIZE="3B" ;;
        2) MODEL_SIZE="7B" ;;
        3) MODEL_SIZE="32B" ;;
        *) MODEL_SIZE="7B" ;; # 기본값
    esac
    
    # 다른 스크립트에서도 사용할 수 있도록 환경 변수 설정
    export QWEN_MODEL_SIZE="$MODEL_SIZE"
fi

echo "다운로드할 모델: Qwen-2.5-VL-${MODEL_SIZE}"

# 모델 설정
MODEL_NAME="Qwen/Qwen2.5-VL-${MODEL_SIZE}-Instruct"

# 선택한 모델 정보를 파일로 저장 (스크립트 간 공유용)
echo "$MODEL_SIZE" > "$WORK_DIR/.selected_model_size"

# 다운로드 방법 선택
echo -e "${GREEN}다운로드 방법을 선택하세요:${NC}"
echo "1) Hugging Face Hub API로 다운로드 (권장, 토큰 필요)"
echo "2) Git LFS로 클론 (대체 방법)"

read -p "선택하세요 (1-2) [기본: 1]: " download_method
download_method=${download_method:-1}

if [ "$download_method" -eq 1 ]; then
    # Hugging Face Hub API로 다운로드
    echo -e "${GREEN}Hugging Face Hub API를 사용하여 모델을 다운로드합니다...${NC}"
    
    pip install -q huggingface_hub
    
    # 토큰 설정
    read -p "Hugging Face 토큰이 있습니까? (y/n): " has_token
    if [[ "$has_token" == "y" || "$has_token" == "Y" ]]; then
        read -p "Hugging Face 토큰을 입력하세요: " hf_token
        export HUGGING_FACE_HUB_TOKEN="$hf_token"
    else
        echo -e "${YELLOW}토큰 없이 다운로드하면 속도 제한이 있을 수 있습니다.${NC}"
    fi
    
    # 다운로드 스크립트가 이미 존재하는지 확인
    if [ ! -f "$SCRIPT_DIR/download_hf_model.py" ]; then
        # 다운로드 스크립트 생성
        cat > "$SCRIPT_DIR/download_hf_model.py" << 'EOF'
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
EOF
    fi
    
    # 다운로드 실행
    OUTPUT_DIR="$WORK_DIR/models/Qwen2.5-VL-${MODEL_SIZE}-original"
    python "$SCRIPT_DIR/download_hf_model.py" --model_name "$MODEL_NAME" --output_dir "$OUTPUT_DIR"
    
    echo -e "${GREEN}모델이 다음 위치에 다운로드되었습니다: $OUTPUT_DIR${NC}"
    
else
    # Git LFS로 클론
    echo -e "${GREEN}Git LFS를 사용하여 모델을 다운로드합니다...${NC}"
    
    git lfs install
    
    OUTPUT_DIR="$WORK_DIR/models/Qwen2.5-VL-${MODEL_SIZE}-original"
    if [ -d "$OUTPUT_DIR" ]; then
        echo -e "${YELLOW}이미 존재하는 디렉토리입니다: $OUTPUT_DIR${NC}"
        read -p "덮어쓰시겠습니까? (y/n): " overwrite
        if [[ "$overwrite" == "y" || "$overwrite" == "Y" ]]; then
            rm -rf "$OUTPUT_DIR"
        else
            echo -e "${YELLOW}다운로드를 건너뜁니다.${NC}"
            exit 0
        fi
    fi
    
    # 메모리 부족 문제를 방지하기 위해 부분 클론
    mkdir -p "$OUTPUT_DIR"
    cd "$OUTPUT_DIR"
    
    git init
    git remote add origin "https://huggingface.co/$MODEL_NAME"
    git config core.sparseCheckout true
    
    # 필수 파일만 가져오기
    cat > .git/info/sparse-checkout << EOF
*.json
*.model
*.bin
*.safetensors
*.txt
config*
vocab*
EOF
    
    git pull origin main
    
    echo -e "${GREEN}모델이 다음 위치에 다운로드되었습니다: $OUTPUT_DIR${NC}"
fi

echo -e "${GREEN}모델 다운로드가 완료되었습니다.${NC}"
echo -e "${YELLOW}다음 단계:${NC}"
echo "MLX 변환: ./scripts/convert_to_mlx.sh" 