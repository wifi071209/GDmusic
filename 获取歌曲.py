#该脚本基于GD音乐台(music.gdstudio.xyz)API编写
#original author:Yifan Wang
#github:wifi071209

import requests
from pathlib import Path
def search_song(song_name, source='netease'):
    search_url = "https://music-api.gdstudio.xyz/api.php"
    params = {
        'types': 'search',
        'source': source,
        'name': song_name,
        'count': 15,
        'pages': 1
    }
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        results = response.json()
        # 假设我们取第一首歌来做后续操作
        if results:
            first_song = results[0]
            song_id = first_song.get('id')
            print(f"找到歌曲: {first_song.get('name')} - {first_song.get('artist')}")
            print(f"歌曲ID: {song_id}")
            return song_id
        else:
            print("未找到相关歌曲。")
            return None
    except requests.exceptions.RequestException as e:
        print(f"搜索请求出错: {e}")
        return None

# 执行搜索
name = input("请输入要搜索的歌曲名称: ")
song_id = search_song(name)
def get_song_url(song_id, source='netease', bitrate='320'):#在这里改音质可选值有 128、192、320，其中 740 和 999 一般代表无损
    download_url = "https://music-api.gdstudio.xyz/api.php"
    params = {
        'types': 'url',
        'source': source,
        'id': song_id,
        'br': bitrate
    }
    try:
        response = requests.get(download_url, params=params)
        response.raise_for_status()
        data = response.json()
        # 从API返回的数据中提取下载链接和文件大小
        mp3_url = data.get('url')
        file_size = data.get('size')
        actual_bitrate = data.get('br')
        print(f"获取到下载链接: {mp3_url}")
        print(f"文件大小: {int(file_size)/1024/1024:.2f} MB")
        print(f"实际音质: {actual_bitrate} kbps")
        return mp3_url
    except requests.exceptions.RequestException as e:
        print(f"获取链接请求出错: {e}")
        return None

from pathlib import Path


if song_id:
    download_link = get_song_url(song_id)
    if download_link:
        print(f"可以开始下载: {download_link}")

       
        music_dir = Path("音乐")
       
        music_dir.mkdir(exist_ok=True)

        
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '.', '-', '_')).rstrip()
        if not safe_name:
            safe_name = "song"

        file_path = music_dir / f"{safe_name}.mp3"
        with open(file_path, "wb") as f:
            f.write(requests.get(download_link).content)

        print(f"歌曲已保存到: {file_path}")
