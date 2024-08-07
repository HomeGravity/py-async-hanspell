class PythonVersionError(Exception):
    pass

def check_python_version():
    import sys
    if sys.version_info < (3, 10):
        raise PythonVersionError("파이썬 버전 3.10 이상이 필요합니다.")