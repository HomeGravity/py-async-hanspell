import aiohttp
import asyncio
import re
from urllib import parse
import time

from . import __version__
from .spell_checker_parser import SpellParser
from .checked import Checked
from .headers import *
from .check_python_version import check_python_version

class AsyncSpellChecker:
    def __init__(self) -> None:
        # 파이썬 버전 검사
        check_python_version()
        
        # 매개 변수 정의
        self.token_url = token_url
        self.spell_checker_url = spell_checker_url
        self.token_requests_headers = token_requests_headers
        self.spell_checker_requests_headers = spell_checker_requests_headers
        
        # 토큰 초기화
        self.token = None
        
        # 세션 생성
        self.session = aiohttp.ClientSession()
        
        # Parse 생성
        self.speel_parser = SpellParser()
        
    
    # 토큰 초기화
    async def initialize_token(self):
        # 토큰을 생성합니다.
        self.token = await self._get_token()
        
    # 토큰 생성을 요청합니다.
    async def _get_token(self):
        # 토큰 요청
        async with self.session.get(self.token_url, headers=self.token_requests_headers) as response:
            response.raise_for_status()  # 상태 코드가 200이 아닐 경우 예외 발생
            
            # 토큰 업데이트
            return self._token_update(await response.text())
    
    # 받은 토큰 텍스트를 Parse (구문 분석) 합니다.
    def _token_update(self, token):
        match = re.search('passportKey=([a-zA-Z0-9]+)', token)
        # parse.unquote는 URL 디코딩 함수입니다.
        return parse.unquote(match.group(1)) if match is not None else None


    # 맞춤법 검사기 요청 함수입니다.
    async def _get_response(self, text):
        spell_checker_payload.update({
            "passportKey" : self.token,
            "q": text
        })
        
        
        # 맞춤법 검사기에 텍스트 교정 요청을 보냅니다.
        async with self.session.get(self.spell_checker_url, headers=self.spell_checker_requests_headers, params=spell_checker_payload) as response:
            response.raise_for_status()  # 상태 코드가 200이 아닐 경우 예외 발생
            return await response.json() # json 타입으로 리턴

    
    # 매개변수로 받은 텍스트를 맞춤법 검사를 진행합니다.
    async def spell_check(self, text, async_delay, is_output=False):
        # 필요한 리스트 초기화
        spell_check_results = {
            "spell_checked": [],
            "passed_time": [],
            "original_text": [],
            "spell_checked_error": {} # 텍스트 길이가 500자가 넘어간 경우 처리
        }

        
        # 리스트나 튜플을 texts 변수에 할당, 단일 텍스트를 리스트로 변환
        texts = text if isinstance(text, (list, tuple)) else [text]
        texts_len = len(texts)
        
        for idx, txt in enumerate(texts):
            if len(txt) < 500: # 네이버 맞춤법 검사기 최대로 지원하는 글자수.
                start_time = time.time()
                spell_check_results["spell_checked"].append(await self._get_response(txt))  # 응답 가져와서 저장
                spell_check_results["passed_time"].append(time.time() - start_time)
                spell_check_results["original_text"].append(txt)
                # 텍스트 검사 개수가 1개 보다 많으면 대기.
                await asyncio.sleep(async_delay) if texts_len > 1 else await asyncio.sleep(0)
            
            else:
                spell_check_results["spell_checked_error"][idx] = Checked(result=False)
                

        # 동기적으로 각 텍스트에 대해 파싱 수행
        parsed_results = [self.speel_parser.parse(spell_text, original_text, passed_time) for (spell_text, original_text, passed_time) in zip(spell_check_results["spell_checked"], spell_check_results["original_text"], spell_check_results["passed_time"])]
        
        # 글자수가 500 글자가 넘어간거는 오류로 처리하고 동기적으로 삽입
        updated_results = self._insert_spell_checked_errors(spell_check_results, parsed_results)
        self._results_output(updated_results, is_output)
        return self._process_results(updated_results)



    def _insert_spell_checked_errors(self, spell_check_results, parse_results):
        for k, v in spell_check_results["spell_checked_error"].items():
            parse_results.insert(k, v)
        return parse_results

    def _process_results(self, updated_results):
        # 업데이트된 결과 개수에 따라 반환 방식 결정
        return updated_results[0] if len(updated_results) == 1 else updated_results
    

    def _results_output(self, texts, is_output):
        if is_output:
            print(texts[0]) if len(texts) == 1 else print(texts)
            return None
        return None


    # 세션 종료.
    async def close(self):
        await self.session.close()