#!/usr/bin/env python3
"""
Unsplash高质量图片素材获取器
摄影师级别的免费科普图片
"""

import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
import time


class UnsplashFetcher:
    """Unsplash图片获取器"""

    def __init__(self, config_path: str = "config/settings.json"):
        """
        初始化Unsplash获取器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)

        # Unsplash API配置
        unsplash_config = self.config.get("unsplash", {})
        self.access_key = unsplash_config.get("access_key") or os.getenv("UNSPLASH_ACCESS_KEY")

        if not self.access_key:
            print("⚠️  未配置Unsplash Access Key")
            print("   请访问 https://unsplash.com/developers 免费注册")
            print("   然后在 config/settings.json 中添加 unsplash.access_key")

        # API端点
        self.search_api_url = "https://api.unsplash.com/search/photos"
        self.download_track_url = "https://api.unsplash.com/photos/{id}/download"

        # 请求头
        self.headers = {
            "Authorization": f"Client-ID {self.access_key}"
        }

        # 保存路径
        self.image_dir = Path(self.config["paths"]["materials"]) / "images" / "unsplash"
        self.image_dir.mkdir(parents=True, exist_ok=True)

        # 元数据缓存
        self.cache_file = Path(self.config["paths"]["materials"]) / "unsplash_cache.json"
        self.cache = self._load_cache()

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载配置失败: {str(e)}")
            return {"paths": {"materials": "./materials"}, "unsplash": {}}

    def _load_cache(self) -> dict:
        """加载缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        """保存缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存缓存失败: {str(e)}")

    def search_photos(
        self,
        query: str,
        per_page: int = 10,
        orientation: str = "landscape",
        color: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索Unsplash图片

        Args:
            query: 搜索关键词 (英文)
            per_page: 每页结果数 (最多30)
            orientation: 方向 (landscape/portrait/squarish)
            color: 颜色过滤 (black_and_white/black/white/yellow/orange/red/purple/magenta/green/teal/blue)

        Returns:
            图片信息列表
        """
        if not self.access_key:
            print("❌ Unsplash Access Key未配置")
            return []

        print(f"\n🔍 搜索Unsplash图片: '{query}'")

        # 检查缓存
        cache_key = f"{query}_{orientation}_{color}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            # 缓存7天
            if time.time() - cached["timestamp"] < 7 * 86400:
                print(f"✅ 使用缓存 ({len(cached['results'])}个结果)")
                return cached["results"]

        try:
            params = {
                "query": query,
                "per_page": min(per_page, 30),
                "orientation": orientation
            }

            if color:
                params["color"] = color

            response = requests.get(
                self.search_api_url,
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                photos = data.get("results", [])

                results = []
                for photo in photos:
                    results.append({
                        "id": photo["id"],
                        "description": photo.get("description") or photo.get("alt_description", ""),
                        "urls": {
                            "raw": photo["urls"]["raw"],
                            "full": photo["urls"]["full"],
                            "regular": photo["urls"]["regular"],  # 1080px宽
                            "small": photo["urls"]["small"]
                        },
                        "width": photo["width"],
                        "height": photo["height"],
                        "color": photo.get("color", "#000000"),
                        "user": {
                            "name": photo["user"]["name"],
                            "username": photo["user"]["username"]
                        },
                        "downloads": photo.get("downloads", 0),
                        "likes": photo.get("likes", 0)
                    })

                print(f"✅ 找到 {len(results)} 张图片")

                # 更新缓存
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "results": results
                }
                self._save_cache()

                return results

            elif response.status_code == 403:
                print("⚠️  API请求限制 (每小时50次)")
                return []
            else:
                print(f"❌ API错误: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ 搜索失败: {str(e)}")
            return []

    def download_photo(
        self,
        photo_info: Dict[str, Any],
        keyword: str = "photo",
        quality: str = "regular"
    ) -> Optional[str]:
        """
        下载图片到本地

        Args:
            photo_info: 图片信息字典
            keyword: 关键词(用于命名)
            quality: 质量 (raw/full/regular/small)

        Returns:
            本地文件路径或None
        """
        try:
            photo_id = photo_info["id"]
            url = photo_info["urls"].get(quality, photo_info["urls"]["regular"])

            # 文件名
            safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{safe_keyword}_{photo_id}.jpg"
            filepath = self.image_dir / filename

            # 检查是否已存在
            if filepath.exists():
                print(f"   ⏭️  已存在: {filename}")
                return str(filepath)

            print(f"   ⬇️  下载图片: {filename} ({quality})")

            # Unsplash要求触发下载跟踪(用于统计)
            if self.access_key:
                try:
                    track_url = self.download_track_url.format(id=photo_id)
                    requests.get(track_url, headers=self.headers, timeout=5)
                except:
                    pass  # 忽略跟踪失败

            # 下载图片
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)

                file_size_kb = filepath.stat().st_size / 1024
                print(f"   ✅ 下载完成: {file_size_kb:.0f} KB")

                return str(filepath)
            else:
                print(f"   ❌ 下载失败: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"   ❌ 下载错误: {str(e)}")
            return None

    def fetch_and_download(
        self,
        keyword: str,
        count: int = 10,
        orientation: str = "landscape",
        quality: str = "regular"
    ) -> List[str]:
        """
        搜索并下载图片(一站式)

        Args:
            keyword: 关键词
            count: 下载数量
            orientation: 方向
            quality: 质量

        Returns:
            已下载文件路径列表
        """
        photos = self.search_photos(keyword, per_page=count, orientation=orientation)

        downloaded = []
        for i, photo in enumerate(photos[:count], 1):
            print(f"\n🖼️  [{i}/{len(photos)}]")
            filepath = self.download_photo(photo, keyword, quality)
            if filepath:
                downloaded.append(filepath)
            time.sleep(0.3)  # 避免请求过快

        return downloaded

    def get_stats(self) -> Dict[str, Any]:
        """
        获取下载统计

        Returns:
            统计信息
        """
        photo_count = len(list(self.image_dir.glob("*.jpg"))) + len(list(self.image_dir.glob("*.png")))
        total_size = sum(f.stat().st_size for f in self.image_dir.glob("*.jpg"))
        total_size += sum(f.stat().st_size for f in self.image_dir.glob("*.png"))

        return {
            "photo_count": photo_count,
            "total_size_mb": round(total_size / (1024 * 1024), 1)
        }


# 命令行测试
if __name__ == "__main__":
    import sys

    fetcher = UnsplashFetcher()

    if len(sys.argv) > 1:
        keyword = sys.argv[1]
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5

        print(f"\n{'='*60}")
        print(f"搜索关键词: {keyword}")
        print(f"{'='*60}")

        photos = fetcher.fetch_and_download(keyword, count=count)

        print(f"\n{'='*60}")
        print(f"✅ 下载完成: {len(photos)} 张图片")
        print(f"{'='*60}")

        # 统计
        stats = fetcher.get_stats()
        print(f"\n📊 Unsplash素材统计:")
        print(f"   图片: {stats['photo_count']} 张")
        print(f"   大小: {stats['total_size_mb']} MB")
    else:
        print("用法:")
        print("  python unsplash_fetcher.py <关键词> [数量]")
        print("\n示例:")
        print("  python unsplash_fetcher.py 'space' 10")
        print("  python unsplash_fetcher.py 'DNA' 5")
        print("  python unsplash_fetcher.py 'brain science'")
