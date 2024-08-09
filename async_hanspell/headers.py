# 네이버 토큰 요청 URL
token_url = "https://search.naver.com/search.naver?where=nexearch&sm=top_sug.pre&fbm=0&acr=1&acq=%EB%84%A4%EC%9D%B4%EB%B2%84+%EB%A7%9E&qdt=0&ie=utf8&query=%EB%84%A4%EC%9D%B4%EB%B2%84+%EB%A7%9E%EC%B6%A4%EB%B2%95+%EA%B2%80%EC%82%AC%EA%B8%B0"

# 네이버 맞춤법 검사기 API URL
spell_checker_url = "https://m.search.naver.com/p/csearch/ocontent/util/SpellerProxy"

# 토큰(passportKey) 요청 헤더
token_requests_headers = {
    "User-Agent:" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer" : "https://www.naver.com/"
}

# 맞춤법 검사기 요청 헤더
spell_checker_requests_headers = {
    "User-Agent:" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer" : "https://search.naver.com/search.naver?where=nexearch&sm=top_sug.pre&fbm=0&acr=1&acq=%EB%84%A4%EC%9D%B4%EB%B2%84+%EB%A7%9E&qdt=0&ie=utf8&query=%EB%84%A4%EC%9D%B4%EB%B2%84+%EB%A7%9E%EC%B6%A4%EB%B2%95+%EA%B2%80%EC%82%AC%EA%B8%B0"
}


# 요청 페이로드를 작성합니다.
spell_checker_payload = {
    "passportKey": "",
    "q": "",
    "color_blindness": 0
}