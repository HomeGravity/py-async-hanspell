import aiohttp
import asyncio
import re
from cachetools import TTLCache
from urllib import parse
import time
from collections import OrderedDict
import xml.etree.ElementTree as ET

from . import __version__
from .headers import *
from .check_result import CheckResult
from .checked import Checked
from .check_python_version import check_python_version

# 토큰 요청을 줄이기 위해 캐시로 저장합니다.
cache = TTLCache(maxsize=10, ttl=3600)

def remove_tag(text):
    # 정규 표현식: '<...>'와 그 안의 내용을 모두 삭제합니다.
    return re.sub(r'<[^>]*>', '', text, count=1)

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
        
    # 토큰을 생성합니다.
    async def _create_token(self):
        self.token = await self._get_token()
    
    async def _read_token(self):
        # 토큰이 있는경우 > 계속 사용
        try:
            self.token = cache.get('PASSPORT_TOKEN')
            
        # 토큰이 없는경우 > 새로 생성
        except KeyError:
            self.token = await self._get_token()
    
    # 토큰 값 업데이트 및 재사용 홤수
    async def initialize_token(self):
        # 토큰을 생성합니다.
        await self._create_token() if self.token is None else await self._read_token() # 토큰을 불러옵니다.
    
    # 토큰 생성을 요청합니다.
    async def _get_token(self):
        # 토큰 요청
        async with self.session.get(self.token_url, headers=self.token_requests_headers) as response:
            response.raise_for_status()  # 상태 코드가 200이 아닐 경우 예외 발생
            token_text = await response.text()
            
            # 토큰 업데이트
            return self._token_update(token_text)
    
    # 받은 토큰 텍스트를 Parse (구문 분석) 합니다.
    def _token_update(self, token):
            match = re.search('passportKey=([a-zA-Z0-9]+)', token)
            if match is not None:
                # parse.unquote는 URL 디코딩 함수입니다.
                token_update  = parse.unquote(match.group(1))
                cache['PASSPORT_TOKEN'] = token_update
                
            return token_update 


    # 맞춤법 검사기 요청 함수입니다.
    async def _get_response(self, text):
        spell_checker_payload.update({
            "passportKey" : self.token,
            "q": text
        })
        
        
        # 맞춤법 검사기에 텍스트 교정 요청을 보냅니다.
        async with self.session.get(self.spell_checker_url, headers=self.spell_checker_requests_headers, params=spell_checker_payload) as response:
            response.raise_for_status()  # 상태 코드가 200이 아닐 경우 예외 발생
            return await response.json()

    def insert_spell_checked_errors(self, spell_check_results, parse_results):
        for k, v in spell_check_results["spell_checked_error"].items():
            parse_results.insert(k, v)
        return parse_results

    def process_results(self, updated_results):
        # 업데이트된 결과의 길이에 따라 반환 방식 결정
        if len(updated_results) == 1:
            return updated_results[0]  # 단일 결과 반환

        return updated_results  # 여러 결과를 리스트 형태로 반환

    
    # 매개변수로 받은 텍스트를 맞춤법 검사를 진행합니다.
    async def spell_check(self, text, async_delay):
        # 필요한 리스트 초기화
        spell_check_results = {
            "spell_checked": [],
            "passed_time": [],
            "original_text": [],
            "spell_checked_error": {} # 텍스트 길이가 500자가 넘어간 경우 처리
        }

        
        # 리스트나 튜플을 texts 변수에 할당, 단일 텍스트를 리스트로 변환
        texts = text if isinstance(text, (list, tuple)) else [text]
        
        for idx, txt in enumerate(texts):
            if len(txt) < 500: # 네이버 맞춤법 검사기 최대로 지원하는 글자수.
                start_time = time.time()
                await self.initialize_token()  # 반복할때마다 토큰을 재초기화 (한번 초기화하면 캐시에 저장된게 불러와짐.)
                spell_check_results["spell_checked"].append(await self._get_response(txt))  # 응답 가져와서 저장
                spell_check_results["passed_time"].append(time.time() - start_time)
                spell_check_results["original_text"].append(txt)
            
            else:
                spell_check_results["spell_checked_error"][idx] = Checked(result=False)
                
            # 1 보다 높으면.
            if len(texts) > 1:
                await asyncio.sleep(async_delay)  # 대기


        # 동기적으로 각 텍스트에 대해 파싱 수행
        parsed_results = [self._parse(spell_text, original_text, passed_time) for (spell_text, original_text, passed_time) in zip(spell_check_results["spell_checked"], spell_check_results["original_text"], spell_check_results["passed_time"])]
        
        
        # 글자수가 500 글자가 넘어간거는 오류로 처리하고 동기적으로 삽입
        updated_results = self.insert_spell_checked_errors(spell_check_results, parsed_results)

        return self.process_results(updated_results)


    def _parse(self, data, text, passed_time):
        html = data['message']['result']['html']
        result = {
            'result': True,
            'original': text,
            'checked': self._remove_tags(html),
            'errors': data['message']['result']['errata_count'],
            'time': passed_time,
            'words': OrderedDict(),
        }
        
        words = []
        self._extract_words(words, html)
        return self._check_words(result, words)  # 비동기 체크 호출
    
    def _remove_tags(self, text):
        text = '<content>{}</content>'.format(text).replace('<br>','')
        result = ''.join(ET.fromstring(text).itertext())

        return result
        
    def _extract_words(self, words, html):
        items = self._replace_tags(html).split(' ')
        tmp = ''
        for word in items:
            if tmp == '' and word[:1] == '<':
                pos = word.find('>') + 1
                tmp = word[:pos]
            elif tmp != '':
                word = f'{tmp}{word}'
            
            if word.endswith("<end>"):
                word = word.replace('<end>', '')
                tmp = ''

            words.append(word)

    def _replace_tags(self, html):
        return html.replace('<em class=\'green_text\'>', '<green>') \
                .replace('<em class=\'red_text\'>', '<red>') \
                .replace('<em class=\'violet_text\'>', '<violet>') \
                .replace('<em class=\'blue_text\'>', '<blue>') \
                .replace('</em>', '<end>')
                
    def _check_words(self, result, words):
        # 동기적으로 각 단어를 체크합니다.
        check_results = [self._check_word(word) for word in words]
        
        # 결과를 원하는 형식으로 변환
        for word, check_result in zip(words, check_results):
            result['words'][remove_tag(word)] = check_result

        return Checked(**result)

    def _check_word(self, word):
        # 각 단어의 상태를 체크합니다.
        
        if word.startswith('<red>'):
            return CheckResult.WRONG_SPELLING
        
        elif word.startswith('<green>'):
            return CheckResult.WRONG_SPACING
        
        elif word.startswith('<violet>'):
            return CheckResult.AMBIGUOUS
        
        elif word.startswith('<blue>'):
            return CheckResult.STATISTICAL_CORRECTION
        else:
            return CheckResult.PASSED

    # 세션 종료.
    async def close(self):
        await self.session.close()