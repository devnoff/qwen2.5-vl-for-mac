#!/bin/bash

# 오류 발생 시 스크립트 중단
set -e

# Qwen-2.5-VL 모델을 위한 환경 설정 스크립트
echo "Apple Silicon M4 Pro를 위한 Qwen-2.5-VL 환경 설정 시작..."

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
MODEL_DIR="$WORK_DIR/models"
MLX_MODEL_DIR="$WORK_DIR/models/mlx_models"
LOG_DIR="$WORK_DIR/logs"
SCRIPTS_DIR="$WORK_DIR/scripts"

# 로그 디렉토리 생성
mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/setup_environment_$(date +"%Y%m%d_%H%M%S").log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "로그 파일: $LOG_FILE"
echo "스크립트 디렉토리: $SCRIPT_DIR"
echo "프로젝트 루트: $PROJECT_ROOT"

# 오류 처리 함수
handle_error() {
    echo "오류가 발생했습니다: $1" | tee -a "$LOG_FILE"
    echo "로그 파일을 확인하세요: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 1
}

# 필요한 디렉토리 생성
mkdir -p $MODEL_DIR
mkdir -p $MLX_MODEL_DIR
mkdir -p $SCRIPTS_DIR

cd $WORK_DIR

# Python 3.12 확인 및 설치
echo "Python 3.12 확인 중..."
if ! command -v python3.12 &> /dev/null; then
    echo "Python 3.12가 설치되어 있지 않습니다. Homebrew를 통해 설치를 시도합니다."
    if ! command -v brew &> /dev/null; then
        echo "Homebrew가 설치되어 있지 않습니다. 먼저 Homebrew를 설치해야 합니다."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || handle_error "Homebrew 설치 실패"
    fi
    brew install python@3.12 || handle_error "Python 3.12 설치 실패"
    
    if ! command -v python3.12 &> /dev/null; then
        handle_error "Python 3.12 설치 후에도 명령을 찾을 수 없습니다"
    fi
fi

PYTHON_CMD="python3.12"
echo "Python 3.12 설치 확인됨: $($PYTHON_CMD --version)"

# 가상 환경 생성 및 활성화
echo "Python 가상 환경 생성 및 활성화 중..."
if [ ! -d "$WORK_DIR/venv" ]; then
    $PYTHON_CMD -m venv venv || handle_error "가상 환경 생성 실패"
fi
source "$WORK_DIR/venv/bin/activate" || handle_error "가상 환경 활성화 실패"

# pip 업그레이드
echo "pip 업그레이드 중..."
pip install --upgrade pip || handle_error "pip 업그레이드 실패"

# 필수 라이브러리 설치
echo "필수 라이브러리 설치 중..."
pip install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cpu || handle_error "PyTorch 설치 실패"
pip install transformers==4.38.1 pillow==10.2.0 accelerate==0.27.2 safetensors==0.4.2 sentencepiece==0.1.99 || handle_error "Transformers 및 관련 라이브러리 설치 실패"
pip install fastapi==0.100.1 uvicorn==0.23.2 python-multipart pydantic-settings || handle_error "FastAPI 및 관련 라이브러리 설치 실패"

# Apple Silicon을 위한 MLX 패키지 설치
echo "MLX 패키지 설치 중... (Apple Silicon 최적화)"
# 최신 버전의 MLX 사용 - 0.5.0 버전이 없어 사용 가능한 최신 버전으로 변경
pip install --no-cache-dir mlx mlx-lm || handle_error "MLX 라이브러리 설치 실패"

# pytest 설치 (테스트를 위해)
pip install pytest==7.4.3 || handle_error "pytest 설치 실패"

# 환경 설정 완료
echo "Python 환경 설정 완료!"

# MLX API 서버 설치 여부 확인
echo "라이브러리 임포트 테스트 중..."
cat << EOF > $SCRIPTS_DIR/test_imports.py
try:
    import torch
    import mlx.core
    from fastapi import FastAPI
    from pydantic import BaseModel
    from transformers import AutoTokenizer
    from PIL import Image
    
    # 모든 라이브러리가 성공적으로 임포트되었음
    print("SUCCESS: 모든 라이브러리가 성공적으로 임포트되었습니다.")
    exit(0)
except ImportError as e:
    print(f"ERROR: 라이브러리 임포트 실패: {e}")
    exit(1)
EOF

# 임포트 테스트 실행
python $SCRIPTS_DIR/test_imports.py || handle_error "라이브러리 임포트 테스트 실패"

echo "Qwen-2.5-VL 환경이 성공적으로 설정되었습니다."
echo "다음 단계: Qwen-2.5-VL 모델 다운로드 또는 변환"

# 모델 다운로드 안내
echo "
환경 설정이 완료되었습니다!

다음 명령어로 모델을 다운로드하세요:
bash $SCRIPTS_DIR/download_model.sh

또는 전체 설치 프로세스를 계속 진행하세요:
bash $WORK_DIR/setup.sh
" 