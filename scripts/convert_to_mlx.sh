#!/bin/bash

# 디버깅을 위한 echo 명령어 활성화
set -x

# Qwen-2.5-VL 모델을 MLX 형식으로 변환하는 스크립트
echo "Qwen-2.5-VL 모델을 MLX 형식으로 변환을 시작합니다..."

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

# 작업 디렉토리로 이동
cd "$WORK_DIR"

# 로그 디렉토리 설정
LOG_DIR="$WORK_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/convert_to_mlx_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "스크립트 디렉토리: $SCRIPT_DIR"
echo "프로젝트 루트: $PROJECT_ROOT"

# 오류 처리 함수
handle_error() {
    echo "오류가 발생했습니다: $1" | tee -a "$LOG_FILE"
    echo "로그 파일을 확인하세요: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 1
}

# 가상 환경 활성화
source "$WORK_DIR/venv/bin/activate" || handle_error "가상 환경 활성화 실패"

# 필요한 패키지 설치
pip install mlx-vlm || handle_error "mlx-vlm 패키지 설치 실패"

# 모델 크기 선택
echo -e "${GREEN}변환할 모델 크기를 선택하세요:${NC}"
echo "1) Qwen-2.5-VL-3B (소형, 빠름, 가장 적은 메모리 필요)"
echo "2) Qwen-2.5-VL-7B (중형, 균형적인 품질)"
echo "3) Qwen-2.5-VL-32B (대형, 최고 품질, 많은 메모리 필요)"

read -p "선택하세요 (1-3): " model_option

case $model_option in
    1)
        MODEL_SIZE="3B"
        ;;
    2)
        MODEL_SIZE="7B"
        ;;
    3)
        MODEL_SIZE="32B"
        ;;
    *)
        echo "잘못된 선택입니다. 기본값으로 7B를 사용합니다."
        MODEL_SIZE="7B"
        ;;
esac

# 입력 및 출력 경로 설정
INPUT_MODEL_PATH="$MODEL_DIR/Qwen2.5-VL-${MODEL_SIZE}-original"
OUTPUT_MODEL_PATH="$MLX_MODEL_DIR/qwen2.5-vl-${MODEL_SIZE}-mlx"

# 입력 모델 존재 확인
if [ ! -d "$INPUT_MODEL_PATH" ]; then
    handle_error "모델이 존재하지 않습니다. 먼저 모델을 다운로드하세요. bash $SCRIPT_DIR/download_model.sh를 실행하여 모델을 다운로드하세요."
fi

echo "모델 경로 확인: $INPUT_MODEL_PATH"
ls -la "$INPUT_MODEL_PATH" | head -10

# 출력 디렉토리 생성
mkdir -p "$MLX_MODEL_DIR"

# 출력 모델 경로가 이미 존재하는 경우 확인
if [ -d "$OUTPUT_MODEL_PATH" ]; then
    echo "경고: 출력 디렉토리가 이미 존재합니다: $OUTPUT_MODEL_PATH"
    read -p "기존 디렉토리를 삭제하고 계속 진행하시겠습니까? (y/n): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        echo "기존 디렉토리 삭제 중..."
        rm -rf "$OUTPUT_MODEL_PATH" || handle_error "디렉토리 삭제 실패"
    else
        handle_error "사용자에 의해 작업이 중단되었습니다."
    fi
fi

# MLX 변환 실행
echo "MLX 변환 시작... (이 작업은 수 분이 소요될 수 있습니다)"

python -m mlx_vlm.convert \
    --hf-path "$INPUT_MODEL_PATH" \
    --mlx-path "$OUTPUT_MODEL_PATH" || handle_error "모델 변환 실패"

# 변환 결과 확인
if [ -d "$OUTPUT_MODEL_PATH" ]; then
    echo "
=================================================================
MLX 모델 변환이 완료되었습니다!
=================================================================

변환된 모델 정보:
- 모델 타입: Qwen2.5-VL-${MODEL_SIZE}
- 경로: $OUTPUT_MODEL_PATH

다음 단계:
1. MLX-VLM을 사용하여 모델 테스트:
   python -m mlx_vlm.generate --model $OUTPUT_MODEL_PATH --max-tokens 100 --temperature 0.0 --prompt \"이미지를 설명해주세요.\" --image <이미지_경로>

2. API 서버 시작:
   bash $SCRIPT_DIR/start_api_server.sh

3. Open Web UI 연결:
   cat $WORK_DIR/docs/connect_to_openwebui.md

=================================================================
"
else
    handle_error "모델 변환에 실패했습니다. 출력 디렉토리가 생성되지 않았습니다."
fi 