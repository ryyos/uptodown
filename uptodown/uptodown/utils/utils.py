import os

def __create_dir(main_path: str, result: dict) -> str:
    try: os.makedirs(f'{main_path}/data_raw/uptodown/{result["detail_application"]["platform"]}/{result["detail_application"]["type"]}/{vname(result["reviews_name"].lower())}/json/detail')
    except Exception: ...
    finally: return f'{main_path}/data_raw/uptodown/{result["detail_application"]["platform"]}/{result["detail_application"]["type"]}/{vname(result["reviews_name"].lower())}/json'
    ...

def __convert_path( path: str) -> str:
    
    path = path.split('/')
    path[1] = 'data_clean'
    return '/'.join(path)
    ...

def vname(name: str) -> str:
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '+', '=', '&', '%', '@', '#', '$', '^', '[', ']', '{', '}', '`', '~']
    falid = ''.join(char if char not in invalid_chars else '' for char in name)
    
    return falid.replace(" ", "_").replace('__', '_')