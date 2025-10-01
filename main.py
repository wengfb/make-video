#!/usr/bin/env python3
"""
科普视频自动化制作系统 - 主程序 v5.0
新增: TTS语音合成 + 字幕生成 + 完整AI视频工作流
"""

import sys
import os
import argparse

# 添加模块路径
sys.path.insert(0, 'scripts/1_script_generator')
sys.path.insert(0, 'scripts/0_topic_generator')
sys.path.insert(0, 'scripts/2_material_manager')
sys.path.insert(0, 'scripts/3_video_editor')

# 导入模块（由于多个目录都有generator.py，需要分别导入）
import importlib.util

# 加载脚本生成器
spec1 = importlib.util.spec_from_file_location("script_generator", "scripts/1_script_generator/generator.py")
script_gen_module = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(script_gen_module)
ScriptGenerator = script_gen_module.ScriptGenerator

# 加载主题生成器
spec2 = importlib.util.spec_from_file_location("topic_generator", "scripts/0_topic_generator/generator.py")
topic_gen_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(topic_gen_module)
TopicGenerator = topic_gen_module.TopicGenerator

# 加载主题管理器
spec3 = importlib.util.spec_from_file_location("topic_manager", "scripts/0_topic_generator/manager.py")
topic_mgr_module = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(topic_mgr_module)
TopicManager = topic_mgr_module.TopicManager

# 加载素材管理器
spec4 = importlib.util.spec_from_file_location("material_manager", "scripts/2_material_manager/manager.py")
mat_mgr_module = importlib.util.module_from_spec(spec4)
spec4.loader.exec_module(mat_mgr_module)
MaterialManager = mat_mgr_module.MaterialManager

# 加载AI图片生成器
spec5 = importlib.util.spec_from_file_location("ai_generator", "scripts/2_material_manager/ai_generator.py")
ai_gen_module = importlib.util.module_from_spec(spec5)
spec5.loader.exec_module(ai_gen_module)
AIImageGenerator = ai_gen_module.AIImageGenerator

# 加载素材管理UI
spec6 = importlib.util.spec_from_file_location("material_ui", "scripts/2_material_manager/ui.py")
mat_ui_module = importlib.util.module_from_spec(spec6)
spec6.loader.exec_module(mat_ui_module)
material_manager_menu = mat_ui_module.material_manager_menu

# 加载视频合成器
spec7 = importlib.util.spec_from_file_location("video_composer", "scripts/3_video_editor/composer.py")
video_comp_module = importlib.util.module_from_spec(spec7)
spec7.loader.exec_module(video_comp_module)
VideoComposer = video_comp_module.VideoComposer

# 加载TTS生成器
spec8 = importlib.util.spec_from_file_location("tts_generator", "scripts/4_tts_generator/generator.py")
tts_gen_module = importlib.util.module_from_spec(spec8)
spec8.loader.exec_module(tts_gen_module)
TTSGenerator = tts_gen_module.TTSGenerator

# 加载TTS管理器
spec9 = importlib.util.spec_from_file_location("tts_manager", "scripts/4_tts_generator/manager.py")
tts_mgr_module = importlib.util.module_from_spec(spec9)
spec9.loader.exec_module(tts_mgr_module)
TTSManager = tts_mgr_module.TTSManager

# 加载字幕生成器
spec10 = importlib.util.spec_from_file_location("subtitle_generator", "scripts/4_subtitle_generator/generator.py")
sub_gen_module = importlib.util.module_from_spec(spec10)
spec10.loader.exec_module(sub_gen_module)
SubtitleGenerator = sub_gen_module.SubtitleGenerator

# 加载成本估算器
spec11 = importlib.util.spec_from_file_location("cost_estimator", "scripts/utils/cost_estimator.py")
cost_est_module = importlib.util.module_from_spec(spec11)
spec11.loader.exec_module(cost_est_module)
CostEstimator = cost_est_module.CostEstimator


def print_banner():
    """打印程序横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        科普视频自动化制作系统 v1.0-beta                   ║
║        AI-Powered Science Video Production System         ║
║        ✨ TTS语音合成 + 字幕生成 + 完整工作流             ║
║        🎙️  从主题到带语音字幕的成品视频                  ║
║        ⚠️  实验性质 | 请注意API成本                       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def interactive_mode():
    """交互式模式"""
    print_banner()
    print("\n欢迎使用科普视频自动化制作系统！")
    print("=" * 60)

    # 初始化
    try:
        script_gen = ScriptGenerator()
        topic_gen = TopicGenerator()
        topic_mgr = TopicManager()
        material_mgr = MaterialManager()
        ai_image_gen = AIImageGenerator()
        video_composer = VideoComposer()
        tts_generator = TTSGenerator()  # V5.0新增
        tts_manager = TTSManager()      # V5.0新增
        subtitle_generator = SubtitleGenerator()  # V5.0新增
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        print("\n请确保:")
        print("1. config/settings.json 中已配置API密钥")
        print("2. 或设置环境变量 OPENAI_API_KEY")
        print("3. 已安装所有依赖: pip install -r requirements.txt")
        print("4. V5.0新增: 需要edge-tts库(免费TTS)")
        return

    # 主循环
    while True:
        print("\n" + "=" * 60)
        print("🎬 主菜单:")
        print("\n📝 主题管理:")
        print("  1. 生成主题建议")
        print("  2. 查看热门趋势主题")
        print("  3. 浏览已保存的主题")
        print("  4. 搜索主题")
        print("  5. 查看收藏的主题")
        print("\n🎥 脚本生成:")
        print("  6. 从主题生成脚本（一站式）")
        print("  7. 直接生成脚本")
        print("\n🎨 素材管理:")
        print("  10. 素材管理（素材库+AI生成）")
        print("\n🎬 视频合成:")
        print("  11. 从脚本生成视频（自动）")
        print("  12. 预览素材推荐")
        print("  13. 完整工作流（主题→脚本→视频）")
        print("\n🎙️  语音合成 (V5.0):")
        print("  14. 从脚本生成TTS语音")
        print("  15. 管理TTS语音文件")
        print("\n📝 字幕生成 (V5.0):")
        print("  16. 从脚本生成字幕")
        print("\n🚀 完整AI工作流 (V5.0):")
        print("  17. 从脚本生成完整视频（语音+字幕）")
        print("  18. 全自动工作流（主题→脚本→语音→字幕→视频）")
        print("\n🛠️  其他工具:")
        print("  8. 查看统计信息")
        print("  9. 查看脚本模板")
        print("  0. 退出")
        print("=" * 60)

        choice = input("\n请选择功能 (0-18): ").strip()

        if choice == '0':
            print("\n👋 再见！")
            break
        elif choice == '1':
            generate_topics_interactive(topic_gen, topic_mgr)
        elif choice == '2':
            show_trending_topics(topic_gen, topic_mgr)
        elif choice == '3':
            browse_topics(topic_mgr)
        elif choice == '4':
            search_topics_interactive(topic_mgr)
        elif choice == '5':
            show_favorites(topic_mgr, script_gen)
        elif choice == '6':
            topic_to_script_workflow(topic_gen, topic_mgr, script_gen)
        elif choice == '7':
            generate_script_directly(script_gen)
        elif choice == '8':
            show_statistics(topic_mgr)
        elif choice == '9':
            show_templates(script_gen)
        elif choice == '10':
            material_manager_menu(material_mgr, ai_image_gen)
        elif choice == '11':
            compose_video_from_script(video_composer, script_gen)
        elif choice == '12':
            preview_material_recommendations(video_composer, script_gen)
        elif choice == '13':
            full_workflow(topic_gen, topic_mgr, script_gen, video_composer)
        elif choice == '14':
            # V5.0: 从脚本生成TTS语音
            generate_tts_from_script(tts_generator, script_gen)
        elif choice == '15':
            # V5.0: 管理TTS语音文件
            manage_tts_audio(tts_manager)
        elif choice == '16':
            # V5.0: 从脚本生成字幕
            generate_subtitle_from_script(subtitle_generator)
        elif choice == '17':
            # V5.0: 从脚本生成完整视频(语音+字幕)
            compose_video_with_tts_subtitle(video_composer, tts_manager)
        elif choice == '18':
            # V5.0: 全自动AI工作流
            full_ai_workflow(topic_gen, script_gen, tts_generator, subtitle_generator, video_composer)
        else:
            print("\n❌ 无效的选择，请重新输入")


def generate_topics_interactive(topic_gen: TopicGenerator, topic_mgr: TopicManager):
    """交互式生成主题"""
    print("\n" + "-" * 60)
    print("💡 生成主题建议")
    print("-" * 60)

    # 选择领域
    fields = topic_gen.list_fields()
    print("\n可选领域:")
    for i, field in enumerate(fields, 1):
        print(f"  {i}. {field}")
    print("  0. 不限（所有领域）")

    field_choice = input(f"\n选择领域 (0-{len(fields)}): ").strip()
    field = None
    if field_choice.isdigit() and 1 <= int(field_choice) <= len(fields):
        field = fields[int(field_choice) - 1]

    # 选择受众
    audiences = topic_gen.list_audiences()
    print("\n目标受众:")
    for i, aud in enumerate(audiences, 1):
        print(f"  {i}. {aud['name']} - {aud['description']}")

    aud_choice = input(f"\n选择受众 (1-{len(audiences)}, 默认4): ").strip()
    audience = 'general_public'
    if aud_choice.isdigit() and 1 <= int(aud_choice) <= len(audiences):
        audience = audiences[int(aud_choice) - 1]['id']

    # 生成数量
    count_input = input("\n生成数量 (默认10): ").strip()
    count = int(count_input) if count_input.isdigit() else 10

    # 成本估算
    cost = CostEstimator.estimate_topic_generation(count=count)
    print(f"\n💰 预估成本: ${cost:.4f} USD")
    confirm = input("是否继续? (Y/n): ").strip().lower()
    if confirm == 'n':
        print("已取消")
        return

    # 额外要求
    custom = input("\n额外要求 (可选，直接回车跳过): ").strip() or None

    try:
        topics = topic_gen.generate_topics(
            field=field,
            audience=audience,
            count=count,
            custom_requirements=custom
        )

        if topics:
            print("\n" + "=" * 60)
            print(f"✨ 成功生成 {len(topics)} 个主题建议！")
            print("=" * 60)

            display_topics_list(topics, topic_mgr)

            # 保存和选择操作
            handle_topic_selection(topics, topic_mgr)

    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")


def show_trending_topics(topic_gen: TopicGenerator, topic_mgr: TopicManager):
    """显示热门趋势主题"""
    print("\n" + "-" * 60)
    print("🔥 热门趋势主题")
    print("-" * 60)

    count_input = input("\n生成数量 (默认10): ").strip()
    count = int(count_input) if count_input.isdigit() else 10

    try:
        topics = topic_gen.generate_trending_topics(count=count)

        if topics:
            print("\n" + "=" * 60)
            print(f"🔥 热门趋势主题 ({len(topics)}个)")
            print("=" * 60)

            for i, topic in enumerate(topics, 1):
                print(f"\n{i}. 【{topic.get('title', 'N/A')}】")
                print(f"   描述: {topic.get('description', 'N/A')}")
                print(f"   热门原因: {topic.get('trend_reason', 'N/A')}")
                print(f"   时效性: {topic.get('urgency', 'N/A')}")
                print(f"   预估热度: {topic.get('estimated_popularity', 'N/A')}")

            handle_topic_selection(topics, topic_mgr)

    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")


def browse_topics(topic_mgr: TopicManager):
    """浏览已保存的主题"""
    print("\n" + "-" * 60)
    print("📚 已保存的主题")
    print("-" * 60)

    topics = topic_mgr.list_topics(sort_by='date', limit=20)

    if not topics:
        print("\n暂无保存的主题")
        return

    print(f"\n共 {len(topics)} 个主题:\n")
    display_topics_list(topics, topic_mgr)

    # 查看详情
    choice = input("\n输入编号查看详情 (直接回车返回): ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(topics):
            show_topic_detail(topics[idx], topic_mgr)


def search_topics_interactive(topic_mgr: TopicManager):
    """交互式搜索主题"""
    print("\n" + "-" * 60)
    print("🔍 搜索主题")
    print("-" * 60)

    keyword = input("\n请输入关键词: ").strip()
    if not keyword:
        return

    topics = topic_mgr.search_topics(keyword)

    if topics:
        print(f"\n找到 {len(topics)} 个相关主题:\n")
        display_topics_list(topics, topic_mgr)

        choice = input("\n输入编号查看详情 (直接回车返回): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(topics):
                show_topic_detail(topics[idx], topic_mgr)
    else:
        print(f"\n未找到包含「{keyword}」的主题")


def show_favorites(topic_mgr: TopicManager, script_gen: ScriptGenerator):
    """显示收藏的主题"""
    print("\n" + "-" * 60)
    print("⭐ 我的收藏")
    print("-" * 60)

    favorites = topic_mgr.list_favorites()

    if not favorites:
        print("\n暂无收藏的主题")
        return

    print(f"\n共 {len(favorites)} 个收藏:\n")

    for i, topic in enumerate(favorites, 1):
        star = "⭐" if topic_mgr.is_favorite(topic.get('id')) else "  "
        rating = f"[{topic.get('rating', '-')}/5]" if 'rating' in topic else "[未评分]"
        print(f"{i}. {star} {topic.get('title', 'N/A')} {rating}")
        if topic.get('favorite_note'):
            print(f"   备注: {topic['favorite_note']}")

    # 操作选项
    choice = input("\n输入编号操作主题 (直接回车返回): ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(favorites):
            topic_action_menu(favorites[idx], topic_mgr, script_gen)


def topic_to_script_workflow(topic_gen: TopicGenerator, topic_mgr: TopicManager, script_gen: ScriptGenerator):
    """主题到脚本的完整工作流"""
    print("\n" + "-" * 60)
    print("🎬 一站式：从主题生成到脚本")
    print("-" * 60)

    print("\n步骤1: 选择主题来源")
    print("  1. 从已保存的主题中选择")
    print("  2. 生成新主题并选择")
    print("  3. 手动输入主题")

    source = input("\n请选择 (1-3): ").strip()

    topic_title = None
    topic_obj = None

    if source == '1':
        # 从已保存的主题中选择
        topics = topic_mgr.list_topics(limit=20)
        if not topics:
            print("\n暂无保存的主题，请先生成主题")
            return

        display_topics_list(topics, topic_mgr)
        choice = input("\n选择主题编号: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(topics):
                topic_obj = topics[idx]
                topic_title = topic_obj.get('title')

    elif source == '2':
        # 生成新主题
        print("\n生成新主题...")
        try:
            topics = topic_gen.generate_topics(count=5)
            display_topics_list(topics, topic_mgr)

            choice = input("\n选择主题编号: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(topics):
                    topic_obj = topics[idx]
                    topic_title = topic_obj.get('title')
                    # 保存选中的主题
                    topic_mgr.save_topic(topic_obj)
                    print(f"\n💾 主题已保存")
        except Exception as e:
            print(f"\n❌ 主题生成失败: {str(e)}")
            return

    elif source == '3':
        # 手动输入
        topic_title = input("\n请输入主题: ").strip()

    if not topic_title:
        print("\n❌ 未选择主题")
        return

    # 步骤2: 生成脚本
    print(f"\n步骤2: 生成脚本")
    print(f"主题: {topic_title}")

    # 选择模板
    templates = script_gen.list_templates()
    print("\n可用模板:")
    for i, tmpl in enumerate(templates, 1):
        print(f"  {i}. {tmpl['display_name']}")

    template_choice = input(f"\n选择模板 (1-{len(templates)}, 默认1): ").strip()
    template_name = templates[0]['name']
    if template_choice.isdigit():
        idx = int(template_choice) - 1
        if 0 <= idx < len(templates):
            template_name = templates[idx]['name']

    # 生成脚本
    try:
        print("\n⏳ 正在生成脚本...")
        script = script_gen.generate_script(
            topic=topic_title,
            template_name=template_name
        )

        print("\n" + "=" * 60)
        print("✨ 脚本生成成功！")
        print("=" * 60)
        print(f"\n标题: {script.get('title', 'N/A')}")
        print(f"\n共 {len(script.get('sections', []))} 个部分")

        # 保存脚本
        save = input("\n是否保存脚本? (Y/n): ").strip().lower()
        if save != 'n':
            filepath = script_gen.save_script(script)

            # 记录历史
            if topic_obj:
                topic_mgr.add_to_history(
                    topic_obj.get('id'),
                    'generated_script',
                    {'script_path': filepath}
                )

    except Exception as e:
        print(f"\n❌ 脚本生成失败: {str(e)}")


def generate_script_directly(script_gen: ScriptGenerator):
    """直接生成脚本（原有功能）"""
    print("\n" + "-" * 60)
    print("📝 生成视频脚本")
    print("-" * 60)

    topic = input("\n请输入视频主题: ").strip()
    if not topic:
        print("❌ 主题不能为空")
        return

    templates = script_gen.list_templates()
    print("\n可用模板:")
    for i, tmpl in enumerate(templates, 1):
        print(f"  {i}. {tmpl['display_name']} - {tmpl['description']}")

    template_choice = input(f"\n选择模板 (1-{len(templates)}, 默认1): ").strip()
    template_name = templates[0]['name']
    if template_choice.isdigit():
        idx = int(template_choice) - 1
        if 0 <= idx < len(templates):
            template_name = templates[idx]['name']

    duration = input("\n视频时长 (如 3-5min, 直接回车使用默认): ").strip() or None
    custom_req = input("\n额外要求 (可选，直接回车跳过): ").strip() or None

    # 成本估算
    cost = CostEstimator.estimate_script_generation(sections=5)
    print(f"\n💰 预估成本: ${cost:.4f} USD")
    confirm = input("是否继续? (Y/n): ").strip().lower()
    if confirm == 'n':
        print("已取消")
        return

    try:
        print("\n⏳ 正在调用AI生成脚本，请稍候...")
        script = script_gen.generate_script(
            topic=topic,
            template_name=template_name,
            duration=duration,
            custom_requirements=custom_req
        )

        print("\n" + "=" * 60)
        print("✨ 脚本生成成功！")
        print("=" * 60)
        print(f"\n标题: {script.get('title', 'N/A')}")
        print(f"\n共 {len(script.get('sections', []))} 个部分:")
        for i, section in enumerate(script.get('sections', []), 1):
            print(f"  {i}. {section.get('section_name', 'N/A')} ({section.get('duration', 'N/A')})")

        save = input("\n是否保存脚本? (Y/n): ").strip().lower()
        if save != 'n':
            script_gen.save_script(script)

    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")


def show_statistics(topic_mgr: TopicManager):
    """显示统计信息"""
    print("\n" + "-" * 60)
    print("📊 统计信息")
    print("-" * 60)

    stats = topic_mgr.get_statistics()

    print(f"\n主题总数: {stats['total_topics']}")
    print(f"收藏数: {stats['total_favorites']}")
    print(f"已评分: {stats['rated_topics']}")
    print(f"平均评分: {stats['average_rating']}/5")

    if stats['by_field']:
        print("\n按领域分布:")
        for field, count in sorted(stats['by_field'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {field}: {count}")

    if stats['by_difficulty']:
        print("\n按难度分布:")
        for diff, count in stats['by_difficulty'].items():
            print(f"  {diff}: {count}")


def show_templates(script_gen: ScriptGenerator):
    """显示模板"""
    print("\n" + "-" * 60)
    print("📋 可用脚本模板")
    print("-" * 60)

    templates = script_gen.list_templates()
    for i, tmpl in enumerate(templates, 1):
        print(f"\n{i}. {tmpl['display_name']}")
        print(f"   ID: {tmpl['name']}")
        print(f"   描述: {tmpl['description']}")


def display_topics_list(topics: list, topic_mgr: TopicManager):
    """显示主题列表"""
    for i, topic in enumerate(topics, 1):
        star = "⭐" if topic_mgr.is_favorite(topic.get('id')) else "  "
        difficulty = topic.get('difficulty', '-')
        popularity = topic.get('estimated_popularity', '-')
        rating = f"[{topic.get('rating', '-')}/5]" if 'rating' in topic else ""

        print(f"{i}. {star} {topic.get('title', 'N/A')} {rating}")
        print(f"   {topic.get('description', 'N/A')[:80]}...")
        print(f"   难度: {difficulty} | 热度: {popularity}")


def show_topic_detail(topic: dict, topic_mgr: TopicManager):
    """显示主题详情"""
    print("\n" + "=" * 60)
    print(f"📋 主题详情")
    print("=" * 60)

    print(f"\n标题: {topic.get('title', 'N/A')}")
    print(f"\n描述: {topic.get('description', 'N/A')}")
    print(f"\n难度: {topic.get('difficulty', 'N/A')}")
    print(f"预估热度: {topic.get('estimated_popularity', 'N/A')}")
    print(f"视觉潜力: {topic.get('visual_potential', 'N/A')}")

    if topic.get('key_points'):
        print(f"\n核心要点:")
        for point in topic['key_points']:
            print(f"  • {point}")

    if topic.get('why_interesting'):
        print(f"\n为什么有趣:")
        print(f"  {topic['why_interesting']}")

    if topic.get('related_topics'):
        print(f"\n相关主题:")
        for related in topic['related_topics']:
            print(f"  • {related}")

    is_fav = topic_mgr.is_favorite(topic.get('id'))
    print(f"\n收藏状态: {'⭐ 已收藏' if is_fav else '未收藏'}")

    if 'rating' in topic:
        print(f"我的评分: {topic['rating']}/5")
        if topic.get('rating_comment'):
            print(f"评价: {topic['rating_comment']}")

    # 操作菜单
    print("\n" + "-" * 60)
    print("操作:")
    print("  1. 添加/取消收藏")
    print("  2. 评分")
    print("  3. 删除主题")
    print("  0. 返回")

    choice = input("\n请选择: ").strip()

    if choice == '1':
        if is_fav:
            topic_mgr.remove_from_favorites(topic.get('id'))
        else:
            note = input("添加备注 (可选): ").strip() or None
            topic_mgr.add_to_favorites(topic.get('id'), note)

    elif choice == '2':
        rating_input = input("评分 (1-5): ").strip()
        if rating_input.isdigit():
            rating = int(rating_input)
            comment = input("评价 (可选): ").strip() or None
            topic_mgr.rate_topic(topic.get('id'), rating, comment)

    elif choice == '3':
        confirm = input("确认删除? (y/N): ").strip().lower()
        if confirm == 'y':
            topic_mgr.delete_topic(topic.get('id'))


def topic_action_menu(topic: dict, topic_mgr: TopicManager, script_gen: ScriptGenerator):
    """主题操作菜单"""
    show_topic_detail(topic, topic_mgr)


def handle_topic_selection(topics: list, topic_mgr: TopicManager):
    """处理主题选择"""
    print("\n" + "-" * 60)
    print("操作选项:")
    print("  s - 保存所有主题")
    print("  数字 - 查看指定主题详情")
    print("  直接回车 - 返回")

    choice = input("\n请选择: ").strip().lower()

    if choice == 's':
        for topic in topics:
            topic_mgr.save_topic(topic)
        print(f"\n💾 已保存 {len(topics)} 个主题")

    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(topics):
            show_topic_detail(topics[idx], topic_mgr)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='科普视频自动化制作系统 v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # generate-topics 命令
    topic_parser = subparsers.add_parser('generate-topics', help='生成主题建议')
    topic_parser.add_argument('-f', '--field', help='科学领域')
    topic_parser.add_argument('-a', '--audience', help='目标受众')
    topic_parser.add_argument('-n', '--count', type=int, default=10, help='生成数量')

    # generate 命令
    generate_parser = subparsers.add_parser('generate', help='生成视频脚本')
    generate_parser.add_argument('topic', help='视频主题')
    generate_parser.add_argument('-t', '--template', help='使用的模板名称')
    generate_parser.add_argument('-d', '--duration', help='视频时长')
    generate_parser.add_argument('-r', '--requirements', help='额外要求')
    generate_parser.add_argument('-o', '--output', help='输出文件名')

    # templates 命令
    subparsers.add_parser('templates', help='列出所有可用模板')

    # stats 命令
    subparsers.add_parser('stats', help='查看统计信息')

    args = parser.parse_args()

    # 如果没有提供命令，进入交互模式
    if args.command is None:
        interactive_mode()
    else:
        # 命令行模式
        try:
            if args.command == 'generate-topics':
                topic_gen = TopicGenerator()
                topics = topic_gen.generate_topics(
                    field=args.field,
                    audience=args.audience,
                    count=args.count
                )
                for i, topic in enumerate(topics, 1):
                    print(f"{i}. {topic.get('title')}")
                    print(f"   {topic.get('description')}")

            elif args.command == 'generate':
                script_gen = ScriptGenerator()
                script = script_gen.generate_script(
                    topic=args.topic,
                    template_name=args.template or 'popular_science',
                    duration=args.duration,
                    custom_requirements=args.requirements
                )
                filepath = script_gen.save_script(script, args.output)
                print(f"✅ 脚本已保存至: {filepath}")

            elif args.command == 'templates':
                script_gen = ScriptGenerator()
                templates = script_gen.list_templates()
                print("可用模板:")
                for tmpl in templates:
                    print(f"  - {tmpl['name']}: {tmpl['display_name']}")

            elif args.command == 'stats':
                topic_mgr = TopicManager()
                stats = topic_mgr.get_statistics()
                print(f"主题总数: {stats['total_topics']}")
                print(f"收藏数: {stats['total_favorites']}")
                print(f"平均评分: {stats['average_rating']}/5")

        except Exception as e:
            print(f"❌ 执行失败: {str(e)}")
            sys.exit(1)


def compose_video_from_script(composer: VideoComposer, script_gen: ScriptGenerator):
    """从脚本生成视频"""
    print("\n" + "-" * 60)
    print("🎬 从脚本生成视频")
    print("-" * 60)

    # 选择脚本
    print("\n1. 从最近生成的脚本选择")
    print("2. 输入脚本文件路径")

    choice = input("\n选择方式 (1-2): ").strip()

    script = None

    if choice == '1':
        # 查找最近的脚本
        import glob
        script_files = glob.glob('output/scripts/*.json')
        if not script_files:
            print("\n❌ 未找到脚本文件")
            return

        script_files.sort(key=os.path.getmtime, reverse=True)
        print(f"\n找到 {len(script_files[:10])} 个最近的脚本:")
        for i, file in enumerate(script_files[:10], 1):
            basename = os.path.basename(file)
            print(f"  {i}. {basename}")

        file_choice = input(f"\n选择脚本 (1-{min(10, len(script_files))}): ").strip()
        if file_choice.isdigit():
            idx = int(file_choice) - 1
            if 0 <= idx < len(script_files):
                import json
                with open(script_files[idx], 'r', encoding='utf-8') as f:
                    script = json.load(f)

    elif choice == '2':
        path = input("\n脚本文件路径: ").strip()
        if os.path.exists(path):
            import json
            with open(path, 'r', encoding='utf-8') as f:
                script = json.load(f)
        else:
            print(f"\n❌ 文件不存在: {path}")
            return

    if not script:
        print("\n❌ 未选择脚本")
        return

    # 显示脚本信息
    print(f"\n📝 脚本: {script.get('title', '未命名')}")
    print(f"   章节数: {len(script.get('sections', []))}")

    info = composer.get_composition_info(script)
    print(f"   预估时长: {info['estimated_duration']:.1f}秒")
    print(f"   预估大小: {info['estimated_file_size_mb']} MB")

    # 确认合成
    confirm = input("\n开始合成视频? (Y/n): ").strip().lower()
    if confirm == 'n':
        return

    try:
        video_path = composer.compose_from_script(
            script,
            auto_select_materials=True
        )
        print(f"\n🎉 视频已生成: {video_path}")

    except Exception as e:
        print(f"\n❌ 合成失败: {str(e)}")
        import traceback
        traceback.print_exc()


def preview_material_recommendations(composer: VideoComposer, script_gen: ScriptGenerator):
    """预览素材推荐"""
    print("\n" + "-" * 60)
    print("🔍 预览素材推荐")
    print("-" * 60)

    # 选择脚本（同上）
    print("\n1. 从最近生成的脚本选择")
    print("2. 输入脚本文件路径")

    choice = input("\n选择方式 (1-2): ").strip()

    script = None

    if choice == '1':
        import glob
        script_files = glob.glob('output/scripts/*.json')
        if not script_files:
            print("\n❌ 未找到脚本文件")
            return

        script_files.sort(key=os.path.getmtime, reverse=True)
        print(f"\n找到 {len(script_files[:10])} 个最近的脚本:")
        for i, file in enumerate(script_files[:10], 1):
            print(f"  {i}. {os.path.basename(file)}")

        file_choice = input(f"\n选择脚本 (1-{min(10, len(script_files))}): ").strip()
        if file_choice.isdigit():
            idx = int(file_choice) - 1
            if 0 <= idx < len(script_files):
                import json
                with open(script_files[idx], 'r', encoding='utf-8') as f:
                    script = json.load(f)

    elif choice == '2':
        path = input("\n脚本文件路径: ").strip()
        if os.path.exists(path):
            import json
            with open(path, 'r', encoding='utf-8') as f:
                script = json.load(f)

    if not script:
        print("\n❌ 未选择脚本")
        return

    # 预览推荐
    try:
        composer.preview_material_recommendations(script)
    except Exception as e:
        print(f"\n❌ 预览失败: {str(e)}")


def full_workflow(
    topic_gen: TopicGenerator,
    topic_mgr: TopicManager,
    script_gen: ScriptGenerator,
    composer: VideoComposer
):
    """完整工作流: 主题 → 脚本 → 视频"""
    print("\n" + "=" * 60)
    print("🚀 完整工作流: 主题 → 脚本 → 视频")
    print("=" * 60)

    # 步骤1: 生成或选择主题
    print("\n📝 步骤1: 选择主题")
    print("-" * 60)
    print("1. 生成新主题")
    print("2. 从收藏中选择")
    print("3. 从历史中选择")

    topic_choice = input("\n选择方式 (1-3): ").strip()

    topic = None

    if topic_choice == '1':
        # 快速生成
        print("\n⏳ 正在生成主题建议...")
        topics = topic_gen.generate_topics(count=5)
        if topics:
            print(f"\n生成了 {len(topics)} 个主题:")
            for i, t in enumerate(topics, 1):
                print(f"  {i}. {t['title']}")

            sel = input(f"\n选择主题 (1-{len(topics)}): ").strip()
            if sel.isdigit():
                idx = int(sel) - 1
                if 0 <= idx < len(topics):
                    topic = topics[idx]

    elif topic_choice == '2':
        favorites = topic_mgr.list_favorites()
        if favorites:
            print(f"\n收藏的主题 ({len(favorites)}个):")
            for i, t in enumerate(favorites[:10], 1):
                print(f"  {i}. {t['title']}")

            sel = input(f"\n选择主题 (1-{min(10, len(favorites))}): ").strip()
            if sel.isdigit():
                idx = int(sel) - 1
                if 0 <= idx < len(favorites):
                    topic = favorites[idx]
        else:
            print("\n暂无收藏的主题")
            return

    elif topic_choice == '3':
        history = topic_mgr.list_topics(limit=10)
        if history:
            print(f"\n最近的主题:")
            for i, t in enumerate(history, 1):
                print(f"  {i}. {t['title']}")

            sel = input(f"\n选择主题 (1-{len(history)}): ").strip()
            if sel.isdigit():
                idx = int(sel) - 1
                if 0 <= idx < len(history):
                    topic = history[idx]
        else:
            print("\n暂无主题历史")
            return

    if not topic:
        print("\n❌ 未选择主题")
        return

    print(f"\n✅ 已选择主题: {topic['title']}")

    # 步骤2: 生成脚本
    print("\n📄 步骤2: 生成脚本")
    print("-" * 60)

    confirm = input("开始生成脚本? (Y/n): ").strip().lower()
    if confirm == 'n':
        return

    try:
        print("\n⏳ 正在生成脚本（可能需要1-2分钟）...")
        script_path = script_gen.generate_from_topic(topic)

        if script_path:
            # 读取生成的脚本
            import json
            with open(script_path, 'r', encoding='utf-8') as f:
                script = json.load(f)

            print(f"\n✅ 脚本生成完成!")
            print(f"   标题: {script.get('title')}")
            print(f"   章节数: {len(script.get('sections', []))}")
            print(f"   总时长: {script.get('total_duration', 0)}秒")
        else:
            print("\n❌ 脚本生成失败")
            return

    except Exception as e:
        print(f"\n❌ 脚本生成失败: {str(e)}")
        return

    # 步骤3: 合成视频
    print("\n🎬 步骤3: 合成视频")
    print("-" * 60)

    info = composer.get_composition_info(script)
    print(f"   预估时长: {info['estimated_duration']:.1f}秒")
    print(f"   预估大小: {info['estimated_file_size_mb']} MB")

    confirm = input("\n开始合成视频? (Y/n): ").strip().lower()
    if confirm == 'n':
        print("\n脚本已保存，您可以稍后在菜单11中合成视频")
        return

    try:
        print("\n⏳ 正在合成视频...")
        video_path = composer.compose_from_script(script, auto_select_materials=True)

        print("\n" + "=" * 60)
        print("🎉 完整工作流完成!")
        print("=" * 60)
        print(f"   主题: {topic['title']}")
        print(f"   脚本: {script.get('title')}")
        print(f"   视频: {video_path}")

    except Exception as e:
        print(f"\n❌ 视频合成失败: {str(e)}")
        import traceback
        traceback.print_exc()


def generate_tts_from_script(tts_gen: TTSGenerator, script_gen: ScriptGenerator):
    """从脚本生成TTS语音 (V5.0)"""
    print("\n" + "-" * 60)
    print("🎙️  从脚本生成TTS语音")
    print("-" * 60)

    # 选择脚本
    print("\n1. 从最近生成的脚本选择")
    print("2. 输入脚本文件路径")

    choice = input("\n选择方式 (1-2): ").strip()

    script_path = None

    if choice == '1':
        import glob
        script_files = glob.glob('output/scripts/*.json')
        if not script_files:
            print("\n❌ 未找到脚本文件")
            return

        script_files.sort(key=os.path.getmtime, reverse=True)
        print(f"\n找到 {len(script_files[:10])} 个最近的脚本:")
        for i, file in enumerate(script_files[:10], 1):
            print(f"  {i}. {os.path.basename(file)}")

        file_choice = input(f"\n选择脚本 (1-{min(10, len(script_files))}): ").strip()
        if file_choice.isdigit():
            idx = int(file_choice) - 1
            if 0 <= idx < len(script_files):
                script_path = script_files[idx]

    elif choice == '2':
        path = input("\n脚本文件路径: ").strip()
        if os.path.exists(path):
            script_path = path

    if not script_path:
        print("\n❌ 未选择脚本")
        return

    # 生成TTS
    try:
        result = tts_gen.generate_speech_from_script(script_path)
        if result.get('success'):
            print("\n✅ TTS语音生成成功!")
            print(f"元数据文件: {result['metadata_path']}")
        else:
            print(f"\n❌ TTS生成失败: {result.get('error')}")
    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")
        import traceback
        traceback.print_exc()


def manage_tts_audio(tts_mgr: TTSManager):
    """管理TTS语音文件 (V5.0)"""
    print("\n" + "-" * 60)
    print("📚 TTS语音管理")
    print("-" * 60)

    tts_mgr.interactive_menu()


def generate_subtitle_from_script(sub_gen: SubtitleGenerator):
    """从脚本生成字幕 (V5.0)"""
    print("\n" + "-" * 60)
    print("📝 从脚本生成字幕")
    print("-" * 60)

    # 选择脚本
    print("\n1. 从最近生成的脚本选择")
    print("2. 输入脚本文件路径")

    choice = input("\n选择方式 (1-2): ").strip()

    script_path = None

    if choice == '1':
        import glob
        script_files = glob.glob('output/scripts/*.json')
        if not script_files:
            print("\n❌ 未找到脚本文件")
            return

        script_files.sort(key=os.path.getmtime, reverse=True)
        print(f"\n找到 {len(script_files[:10])} 个最近的脚本:")
        for i, file in enumerate(script_files[:10], 1):
            print(f"  {i}. {os.path.basename(file)}")

        file_choice = input(f"\n选择脚本 (1-{min(10, len(script_files))}): ").strip()
        if file_choice.isdigit():
            idx = int(file_choice) - 1
            if 0 <= idx < len(script_files):
                script_path = script_files[idx]

    elif choice == '2':
        path = input("\n脚本文件路径: ").strip()
        if os.path.exists(path):
            script_path = path

    if not script_path:
        print("\n❌ 未选择脚本")
        return

    # 可选: 选择TTS音频元数据(用于精确对齐)
    print("\n是否使用TTS音频进行精确时间对齐?")
    print("1. 是 (推荐,需要先生成TTS)")
    print("2. 否 (使用估算时长)")

    audio_choice = input("\n选择 (1-2): ").strip()

    audio_metadata_path = None

    if audio_choice == '1':
        # 查找对应的TTS元数据
        import glob
        tts_files = glob.glob('materials/audio/tts/*_metadata.json')
        if tts_files:
            print(f"\n找到 {len(tts_files)} 个TTS音频:")
            for i, file in enumerate(tts_files, 1):
                print(f"  {i}. {os.path.basename(file)}")

            tts_choice = input(f"\n选择TTS音频 (1-{len(tts_files)}, 0=跳过): ").strip()
            if tts_choice.isdigit() and int(tts_choice) > 0:
                idx = int(tts_choice) - 1
                if 0 <= idx < len(tts_files):
                    audio_metadata_path = tts_files[idx]

    # 选择字幕格式
    print("\n选择字幕格式:")
    print("1. SRT (推荐,通用格式)")
    print("2. ASS (高级字幕)")

    format_choice = input("\n选择格式 (1-2): ").strip()
    format = "srt" if format_choice == "1" else "ass"

    # 生成字幕
    try:
        result = sub_gen.generate_from_script(
            script_path,
            audio_metadata_path,
            format=format
        )

        if result.get('success'):
            print("\n✅ 字幕生成成功!")
            print(f"字幕文件: {result['subtitle_file']}")
        else:
            print(f"\n❌ 字幕生成失败: {result.get('error')}")
    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")
        import traceback
        traceback.print_exc()


def compose_video_with_tts_subtitle(
    composer: VideoComposer,
    tts_mgr: TTSManager
):
    """从脚本生成完整视频(语音+字幕) (V5.0)"""
    print("\n" + "=" * 60)
    print("🚀 生成完整视频 (语音+字幕)")
    print("=" * 60)

    # 选择脚本
    print("\n📄 步骤1: 选择脚本")
    import glob
    script_files = glob.glob('output/scripts/*.json')
    if not script_files:
        print("\n❌ 未找到脚本文件")
        return

    script_files.sort(key=os.path.getmtime, reverse=True)
    print(f"\n找到 {len(script_files[:10])} 个最近的脚本:")
    for i, file in enumerate(script_files[:10], 1):
        print(f"  {i}. {os.path.basename(file)}")

    file_choice = input(f"\n选择脚本 (1-{min(10, len(script_files))}): ").strip()
    if not file_choice.isdigit():
        return

    idx = int(file_choice) - 1
    if not (0 <= idx < len(script_files)):
        return

    script_path = script_files[idx]

    import json
    with open(script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)

    # 选择TTS音频
    print("\n🎙️  步骤2: 选择TTS音频")
    audio_list = tts_mgr.list_all_audio()

    if not audio_list:
        print("❌ 未找到TTS音频,请先生成TTS (菜单14)")
        return

    tts_mgr.print_audio_list(audio_list)

    audio_choice = input(f"\n选择TTS音频 (1-{len(audio_list)}): ").strip()
    if not audio_choice.isdigit():
        return

    audio_idx = int(audio_choice) - 1
    if not (0 <= audio_idx < len(audio_list)):
        return

    tts_metadata_path = audio_list[audio_idx]['metadata_file']

    # 选择字幕
    print("\n📝 步骤3: 选择字幕文件")
    print("1. 使用现有字幕")
    print("2. 跳过字幕")

    subtitle_choice = input("\n选择 (1-2): ").strip()

    subtitle_file = None

    if subtitle_choice == '1':
        subtitle_files = glob.glob('output/subtitles/*.srt') + glob.glob('output/subtitles/*.ass')
        if subtitle_files:
            print(f"\n找到 {len(subtitle_files)} 个字幕文件:")
            for i, file in enumerate(subtitle_files, 1):
                print(f"  {i}. {os.path.basename(file)}")

            sub_choice = input(f"\n选择字幕 (1-{len(subtitle_files)}, 0=跳过): ").strip()
            if sub_choice.isdigit() and int(sub_choice) > 0:
                sub_idx = int(sub_choice) - 1
                if 0 <= sub_idx < len(subtitle_files):
                    subtitle_file = subtitle_files[sub_idx]

    # 合成视频
    print("\n🎬 步骤4: 合成视频")
    print("-" * 60)

    info = composer.get_composition_info(script)
    print(f"   预估时长: {info['estimated_duration']:.1f}秒")

    confirm = input("\n开始合成视频? (Y/n): ").strip().lower()
    if confirm == 'n':
        return

    try:
        print("\n⏳ 正在合成视频...")
        video_path = composer.compose_from_script(
            script,
            auto_select_materials=True,
            tts_metadata_path=tts_metadata_path,
            subtitle_file=subtitle_file,
            use_tts_audio=True
        )

        print("\n" + "=" * 60)
        print("🎉 完整视频生成成功!")
        print("=" * 60)
        print(f"   视频: {video_path}")
        print(f"   包含: TTS语音 + {'字幕' if subtitle_file else '无字幕'}")

    except Exception as e:
        print(f"\n❌ 视频合成失败: {str(e)}")
        import traceback
        traceback.print_exc()


def full_ai_workflow(
    topic_gen: TopicGenerator,
    script_gen: ScriptGenerator,
    tts_gen: TTSGenerator,
    sub_gen: SubtitleGenerator,
    composer: VideoComposer
):
    """全自动AI工作流: 主题→脚本→语音→字幕→视频 (V5.0)"""
    print("\n" + "=" * 60)
    print("🚀 全自动AI工作流")
    print("从主题到带语音字幕的成品视频 - 一键完成!")
    print("=" * 60)

    # 步骤1: 生成主题
    print("\n📝 步骤1: 生成主题")
    print("-" * 60)
    print("⏳ 正在生成主题建议...")

    topics = topic_gen.generate_topics(count=5)
    if not topics:
        print("❌ 主题生成失败")
        return

    print(f"\n生成了 {len(topics)} 个主题:")
    for i, t in enumerate(topics, 1):
        print(f"  {i}. {t['title']}")

    sel = input(f"\n选择主题 (1-{len(topics)}): ").strip()
    if not sel.isdigit():
        return

    idx = int(sel) - 1
    if not (0 <= idx < len(topics)):
        return

    topic = topics[idx]

    # 步骤2: 生成脚本
    print(f"\n📄 步骤2: 生成脚本")
    print("-" * 60)
    print("⏳ 正在生成脚本...")

    try:
        # 从主题字典生成脚本
        script_path = script_gen.generate_from_topic(topic)
        if not script_path:
            print("❌ 脚本生成失败")
            return

        import json
        with open(script_path, 'r', encoding='utf-8') as f:
            script = json.load(f)

        print(f"✅ 脚本已生成: {script.get('title')}")
    except Exception as e:
        print(f"❌ 脚本生成失败: {str(e)}")
        return

    # 步骤3: 生成TTS语音
    print(f"\n🎙️  步骤3: 生成TTS语音")
    print("-" * 60)
    print("⏳ 正在生成语音...")

    tts_result = tts_gen.generate_speech_from_script(script_path)
    if not tts_result.get('success'):
        print("❌ TTS生成失败")
        return

    tts_metadata_path = tts_result['metadata_path']
    print(f"✅ 语音已生成 ({tts_result['total_duration']:.1f}秒)")

    # 步骤4: 生成字幕
    print(f"\n📝 步骤4: 生成字幕")
    print("-" * 60)
    print("⏳ 正在生成字幕...")

    sub_result = sub_gen.generate_from_script(
        script_path,
        tts_metadata_path,
        format="srt"
    )

    if not sub_result.get('success'):
        print("⚠️  字幕生成失败,将继续合成视频(无字幕)")
        subtitle_file = None
    else:
        subtitle_file = sub_result['subtitle_file']
        print(f"✅ 字幕已生成")

    # 步骤5: 合成视频
    print(f"\n🎬 步骤5: 合成视频")
    print("-" * 60)
    print("⏳ 正在合成视频...")

    try:
        video_path = composer.compose_from_script(
            script,
            auto_select_materials=True,
            tts_metadata_path=tts_metadata_path,
            subtitle_file=subtitle_file,
            use_tts_audio=True
        )

        print("\n" + "=" * 60)
        print("🎉 全自动AI工作流完成!")
        print("=" * 60)
        print(f"   主题: {topic['title']}")
        print(f"   脚本: {script.get('title')}")
        print(f"   语音: {tts_result['audio_files'][0]['file_path'] if tts_result['audio_files'] else 'N/A'}")
        print(f"   字幕: {subtitle_file if subtitle_file else '无'}")
        print(f"   视频: {video_path}")
        print("\n🎊 您的AI视频已准备就绪!")

    except Exception as e:
        print(f"\n❌ 视频合成失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
