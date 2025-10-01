#!/usr/bin/env python3
"""
科普视频自动化制作系统 - 主程序 v2.0
新增主题生成和管理功能
"""

import sys
import os
import argparse

# 添加模块路径
sys.path.insert(0, 'scripts/1_script_generator')
sys.path.insert(0, 'scripts/0_topic_generator')

# 导入模块（由于两个目录都有generator.py，需要分别导入）
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


def print_banner():
    """打印程序横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        科普视频自动化制作系统 v2.0                        ║
║        AI-Powered Science Video Production System         ║
║        ✨ 新增：智能主题生成和管理                        ║
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
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        print("\n请确保:")
        print("1. config/settings.json 中已配置API密钥")
        print("2. 或设置环境变量 OPENAI_API_KEY")
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
        print("\n🛠️  其他工具:")
        print("  8. 查看统计信息")
        print("  9. 查看脚本模板")
        print("  0. 退出")
        print("=" * 60)

        choice = input("\n请选择功能 (0-9): ").strip()

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


if __name__ == '__main__':
    main()
