#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import base64
import requests
import json
from PIL import Image
import io
import time

# 테스트 이미지 경로 설정
TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test_images", "test.png")

def encode_image(image_path):
    """이미지를 Base64로 인코딩"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_text_generation(api_url, model_id="qwen2.5-vl-7B-mlx"):
    """텍스트 생성 API 테스트"""
    prompt = "안녕하세요! 오늘 날씨는 어떤가요?"
    
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"API 요청 URL: {api_url}")
    print(f"프롬프트: {prompt}")
    
    try:
        start_time = time.time()
        response = requests.post(f"{api_url}/v1/chat/completions", headers=headers, json=payload)
        end_time = time.time()
        
        print(f"응답 시간: {end_time - start_time:.2f}초")
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("응답 성공!")
            print(f"생성된 텍스트: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"오류 응답: {response.text}")
            return False
    except Exception as e:
        print(f"API 요청 오류: {e}")
        return False

def test_image_generation(api_url, model_id="qwen2.5-vl-7B-mlx"):
    """이미지-텍스트 생성 API 테스트"""
    # 이미지가 존재하는지 확인
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"테스트 이미지를 찾을 수 없습니다: {TEST_IMAGE_PATH}")
        return False
    
    # 이미지 인코딩
    base64_image = encode_image(TEST_IMAGE_PATH)
    
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "이 이미지에 대해 설명해 주세요."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"API 요청 URL: {api_url}")
    print(f"이미지 파일: {TEST_IMAGE_PATH}")
    
    try:
        start_time = time.time()
        response = requests.post(f"{api_url}/v1/chat/completions", headers=headers, json=payload)
        end_time = time.time()
        
        print(f"응답 시간: {end_time - start_time:.2f}초")
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("응답 성공!")
            print(f"생성된 텍스트: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"오류 응답: {response.text}")
            return False
    except Exception as e:
        print(f"API 요청 오류: {e}")
        return False

def test_models_api(api_url):
    """모델 목록 API 테스트"""
    try:
        response = requests.get(f"{api_url}/v1/models")
        
        if response.status_code == 200:
            result = response.json()
            print("모델 목록 응답 성공!")
            print(f"사용 가능한 모델: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"모델 목록 API 오류 응답: {response.text}")
            return False
    except Exception as e:
        print(f"모델 목록 API 요청 오류: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Qwen2.5-VL API 테스트")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="API 서버 URL")
    parser.add_argument("--model", type=str, default="qwen2.5-vl-7B-mlx", help="모델 ID")
    parser.add_argument("--test", choices=["text", "image", "models", "all"], default="all",
                       help="실행할 테스트 (text, image, models, all)")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print(f"Qwen2.5-VL API 테스트 시작")
    print(f"서버 URL: {args.url}")
    print(f"모델 ID: {args.model}")
    print("=" * 50)
    
    if args.test in ["models", "all"]:
        print("\n1. 모델 목록 API 테스트")
        success = test_models_api(args.url)
        print("모델 목록 테스트 결과:", "성공" if success else "실패")
    
    if args.test in ["text", "all"]:
        print("\n2. 텍스트 생성 API 테스트")
        success = test_text_generation(args.url, args.model)
        print("텍스트 생성 테스트 결과:", "성공" if success else "실패")
    
    if args.test in ["image", "all"]:
        print("\n3. 이미지-텍스트 생성 API 테스트")
        success = test_image_generation(args.url, args.model)
        print("이미지-텍스트 생성 테스트 결과:", "성공" if success else "실패")
    
    print("\n테스트 완료!")

if __name__ == "__main__":
    main() 