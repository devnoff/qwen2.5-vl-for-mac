#!/usr/bin/env python3
import requests
import base64
import json
from PIL import Image
import io

# API 엔드포인트 설정
API_URL = "http://localhost:8000/v1/chat/completions"

# 테스트할 이미지 경로 입력
image_path = input("테스트할 이미지 경로를 입력하세요: ")

# 이미지를 base64로 인코딩
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

try:
    # 이미지 열기 및 크기 확인
    with Image.open(image_path) as img:
        width, height = img.size
        print(f"이미지 크기: {width}x{height}")
    
    # 이미지를 base64로 인코딩
    base64_image = encode_image_to_base64(image_path)
    
    # 프롬프트 입력
    prompt = input("질문을 입력하세요 (기본: '이 이미지에서 무엇을 볼 수 있습니까?'): ") or "이 이미지에서 무엇을 볼 수 있습니까?"
    
    # API 요청 생성
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 512
    }
    
    print("API 요청 중...")
    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        generated_text = result["choices"][0]["message"]["content"]
        print("\n응답:")
        print(generated_text)
    else:
        print(f"에러: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"오류 발생: {e}")

