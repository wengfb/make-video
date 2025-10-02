#!/usr/bin/env python3
"""
批量预缓存科普素材工具
一键下载100+热门科普关键词的视频和图片
"""

import sys
import os
import time

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '2_material_manager'))

from pexels_fetcher import PexelsFetcher
from unsplash_fetcher import UnsplashFetcher


# 热门科普关键词库 (100个)
SCIENCE_KEYWORDS = [
    # 天文宇宙 (15个)
    "space universe", "galaxy stars", "planet earth", "solar system", "black hole",
    "nebula cosmos", "meteor shower", "aurora borealis", "moon phases", "sun flare",
    "asteroid belt", "milky way", "telescope astronomy", "comet tail", "space station",

    # 生物医学 (20个)
    "DNA genetics", "cell biology", "microscope bacteria", "virus pathogen", "brain neuroscience",
    "heart cardiology", "lungs respiratory", "blood circulation", "immune system", "vaccine syringe",
    "microscopy lab", "petri dish culture", "chromosome genes", "protein molecule", "enzyme reaction",
    "neurons synapse", "antibody defense", "stem cells", "cancer cells", "organ transplant",

    # 物理化学 (20个)
    "quantum physics", "atom molecule", "chemistry lab", "periodic table", "chemical reaction",
    "electricity circuit", "magnetism field", "light spectrum", "laser beam", "wave particle",
    "nuclear energy", "atomic structure", "chemical flask", "crystallization process", "laboratory equipment",
    "plasma state", "superconductor", "fiber optics", "radioactive decay", "fusion reactor",

    # 科技工程 (20个)
    "artificial intelligence AI", "robot technology", "computer chip", "circuit board", "data network",
    "machine learning", "neural network", "algorithm code", "server datacenter", "cybersecurity hacker",
    "3D printing", "drone aircraft", "renewable energy", "solar panels", "wind turbine",
    "electric vehicle", "nanotechnology", "quantum computer", "5G network", "blockchain technology",

    # 环境自然 (15个)
    "ocean sea waves", "coral reef marine", "forest trees", "mountain landscape", "volcano eruption",
    "earthquake seismic", "climate weather", "glacier ice", "rainforest biodiversity", "desert sand",
    "waterfall river", "ecosystem wildlife", "pollution environment", "recycling waste", "conservation nature",

    # 数学工程 (10个)
    "mathematics geometry", "fractal pattern", "graph statistics", "pi number", "fibonacci sequence",
    "engineering blueprint", "mechanical gears", "architecture building", "bridge structure", "pyramid geometry"
]


class MaterialPrefetcher:
    """素材预缓存工具"""

    def __init__(self):
        """初始化"""
        print("\n🚀 科普素材批量预缓存工具")
        print("=" * 60)

        self.pexels = PexelsFetcher()
        self.unsplash = UnsplashFetcher()

        # 统计
        self.stats = {
            "total_keywords": 0,
            "videos_downloaded": 0,
            "photos_pexels": 0,
            "photos_unsplash": 0,
            "errors": 0,
            "skipped": 0
        }

    def prefetch_all(
        self,
        videos_per_keyword: int = 3,
        photos_per_keyword: int = 2,
        max_keywords: int = None,
        enable_videos: bool = True,
        enable_pexels_photos: bool = True,
        enable_unsplash: bool = True
    ):
        """
        批量预缓存所有关键词

        Args:
            videos_per_keyword: 每个关键词下载视频数
            photos_per_keyword: 每个关键词下载图片数
            max_keywords: 最多处理关键词数(None=全部)
            enable_videos: 是否下载视频
            enable_pexels_photos: 是否下载Pexels图片
            enable_unsplash: 是否下载Unsplash图片
        """
        keywords = SCIENCE_KEYWORDS[:max_keywords] if max_keywords else SCIENCE_KEYWORDS

        self.stats["total_keywords"] = len(keywords)

        print(f"\n📦 预缓存配置:")
        print(f"   关键词总数: {len(keywords)}")
        print(f"   每个关键词: {videos_per_keyword}个视频 + {photos_per_keyword}张图片")
        print(f"   预计下载: {len(keywords) * videos_per_keyword}个视频 + {len(keywords) * photos_per_keyword * 2}张图片")
        print(f"   启用源: {'视频✓' if enable_videos else '视频✗'} "
              f"{'Pexels图片✓' if enable_pexels_photos else 'Pexels图片✗'} "
              f"{'Unsplash✓' if enable_unsplash else 'Unsplash✗'}")

        confirm = input("\n是否继续? (Y/n): ").strip().lower()
        if confirm == 'n':
            print("已取消")
            return

        print(f"\n{'='*60}")
        print("开始批量下载...")
        print(f"{'='*60}\n")

        start_time = time.time()

        for i, keyword in enumerate(keywords, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(keywords)}] 处理关键词: {keyword}")
            print(f"{'='*60}")

            try:
                # 🎥 下载视频
                if enable_videos:
                    videos = self.pexels.fetch_and_download_videos(keyword, count=videos_per_keyword)
                    self.stats["videos_downloaded"] += len(videos)
                    time.sleep(1)  # 避免API限流

                # 🖼️ 下载Pexels图片
                if enable_pexels_photos:
                    photos = self.pexels.fetch_and_download_photos(keyword, count=photos_per_keyword)
                    self.stats["photos_pexels"] += len(photos)
                    time.sleep(0.5)

                # 📸 下载Unsplash图片
                if enable_unsplash:
                    photos = self.unsplash.fetch_and_download(keyword, count=photos_per_keyword)
                    self.stats["photos_unsplash"] += len(photos)
                    time.sleep(0.5)

                print(f"\n✅ 关键词 '{keyword}' 处理完成")

            except KeyboardInterrupt:
                print("\n\n⚠️  用户中断，正在保存...")
                break

            except Exception as e:
                print(f"\n❌ 关键词 '{keyword}' 处理失败: {str(e)}")
                self.stats["errors"] += 1
                time.sleep(2)

        # 最终统计
        elapsed = time.time() - start_time
        self._print_summary(elapsed)

    def prefetch_category(self, category: str, count: int = 5):
        """
        按类别预缓存

        Args:
            category: 类别(astronomy/biology/physics/chemistry/technology/environment/math)
            count: 每个关键词下载数
        """
        category_map = {
            "astronomy": SCIENCE_KEYWORDS[0:15],
            "biology": SCIENCE_KEYWORDS[15:35],
            "physics": SCIENCE_KEYWORDS[35:55],
            "technology": SCIENCE_KEYWORDS[55:75],
            "environment": SCIENCE_KEYWORDS[75:90],
            "math": SCIENCE_KEYWORDS[90:100]
        }

        if category not in category_map:
            print(f"❌ 未知类别: {category}")
            print(f"可选: {', '.join(category_map.keys())}")
            return

        keywords = category_map[category]
        print(f"\n📂 类别: {category}")
        print(f"   关键词数: {len(keywords)}")

        self.prefetch_all(
            videos_per_keyword=count,
            photos_per_keyword=count,
            max_keywords=len(keywords)
        )

    def _print_summary(self, elapsed: float):
        """打印统计摘要"""
        print(f"\n\n{'='*60}")
        print("📊 预缓存统计")
        print(f"{'='*60}")

        print(f"\n处理关键词: {self.stats['total_keywords']} 个")
        print(f"下载视频: {self.stats['videos_downloaded']} 个")
        print(f"下载图片 (Pexels): {self.stats['photos_pexels']} 张")
        print(f"下载图片 (Unsplash): {self.stats['photos_unsplash']} 张")
        print(f"总计素材: {self.stats['videos_downloaded'] + self.stats['photos_pexels'] + self.stats['photos_unsplash']} 个")

        if self.stats['errors'] > 0:
            print(f"\n⚠️  错误: {self.stats['errors']} 次")

        print(f"\n耗时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")

        # 获取最新素材库统计
        pexels_stats = self.pexels.get_stats()
        unsplash_stats = self.unsplash.get_stats()

        print(f"\n📁 素材库总计:")
        print(f"   Pexels视频: {pexels_stats['video_count']} 个 ({pexels_stats['video_size_mb']} MB)")
        print(f"   Pexels图片: {pexels_stats['photo_count']} 张 ({pexels_stats['photo_size_mb']} MB)")
        print(f"   Unsplash图片: {unsplash_stats['photo_count']} 张 ({unsplash_stats['total_size_mb']} MB)")
        print(f"   总大小: {pexels_stats['total_size_mb'] + unsplash_stats['total_size_mb']:.1f} MB")

        print(f"\n{'='*60}")
        print("🎉 预缓存完成!")
        print(f"{'='*60}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="批量预缓存科普素材",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 预缓存所有100个关键词(每个3视频+2图片)
  python prefetch_materials.py

  # 只预缓存前10个关键词
  python prefetch_materials.py --max 10

  # 预缓存天文类别(每个5素材)
  python prefetch_materials.py --category astronomy --count 5

  # 只下载视频,不下载图片
  python prefetch_materials.py --videos-only

  # 快速模式(每个关键词1视频+1图片)
  python prefetch_materials.py --quick
        """
    )

    parser.add_argument("--max", type=int, help="最多处理关键词数")
    parser.add_argument("--category", choices=["astronomy", "biology", "physics", "technology", "environment", "math"],
                       help="按类别预缓存")
    parser.add_argument("--count", type=int, default=3, help="每个关键词下载数 (默认3)")
    parser.add_argument("--videos-only", action="store_true", help="只下载视频")
    parser.add_argument("--photos-only", action="store_true", help="只下载图片")
    parser.add_argument("--no-unsplash", action="store_true", help="禁用Unsplash")
    parser.add_argument("--quick", action="store_true", help="快速模式(每个1视频+1图片)")

    args = parser.parse_args()

    prefetcher = MaterialPrefetcher()

    # 快速模式
    if args.quick:
        args.count = 1

    # 类别模式
    if args.category:
        prefetcher.prefetch_category(args.category, args.count)
    else:
        # 全量模式
        prefetcher.prefetch_all(
            videos_per_keyword=args.count if not args.photos_only else 0,
            photos_per_keyword=args.count if not args.videos_only else 0,
            max_keywords=args.max,
            enable_videos=not args.photos_only,
            enable_pexels_photos=not args.videos_only,
            enable_unsplash=not args.videos_only and not args.no_unsplash
        )


if __name__ == "__main__":
    main()
