#!/usr/bin/env python3
"""
Pexels视频和图片素材获取器
支持自动搜索、下载、缓存高质量免费素材
"""

import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
import time
from datetime import datetime


class PexelsFetcher:
    """Pexels素材获取器 (视频+图片)"""

    def __init__(self, config_path: str = "config/settings.json"):
        """
        初始化Pexels获取器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)

        # Pexels API配置
        pexels_config = self.config.get("pexels", {})
        self.api_key = pexels_config.get("api_key") or os.getenv("PEXELS_API_KEY")

        if not self.api_key:
            print("⚠️  未配置Pexels API密钥")
            print("   请访问 https://www.pexels.com/api/ 免费申请")
            print("   然后在 config/settings.json 中添加 pexels.api_key")

        # API端点
        self.video_api_url = "https://api.pexels.com/videos/search"
        self.photo_api_url = "https://api.pexels.com/v1/search"

        # 请求头
        self.headers = {
            "Authorization": self.api_key
        }

        # 素材保存路径
        self.video_dir = Path(self.config["paths"]["materials"]) / "videos" / "pexels"
        self.image_dir = Path(self.config["paths"]["materials"]) / "images" / "pexels"
        self.video_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)

        # 元数据缓存
        self.cache_file = Path(self.config["paths"]["materials"]) / "pexels_cache.json"
        self.cache = self._load_cache()

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载配置失败: {str(e)}")
            return {"paths": {"materials": "./materials"}, "pexels": {}}

    def _load_cache(self) -> dict:
        """加载元数据缓存（V5.4：添加下载记录）"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    # 确保包含下载记录字段
                    if "downloaded_materials" not in cache:
                        cache["downloaded_materials"] = {}
                    return cache
            except:
                return {"videos": {}, "photos": {}, "downloaded_materials": {}}
        return {"videos": {}, "photos": {}, "downloaded_materials": {}}

    def _save_cache(self):
        """保存元数据缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存缓存失败: {str(e)}")

    def _record_download(self, material_id: str, local_path: str, material_type: str):
        """
        记录已下载的素材（V5.4新增）

        Args:
            material_id: 素材ID（格式：pexels_video_123 或 pexels_photo_456）
            local_path: 本地文件路径
            material_type: 素材类型 (video/photo)
        """
        self.cache["downloaded_materials"][material_id] = {
            "local_path": local_path,
            "type": material_type,
            "downloaded_at": time.time()
        }
        self._save_cache()

    def _check_downloaded(self, material_id: str) -> Optional[str]:
        """
        检查素材是否已下载（V5.4新增）

        Args:
            material_id: 素材ID

        Returns:
            本地文件路径（如果已下载且文件存在），否则返回None
        """
        downloaded = self.cache.get("downloaded_materials", {}).get(material_id)
        if downloaded:
            local_path = downloaded.get("local_path")
            if local_path and os.path.exists(local_path):
                return local_path
        return None

    def search_videos(
        self,
        query: str,
        per_page: int = 5,
        orientation: str = "landscape",
        size: str = "medium"
    ) -> List[Dict[str, Any]]:
        """
        搜索Pexels视频

        Args:
            query: 搜索关键词 (英文效果最佳)
            per_page: 每页结果数 (最多15)
            orientation: 方向 (landscape/portrait/square)
            size: 尺寸 (large/medium/small)

        Returns:
            视频信息列表
        """
        if not self.api_key:
            print("❌ Pexels API密钥未配置")
            return []

        print(f"\n🔍 搜索Pexels视频: '{query}'")

        # 检查缓存
        cache_key = f"{query}_{orientation}_{size}"
        if cache_key in self.cache["videos"]:
            cached = self.cache["videos"][cache_key]
            # 缓存有效期7天
            if time.time() - cached["timestamp"] < 7 * 86400:
                print(f"✅ 使用缓存 ({len(cached['results'])}个结果)")
                return cached["results"]

        try:
            params = {
                "query": query,
                "per_page": min(per_page, 15),
                "orientation": orientation,
                "size": size
            }

            response = requests.get(
                self.video_api_url,
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                videos = data.get("videos", [])

                # 提取关键信息
                results = []
                for video in videos:
                    video_files = video.get("video_files", [])

                    # 优先选择1080p HD视频
                    hd_file = None
                    for vf in video_files:
                        if vf.get("quality") == "hd" and vf.get("width") == 1920:
                            hd_file = vf
                            break

                    # 降级到SD
                    if not hd_file and video_files:
                        hd_file = video_files[0]

                    if hd_file:
                        results.append({
                            "id": video["id"],
                            "url": hd_file["link"],
                            "width": video["width"],
                            "height": video["height"],
                            "duration": video.get("duration", 0),
                            "image": video.get("image"),
                            "user": video.get("user", {}).get("name", "Unknown"),
                            "quality": hd_file.get("quality", "sd")
                        })

                print(f"✅ 找到 {len(results)} 个视频")

                # 更新缓存
                self.cache["videos"][cache_key] = {
                    "timestamp": time.time(),
                    "results": results
                }
                self._save_cache()

                return results

            elif response.status_code == 429:
                print("⚠️  API请求限制 (每小时200次)")
                return []
            else:
                print(f"❌ API错误: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ 搜索失败: {str(e)}")
            return []

    def search_photos(
        self,
        query: str,
        per_page: int = 5,
        orientation: str = "landscape"
    ) -> List[Dict[str, Any]]:
        """
        搜索Pexels图片

        Args:
            query: 搜索关键词
            per_page: 每页结果数 (最多80)
            orientation: 方向

        Returns:
            图片信息列表
        """
        if not self.api_key:
            print("❌ Pexels API密钥未配置")
            return []

        print(f"\n🔍 搜索Pexels图片: '{query}'")

        # 检查缓存
        cache_key = f"{query}_{orientation}"
        if cache_key in self.cache["photos"]:
            cached = self.cache["photos"][cache_key]
            if time.time() - cached["timestamp"] < 7 * 86400:
                print(f"✅ 使用缓存 ({len(cached['results'])}个结果)")
                return cached["results"]

        try:
            params = {
                "query": query,
                "per_page": min(per_page, 80),
                "orientation": orientation
            }

            response = requests.get(
                self.photo_api_url,
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                photos = data.get("photos", [])

                results = []
                for photo in photos:
                    results.append({
                        "id": photo["id"],
                        "url": photo["src"]["large2x"],  # 高分辨率
                        "original_url": photo["src"]["original"],
                        "width": photo["width"],
                        "height": photo["height"],
                        "photographer": photo.get("photographer", "Unknown"),
                        "avg_color": photo.get("avg_color", "#000000")
                    })

                print(f"✅ 找到 {len(results)} 张图片")

                # 更新缓存
                self.cache["photos"][cache_key] = {
                    "timestamp": time.time(),
                    "results": results
                }
                self._save_cache()

                return results
            else:
                print(f"❌ API错误: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ 搜索失败: {str(e)}")
            return []

    def download_video(
        self,
        video_info: Dict[str, Any],
        keyword: str = "video"
    ) -> Optional[str]:
        """
        下载视频到本地（V5.4：添加下载记录）

        Args:
            video_info: 视频信息字典
            keyword: 关键词(用于文件命名)

        Returns:
            本地文件路径或None
        """
        try:
            video_id = video_info["id"]
            url = video_info["url"]
            material_id = f"pexels_video_{video_id}"

            # V5.4: 先检查下载记录缓存
            cached_path = self._check_downloaded(material_id)
            if cached_path:
                print(f"   ⏭️  已存在（缓存）: {os.path.basename(cached_path)}")
                return cached_path

            # 文件名: keyword_id.mp4
            safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{safe_keyword}_{video_id}.mp4"
            filepath = self.video_dir / filename

            # 检查文件是否已存在
            if filepath.exists():
                print(f"   ⏭️  已存在: {filename}")
                # V5.4: 记录到缓存（补充遗漏的记录）
                self._record_download(material_id, str(filepath), "video")
                return str(filepath)

            print(f"   ⬇️  下载视频: {filename} ({video_info.get('quality', 'sd').upper()})")

            # 下载
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                file_size_mb = filepath.stat().st_size / (1024 * 1024)
                print(f"   ✅ 下载完成: {file_size_mb:.1f} MB")

                # V5.4: 记录下载
                self._record_download(material_id, str(filepath), "video")

                return str(filepath)
            else:
                print(f"   ❌ 下载失败: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"   ❌ 下载错误: {str(e)}")
            return None

    def download_photo(
        self,
        photo_info: Dict[str, Any],
        keyword: str = "photo"
    ) -> Optional[str]:
        """
        下载图片到本地（V5.4：添加下载记录）

        Args:
            photo_info: 图片信息字典
            keyword: 关键词

        Returns:
            本地文件路径或None
        """
        try:
            photo_id = photo_info["id"]
            url = photo_info["url"]  # large2x版本
            material_id = f"pexels_photo_{photo_id}"

            # V5.4: 先检查下载记录缓存
            cached_path = self._check_downloaded(material_id)
            if cached_path:
                print(f"   ⏭️  已存在（缓存）: {os.path.basename(cached_path)}")
                return cached_path

            safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{safe_keyword}_{photo_id}.jpg"
            filepath = self.image_dir / filename

            if filepath.exists():
                print(f"   ⏭️  已存在: {filename}")
                # V5.4: 记录到缓存（补充遗漏的记录）
                self._record_download(material_id, str(filepath), "photo")
                return str(filepath)

            print(f"   ⬇️  下载图片: {filename}")

            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)

                file_size_kb = filepath.stat().st_size / 1024
                print(f"   ✅ 下载完成: {file_size_kb:.0f} KB")

                # V5.4: 记录下载
                self._record_download(material_id, str(filepath), "photo")

                return str(filepath)
            else:
                print(f"   ❌ 下载失败: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"   ❌ 下载错误: {str(e)}")
            return None

    def fetch_and_download_videos(
        self,
        keyword: str,
        count: int = 5
    ) -> List[str]:
        """
        搜索并下载视频(一站式)

        Args:
            keyword: 关键词
            count: 下载数量

        Returns:
            已下载文件路径列表
        """
        videos = self.search_videos(keyword, per_page=count)

        downloaded = []
        for i, video in enumerate(videos[:count], 1):
            print(f"\n📹 [{i}/{len(videos)}]")
            filepath = self.download_video(video, keyword)
            if filepath:
                downloaded.append(filepath)
            time.sleep(0.5)  # 避免请求过快

        return downloaded

    def fetch_and_download_photos(
        self,
        keyword: str,
        count: int = 5
    ) -> List[str]:
        """
        搜索并下载图片(一站式)

        Args:
            keyword: 关键词
            count: 下载数量

        Returns:
            已下载文件路径列表
        """
        photos = self.search_photos(keyword, per_page=count)

        downloaded = []
        for i, photo in enumerate(photos[:count], 1):
            print(f"\n🖼️  [{i}/{len(photos)}]")
            filepath = self.download_photo(photo, keyword)
            if filepath:
                downloaded.append(filepath)
            time.sleep(0.3)

        return downloaded

    def get_stats(self) -> Dict[str, Any]:
        """
        获取下载统计

        Returns:
            统计信息字典
        """
        video_count = len(list(self.video_dir.glob("*.mp4")))
        photo_count = len(list(self.image_dir.glob("*.jpg"))) + len(list(self.image_dir.glob("*.png")))

        # 计算总大小
        video_size = sum(f.stat().st_size for f in self.video_dir.glob("*.mp4"))
        photo_size = sum(f.stat().st_size for f in self.image_dir.glob("*.jpg"))
        photo_size += sum(f.stat().st_size for f in self.image_dir.glob("*.png"))

        return {
            "video_count": video_count,
            "photo_count": photo_count,
            "total_count": video_count + photo_count,
            "video_size_mb": round(video_size / (1024 * 1024), 1),
            "photo_size_mb": round(photo_size / (1024 * 1024), 1),
            "total_size_mb": round((video_size + photo_size) / (1024 * 1024), 1)
        }


# 命令行测试
if __name__ == "__main__":
    import sys

    fetcher = PexelsFetcher()

    if len(sys.argv) > 1:
        keyword = sys.argv[1]

        # 搜索并下载视频
        print(f"\n{'='*60}")
        print(f"搜索关键词: {keyword}")
        print(f"{'='*60}")

        videos = fetcher.fetch_and_download_videos(keyword, count=3)
        photos = fetcher.fetch_and_download_photos(keyword, count=3)

        print(f"\n{'='*60}")
        print(f"✅ 下载完成!")
        print(f"   视频: {len(videos)} 个")
        print(f"   图片: {len(photos)} 个")
        print(f"{'='*60}")

        # 显示统计
        stats = fetcher.get_stats()
        print(f"\n📊 素材库统计:")
        print(f"   总计: {stats['total_count']} 个素材")
        print(f"   视频: {stats['video_count']} 个 ({stats['video_size_mb']} MB)")
        print(f"   图片: {stats['photo_count']} 个 ({stats['photo_size_mb']} MB)")
    else:
        print("用法:")
        print("  python pexels_fetcher.py <关键词>")
        print("\n示例:")
        print("  python pexels_fetcher.py 'space'")
        print("  python pexels_fetcher.py 'DNA'")
        print("  python pexels_fetcher.py 'technology'")
