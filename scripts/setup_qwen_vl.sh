#!/bin/bash

# 오류 발생 시 스크립트 중단
set -e

# Qwen-2.5-VL 모델 전체 설치 및 설정 스크립트
echo "Apple Silicon M4 Pro에서 Qwen-2.5-VL 모델 설치 프로세스를 시작합니다..."

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
LOG_DIR="$WORK_DIR/logs"
mkdir -p $LOG_DIR
MAIN_LOG_FILE="$LOG_DIR/setup_qwen_vl_$(date +"%Y%m%d_%H%M%S").log"
exec > >(tee -a "$MAIN_LOG_FILE") 2>&1

echo "로그 파일: $MAIN_LOG_FILE"
echo "스크립트 디렉토리: $SCRIPT_DIR"
echo "프로젝트 루트: $PROJECT_ROOT"

cd $WORK_DIR

# 오류 처리 함수
handle_error() {
    echo "오류가 발생했습니다: $1" | tee -a "$MAIN_LOG_FILE"
    echo "로그 파일을 확인하세요: $MAIN_LOG_FILE" | tee -a "$MAIN_LOG_FILE"
    exit 1
}

# 스크립트 실행 권한 부여
chmod +x "$SCRIPT_DIR/setup_environment.sh"
chmod +x "$SCRIPT_DIR/download_model.sh"
chmod +x "$SCRIPT_DIR/convert_to_mlx.sh"
chmod +x "$SCRIPT_DIR/start_api_server.sh"

echo "======================================================"
echo "Qwen-2.5-VL 모델 설치 과정"
echo "======================================================"
echo "1. Python 3.12 및 필요한 라이브러리 설치"
echo "2. Qwen-2.5-VL 모델 다운로드"
echo "3. 모델을 Apple Silicon 최적화 MLX 형식으로 변환"
echo "4. MLX 기반 추론 API 서버 설정"
echo "5. Open Web UI 연결 설정"
echo "======================================================"

# 사용자에게 진행 여부 확인
read -p "전체 설치 과정을 진행하시겠습니까? (y/n): " proceed

if [[ $proceed != "y" && $proceed != "Y" ]]; then
    echo "전체 자동 설치를 건너뜁니다. 다음 명령어로 개별 단계를 실행할 수 있습니다:"
    echo "1. 환경 설정: bash scripts/setup_environment.sh"
    echo "2. 모델 다운로드: bash scripts/download_model.sh"
    echo "3. MLX 변환: bash scripts/convert_to_mlx.sh"
    echo "4. API 서버 시작: bash scripts/start_api_server.sh"
    exit 0
fi

# 1. 환경 설정
echo "1단계: Python 3.12 환경 설정 중..."
"$SCRIPT_DIR/setup_environment.sh"

# 환경 설정 성공 여부 확인
if [ $? -ne 0 ]; then
    handle_error "환경 설정에 실패했습니다. setup_environment.sh 로그를 확인하세요."
fi

# 가상 환경 활성화
source "$WORK_DIR/venv/bin/activate" || handle_error "가상 환경 활성화 실패"

# 모델 선택을 한 번만 하고 환경 변수 및 파일에 저장
echo "모델 크기를 선택하세요:"
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

# 환경 변수로 모델 크기 전달
export QWEN_MODEL_SIZE="$MODEL_SIZE"

# 선택한 모델 정보를 파일로 저장 (스크립트 간 공유용)
echo "$MODEL_SIZE" > "$WORK_DIR/.selected_model_size"

echo "선택한 모델: Qwen-2.5-VL-${MODEL_SIZE}"

# 2. 모델 다운로드
echo "2단계: Qwen-2.5-VL 모델 다운로드 중..."
"$SCRIPT_DIR/download_model.sh" --model-size "$MODEL_SIZE"

# 모델 다운로드 성공 여부 확인
if [ $? -ne 0 ]; then
    handle_error "모델 다운로드에 실패했습니다. download_model.sh 로그를 확인하세요."
fi

# 3. MLX 변환
echo "3단계: 모델을 MLX 형식으로 변환 중..."
"$SCRIPT_DIR/convert_to_mlx.sh" --model-size "$MODEL_SIZE"

# MLX 변환 성공 여부 확인
if [ $? -ne 0 ]; then
    handle_error "MLX 변환에 실패했습니다. convert_to_mlx.sh 로그를 확인하세요."
fi

# 4. API 서버 시작
echo "4단계: API 서버 설정 중..."
echo "API 서버를 시작하여 모델을 테스트하시겠습니까? (y/n): " 
read start_server

if [[ $start_server == "y" || $start_server == "Y" ]]; then
    "$SCRIPT_DIR/start_api_server.sh"
    
    if [ $? -ne 0 ]; then
        handle_error "API 서버 시작에 실패했습니다. scripts/start_api_server.sh 로그를 확인하세요."
    else
        echo "API 서버가 성공적으로 시작되었습니다."
        echo "5단계: Open Web UI에 연결하기"
        cat "$PROJECT_ROOT/docs/connect_to_openwebui.md"
    fi
else
    echo "API 서버 시작을 건너뜁니다. 나중에 다음 명령어로 시작할 수 있습니다:"
    echo "bash scripts/start_api_server.sh"
    echo ""
    echo "Open Web UI 연결 방법은 다음 파일을 참조하세요:"
    echo "cat docs/connect_to_openwebui.md"
fi

echo "======================================================"
echo "Qwen-2.5-VL 설치가 완료되었습니다!"
echo "======================================================"
echo "- 모델 테스트: python tests/test_api.py"
echo "- API 서버 시작: bash scripts/start_api_server.sh"
echo "- Open Web UI 연결: 'docs/connect_to_openwebui.md' 참조"
echo ""
echo "추가 질문이나 문제가 있으면 README.md와 docs/INSTALL.md 파일을 참조하세요."
echo "======================================================" 