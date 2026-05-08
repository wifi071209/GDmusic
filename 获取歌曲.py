#该脚本基于GD音乐台API编写


import requests

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
song_id = search_song('好运来')#输名字
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

# 假设从上一步得到歌曲ID是 '123456'
if song_id:
    download_link = get_song_url(song_id)   # 如果拿到了链接，就可以用 requests 或其它库来下载文件了
    if download_link:
        print(f"可以开始下载: {download_link}")

with open("好运来.mp3","wb") as f:#输你的歌名
    f.write(requests.get(download_link).content)