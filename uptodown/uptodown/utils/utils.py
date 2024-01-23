import os

def create_dir(main_path: str, result: dict) -> str:
    try: os.makedirs(f'{main_path}/data_raw/uptodown/{result["detail_application"]["platform"]}/{result["type"]}/{vname(result["reviews_name"].lower())}/json/detail')
    except Exception: ...
    finally: return f'{main_path}/data_raw/uptodown/{result["detail_application"]["platform"]}/{result["type"]}/{vname(result["reviews_name"].lower())}/json'
    ...

def convert_path(path: str) -> str:
    
    path = path.split('/')
    path[1] = 'data_clean'
    return '/'.join(path)
    ...

def vname(name: str) -> str:
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '+', '=', '&', '%', '@', '#', '$', '^', '[', ']', '{', '}', '`', '~', '\n']
    falid = ''.join(char if char not in invalid_chars else '' for char in name)
    
    return falid.replace(" ", "_").replace('__', '_')