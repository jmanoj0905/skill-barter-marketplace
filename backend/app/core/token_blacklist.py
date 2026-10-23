# Temporary in-memory blacklist
blacklisted_tokens = set()

def blacklist_token(token: str):
    blacklisted_tokens.add(token)

def is_token_blacklisted(token: str):
    return token in blacklisted_tokens