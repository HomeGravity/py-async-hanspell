import xml.etree.ElementTree as ET
from collections import OrderedDict
import re


from . import __version__
from .check_result import CheckResult
from .checked import Checked

def remove_tag(text):
    # 정규 표현식: '<...>'와 그 안의 내용을 모두 삭제합니다.
    return re.sub(r'<[^>]*>', '', text, count=1)

class SpellParser:
    def __init__(self) -> None:
        self.tag_mapping = {
            '<em class=\'red_text\'>': '<red>',
            '<em class=\'green_text\'>': '<green>',
            '<em class=\'violet_text\'>': '<violet>',
            '<em class=\'blue_text\'>': '<blue>',
            '</em>': '<end>'
        }
        
        self.tag_to_result = {
            '<red>': CheckResult.WRONG_SPELLING,
            '<green>': CheckResult.WRONG_SPACING,
            '<violet>': CheckResult.AMBIGUOUS,
            '<blue>': CheckResult.STATISTICAL_CORRECTION
        }
    
    
    def parse(self, data, text, passed_time):
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
        return self._check_words(result, words)  # 동기적 체크 호출
        
    def _remove_tags(self, text):
        wrapped_text = f'<content>{text}</content>'
        result = ''.join(ET.fromstring(wrapped_text.replace("<br>", "")).itertext())
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
        
        # 정규 표현식을 사용하여 태그를 대체
        pattern = re.compile('|'.join(self.tag_mapping.keys()))
        return pattern.sub(lambda match : self.tag_mapping[match.group(0)], html)

                
    def _check_words(self, result, words):
        # 각 단어를 체크하고 결과를 OrderedDict에 저장
        for word in words:
            result['words'][remove_tag(word)] = self._check_word(word)

        return Checked(**result)

    def _check_word(self, word):
        # 각 단어의 상태를 체크합니다.
        for tag, check_result in self.tag_to_result.items():
            if word.startswith(tag):
                return check_result

        return CheckResult.PASSED