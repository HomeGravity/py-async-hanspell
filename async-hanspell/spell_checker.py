from headers import *
import aiohttp
import asyncio
import re
from cachetools import TTLCache
from urllib import parse
import time
from collections import OrderedDict
import xml.etree.ElementTree as ET
from check_result import CheckResult
from checked import Checked

# 토큰 요청을 줄이기 위해 캐시로 저장합니다.
cache = TTLCache(maxsize=10, ttl=3600)

def remove_tags_and_contents(text):
    # 정규 표현식: '<...>'와 그 안의 내용을 모두 삭제합니다.
    return re.sub(r'<[^>]*>', '', text, count=1)

class AsyncSpellChecker:
    def __init__(self) -> None:
        # 매개 변수 정의
        self.token_url = token_url
        self.spell_checker_url = spell_checker_url
        self.token_requests_headers = token_requests_headers
        self.spell_checker_requests_headers = spell_checker_requests_headers
        
        # 토큰
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
    
    
    # 토큰 생성을 요청합니다.
    async def _get_token(self):
        # 토큰 요청
        async with self.session.get(self.token_url, headers=self.token_requests_headers) as response:
            response.raise_for_status()  # 상태 코드가 200이 아닐 경우 예외 발생
            token_text = await response.text()
            
            # 토큰 업데이트
            return await self._token_update(token_text)
    
    # 받은 토큰 텍스트를 Parse (구문 분석) 합니다.
    async def _token_update(self, token):
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

    async def _initialize_token(self):
        # 토큰을 생성합니다.
        await self._create_token() if self.token is None else await self._read_token() # 토큰을 불러옵니다.
    
    async def _text_length(self, text):
        return True if len(text) > 500 else False
    
    # 매개변수로 받은 텍스트를 맞춤법 검사를 진행합니다.
    async def spell_check(self, text, async_delay):
        # 리스트나 튜플을 texts 변수에 할당, 단일 텍스트를 리스트로 변환
        texts = text if isinstance(text, (list, tuple)) else [text]
        await self._initialize_token()  # 토큰 초기화
        
        for txt in texts:
            if await self._text_length(txt):
                print(f"텍스트가 500자가 넘습니다. ({len(txt):,.0f})")
                return None
        
        spell_checked_data = []
        passed_time_data = []
        
        for txt in texts:
            start_time = time.time()
            await self._initialize_token()  # 각 텍스트에 대해 토큰 초기화
            spell_checked_data.append(await self._get_response(txt))  # 응답 가져와서 저장
            passed_time_data.append(time.time() - start_time)
            await asyncio.sleep(async_delay)  # 대기

        # 비동기적으로 각 텍스트에 대해 파싱 수행
        parse_results = await asyncio.gather(
            *[self._parse(spell_text, original_text, passed_time) for (spell_text, original_text, passed_time) in zip(spell_checked_data, texts, passed_time_data)]
        )
        
        return parse_results  # 결과 반환
    
    async def spell_check_output(self, data, output_mode=1):
        for spell in data:
            # 기본 출력 모드
            output = spell.only_checked()

            if output_mode == 1:
                output = spell  # output_mode가 1일 경우 spell을 사용
            elif output_mode == 2 and hasattr(spell, 'as_dict'):
                output = spell.as_dict()  # output_mode가 2일 경우 as_dict() 호출

            print(output)  # 최종 출력
                
        

    async def _parse(self, data, text, passed_time):
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
        return await self._check_words(result, words)  # 비동기 체크 호출
    
    def _remove_tags(self, text):
        text = u'<content>{}</content>'.format(text).replace('<br>','')
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
                word = u'{}{}'.format(tmp, word)
            
            if word[-5:] == '<end>':
                word = word.replace('<end>', '')
                tmp = ''

            words.append(word)

    def _replace_tags(self, html):
        return html.replace('<em class=\'green_text\'>', '<green>') \
                .replace('<em class=\'red_text\'>', '<red>') \
                .replace('<em class=\'violet_text\'>', '<violet>') \
                .replace('<em class=\'blue_text\'>', '<blue>') \
                .replace('</em>', '<end>')
                
    async def _check_words(self, result, words):
        # 비동기적으로 각 단어를 체크합니다.
        check_results = await asyncio.gather(
            *[self._check_word(word) for word in words]
        )
        
        # 결과를 원하는 형식으로 변환
        for word, check_result in zip(words, check_results):
            result['words'][remove_tags_and_contents(word)] = check_result

        return Checked(**result)

    async def _check_word(self, word):
        # 각 단어의 상태를 비동기적으로 체크합니다.
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
            


async def main1():
    SpellChecker = AsyncSpellChecker()
    tasks = [
        SpellChecker.spell_check(
            text="안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다.", 
            async_delay=2
        ),
        
        SpellChecker.spell_check(
            text="안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다.", 
            async_delay=2
        )
    ]

    # 비동기 작업을 병렬로 실행하고 완료된 순서대로 결과를 처리
    for completed in asyncio.as_completed(tasks):
        result = await completed
        if result is not None:
            await SpellChecker.spell_check_output(result)

    # 세션 종료
    await SpellChecker.close()


async def main2():
    SpellChecker = AsyncSpellChecker()
    
    word1 = await SpellChecker.spell_check(
            text=["안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다." *50, "안녕"],
            async_delay=2
    )

    word2 = await SpellChecker.spell_check(
            text="안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다.", 
            async_delay=2
    )

    word3 = await SpellChecker.spell_check(
            text="안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다.", 
            async_delay=2
    )
    
    for word in [word1, word2, word3]:
        if word is not None:
            await SpellChecker.spell_check_output(word)

    # 세션 종료
    await SpellChecker.close()

# 비동기 이벤트 루프 실행
if __name__ == '__main__':
    # asyncio.run(main())
    asyncio.run(main2())
    