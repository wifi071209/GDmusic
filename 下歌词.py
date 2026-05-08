import requests
import re
import os
import time

# ------------------------------------------------------------
# 配置区域
# ------------------------------------------------------------
# 稳定音乐源（根据官方文档建议：netease、kuwo、joox、bilibili）
DEFAULT_SOURCE = "netease"
# 搜索返回条数（默认20）
SEARCH_COUNT = 20
# 请求间隔（秒），避免触发限流（5分钟内不超过50次 -> 平均6秒一次）
REQUEST_INTERVAL = 0.5

# API 基础地址
API_BASE = "https://music-api.gdstudio.xyz/api.php"

# ------------------------------------------------------------
# 工具函数：发送请求 + 简单限流
# ------------------------------------------------------------
_last_request_time = 0

def _api_call(params):
    """发送 GET 请求到 API，自动控制频率"""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < REQUEST_INTERVAL:
        time.sleep(REQUEST_INTERVAL - elapsed)
    try:
        resp = requests.get(API_BASE, params=params, timeout=10)
        resp.raise_for_status()
        _last_request_time = time.time()
        return resp.json()
    except Exception as e:
        print(f"API 请求失败: {e}")
        return None

# ------------------------------------------------------------
# 1. 搜索歌曲
# ------------------------------------------------------------
def search_songs(keyword, source=DEFAULT_SOURCE, count=SEARCH_COUNT, page=1):
    """
    搜索歌曲，返回包含歌词ID的歌曲列表
    :return: list of dict, 每个dict包含 id, name, artist, album, lyric_id 等
    """
    params = {
        "types": "search",
        "source": source,
        "name": keyword,
        "count": count,
        "pages": page
    }
    print(f"正在搜索: {keyword} (音源: {source})")
    data = _api_call(params)
    if not data:
        return []
    # 官方文档返回的是一个列表，每个元素是一首歌
    if isinstance(data, list):
        songs = []
        for item in data:
            # 提取关键字段
            song = {
                "id": item.get("id"),
                "name": item.get("name"),
                "artist": item.get("artist"),      # 可能是列表或字符串
                "album": item.get("album"),
                "pic_id": item.get("pic_id"),
                "lyric_id": item.get("lyric_id"),  # 歌词ID，通常等于曲目ID
                "source": source
            }
            songs.append(song)
        print(f"找到 {len(songs)} 首歌曲")
        return songs
    else:
        print("返回格式异常")
        return []

# ------------------------------------------------------------
# 2. 获取歌词
# ------------------------------------------------------------
def get_lyrics(lyric_id, source=DEFAULT_SOURCE):
    """
    通过歌词ID和音源获取歌词内容
    :return: dict {"lyric": "...", "tlyric": "..."} 或 None
    """
    params = {
        "types": "lyric",
        "source": source,
        "id": lyric_id
    }
    print(f"正在获取歌词 (ID: {lyric_id})...")
    data = _api_call(params)
    if not data:
        return None
    # 官方返回包含 lyric 和 tlyric 字段
    return {
        "lyric": data.get("lyric", ""),
        "tlyric": data.get("tlyric", "")
    }

# ------------------------------------------------------------
# 3. 保存歌词到文件
# ------------------------------------------------------------
def save_lyrics_to_file(lyrics_dict, song_name, artist, output_dir="."):
    """
    保存原歌词和翻译歌词为 .lrc 文件
    lyrics_dict: {"lyric": "...", "tlyric": "..."}
    """
    if not lyrics_dict["lyric"]:
        print("警告: 未获取到原歌词")
        return None

    # 清理文件名中的非法字符
    def safe_filename(text):
        return re.sub(r'[\\/*?:"<>|]', "", text)

    base_name = safe_filename(f"{song_name} - {artist}")
    # 保存原歌词
    lyric_file = os.path.join(output_dir, f"{base_name}.lrc")
    with open(lyric_file, "w", encoding="utf-8") as f:
        f.write(lyrics_dict["lyric"])
    print(f"✅ 原歌词已保存: {lyric_file}")

    # 如果有翻译歌词，另外保存
    if lyrics_dict.get("tlyric"):
        trans_file = os.path.join(output_dir, f"{base_name}_trans.lrc")
        with open(trans_file, "w", encoding="utf-8") as f:
            f.write(lyrics_dict["tlyric"])
        print(f"✅ 翻译歌词已保存: {trans_file}")
        return lyric_file, trans_file
    return lyric_file, None

# ------------------------------------------------------------
# 4. 完整流程：搜索 → 选择 → 下载歌词
# ------------------------------------------------------------
def download_lyrics(keyword, source=DEFAULT_SOURCE, song_index=0, output_dir="."):
    """
    主函数：根据关键词搜索，下载第 song_index 首歌的歌词（默认第一首）
    """
    # 1. 搜索
    songs = search_songs(keyword, source)
    if not songs:
        print("未找到任何歌曲，请检查关键词或音源。")
        return

    # 2. 选择歌曲（如果 song_index 超出范围，取最后一首）
    if song_index >= len(songs):
        song_index = -1
        print(f"索引超出范围，自动选择最后一首")
    song = songs[song_index]

    # 显示选中歌曲的信息
    artist_display = song["artist"]
    if isinstance(artist_display, list):
        artist_display = ", ".join(artist_display)
    print(f"\n选中歌曲: {song['name']} - {artist_display}")
    print(f"曲目ID: {song['id']} | 歌词ID: {song['lyric_id']}")

    # 3. 获取歌词（使用 lyric_id，若无则尝试用曲目ID）
    lyric_id = song.get("lyric_id")
    if not lyric_id:
        print("未返回 lyric_id，尝试使用曲目ID...")
        lyric_id = song["id"]
    if not lyric_id:
        print("错误: 无法获取歌词ID")
        return

    lyrics = get_lyrics(lyric_id, song["source"])
    if not lyrics or not lyrics["lyric"]:
        print("未获取到歌词内容，可能该歌曲无歌词或音源不支持。")
        return

    # 4. 保存
    save_lyrics_to_file(lyrics, song["name"], artist_display, output_dir)

# ------------------------------------------------------------
# 命令行入口
# ------------------------------------------------------------
if __name__ == "__main__":
    # ========== 在这里修改参数 ==========
    SEARCH_KEYWORD = "好运来"      # 要搜索的歌曲名/歌手名
    MUSIC_SOURCE = "netease"         # 音源: netease, kuwo, joox, bilibili 等
    OUTPUT_DIR = "."                 # 保存目录，当前目录
    SONG_INDEX = 0                   # 选第几首（0表示第一首）
    # =================================

    # 遵守官方限流: 5分钟内不超过50次请求，我们已经在 api_call 中加入了0.5秒间隔
    print("=== GD音乐台 歌词下载工具 ===")
    print(f"官方限流提醒: 5分钟内不超过50次请求 (已自动间隔 {REQUEST_INTERVAL} 秒)")

    download_lyrics(SEARCH_KEYWORD, MUSIC_SOURCE, SONG_INDEX, OUTPUT_DIR)