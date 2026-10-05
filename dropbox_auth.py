"""Refresh-token authentication and non-sensitive error diagnostics."""
import os


def create_dropbox_client(factory, environ=None):
    env = os.environ if environ is None else environ
    refresh = env.get('DROPBOX_REFRESH_TOKEN', '').strip()
    key = env.get('DROPBOX_APP_KEY', '').strip()
    secret = env.get('DROPBOX_APP_SECRET', '').strip()
    access = env.get('DROPBOX_ACCESS_TOKEN', '').strip()
    if refresh:
        if not key or not secret:
            raise ValueError('DROPBOX_REFRESH_TOKEN 사용 시 DROPBOX_APP_KEY와 DROPBOX_APP_SECRET이 필요합니다.')
        return factory(oauth2_refresh_token=refresh, app_key=key, app_secret=secret)
    if access:
        return factory(oauth2_access_token=access)
    raise ValueError('Dropbox 인증 설정이 없습니다. 갱신 토큰 또는 액세스 토큰을 설정하세요.')


def safe_error_code(error):
    detail = getattr(error, 'error', None)
    for code in ('expired_access_token', 'invalid_access_token', 'missing_scope',
                 'user_suspended', 'route_access_denied'):
        method = getattr(detail, f'is_{code}', None)
        if callable(method) and method():
            return code
    return type(error).__name__


def user_error_message(stage, error):
    code = safe_error_code(error)
    if stage == 'dropbox_upload':
        messages = {
            'expired_access_token': 'Dropbox 연결 토큰이 만료되었습니다. 자동 갱신 연결을 설정해야 합니다.',
            'invalid_access_token': 'Dropbox 연결 토큰이 유효하지 않습니다. 계정 연결을 다시 확인해야 합니다.',
            'missing_scope': 'Dropbox 앱에 파일 저장 권한이 부족합니다. 기존 앱의 권한을 확인해야 합니다.',
        }
        return messages.get(code, 'Dropbox 저장에 실패했습니다. 서버 로그의 오류 코드를 확인해 주세요.')
    if stage == 'gpt_analysis':
        return 'GPT 정리에 실패했습니다. 서버의 OpenAI 키·모델·사용 한도를 확인해 주세요.'
    if stage == 'local_save':
        return '임시 파일 저장에 실패했습니다. 서버 저장 공간을 확인해 주세요.'
    if stage == 'telegram_reply':
        return '저장은 완료됐지만 텔레그램 응답을 보내지 못했습니다.'
    return '요청 처리에 실패했습니다. 서버 로그의 오류 코드를 확인해 주세요.'
