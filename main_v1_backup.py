#!/usr/bin/env python3
"""
科普视频自动化制作系统 - 主程序
"""

import sys
import os
import argparse
from scripts.1_script_generator import ScriptGenerator


def print_banner():
    """打印程序横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        科普视频自动化制作系统 v1.0                        ║
║        AI-Powered Science Video Production System         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def interactive_mode():
    """交互式模式"""
    print_banner()
    print("\n欢迎使用科普视频自动化制作系统！")
    print("=" * 60)

    try:
        generator = ScriptGenerator()
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        print("\n请确保:")
        print("1. config/settings.json 中已配置API密钥")
        print("2. 或设置环境变量 OPENAI_API_KEY")
        return

    while True:
        print("\n" + "=" * 60)
        print("主菜单:")
        print("  1. 生成视频脚本")
        print("  2. 查看可用模板")
        print("  3. 生成开场钩子")
        print("  4. 生成视频标题")
        print("  0. 退出")
        print("=" * 60)

        choice = input("\n请选择功能 (0-4): ").strip()

        if choice == '0':
            print("\n👋 再见！")
            break
        elif choice == '1':
            generate_script_interactive(generator)
        elif choice == '2':
            show_templates(generator)
        elif choice == '3':
            generate_hook_interactive(generator)
        elif choice == '4':
            generate_titles_interactive(generator)
        else:
            print("\n❌ 无效的选择，请重新输入")


def generate_script_interactive(generator: ScriptGenerator):
    """交互式生成脚本"""
    print("\n" + "-" * 60)
    print("📝 生成视频脚本")
    print("-" * 60)

    # 获取主题
    topic = input("\n请输入视频主题: ").strip()
    if not topic:
        print("❌ 主题不能为空")
        return

    # 选择模板
    templates = generator.list_templates()
    print("\n可用模板:")
    for i, tmpl in enumerate(templates, 1):
        print(f"  {i}. {tmpl['display_name']} - {tmpl['description']}")

    template_choice = input(f"\n选择模板 (1-{len(templates)}, 默认1): ").strip()
    if template_choice and template_choice.isdigit():
        template_idx = int(template_choice) - 1
        if 0 <= template_idx < len(templates):
            template_name = templates[template_idx]['name']
        else:
            template_name = templates[0]['name']
    else:
        template_name = templates[0]['name']

    # 可选参数
    duration = input("\n视频时长 (如 3-5min, 直接回车使用默认): ").strip() or None
    custom_req = input("\n额外要求 (可选，直接回车跳过): ").strip() or None

    # 生成脚本
    try:
        print("\n⏳ 正在调用AI生成脚本，请稍候...")
        script = generator.generate_script(
            topic=topic,
            template_name=template_name,
            duration=duration,
            custom_requirements=custom_req
        )

        # 显示脚本预览
        print("\n" + "=" * 60)
        print("✨ 脚本生成成功！")
        print("=" * 60)
        print(f"\n标题: {script.get('title', 'N/A')}")
        print(f"\n共 {len(script.get('sections', []))} 个部分:")
        for i, section in enumerate(script.get('sections', []), 1):
            print(f"  {i}. {section.get('section_name', 'N/A')} ({section.get('duration', 'N/A')})")

        # 保存脚本
        save = input("\n是否保存脚本? (Y/n): ").strip().lower()
        if save != 'n':
            filepath = generator.save_script(script)
            print(f"\n💾 脚本已保存至: {filepath}")

    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")


def show_templates(generator: ScriptGenerator):
    """显示所有可用模板"""
    print("\n" + "-" * 60)
    print("📋 可用脚本模板")
    print("-" * 60)

    templates = generator.list_templates()
    for i, tmpl in enumerate(templates, 1):
        print(f"\n{i}. {tmpl['display_name']}")
        print(f"   ID: {tmpl['name']}")
        print(f"   描述: {tmpl['description']}")


def generate_hook_interactive(generator: ScriptGenerator):
    """交互式生成开场钩子"""
    print("\n" + "-" * 60)
    print("🎣 生成开场钩子")
    print("-" * 60)

    topic = input("\n请输入视频主题: ").strip()
    if not topic:
        print("❌ 主题不能为空")
        return

    try:
        print("\n⏳ 正在生成...")
        hook = generator.generate_hook(topic)
        print("\n" + "=" * 60)
        print("✨ 开场钩子:")
        print("=" * 60)
        print(hook)
    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")


def generate_titles_interactive(generator: ScriptGenerator):
    """交互式生成标题"""
    print("\n" + "-" * 60)
    print("📰 生成视频标题")
    print("-" * 60)

    summary = input("\n请输入视频内容摘要: ").strip()
    if not summary:
        print("❌ 摘要不能为空")
        return

    try:
        print("\n⏳ 正在生成...")
        titles = generator.generate_titles(summary)
        print("\n" + "=" * 60)
        print("✨ 建议的标题:")
        print("=" * 60)
        for i, title in enumerate(titles, 1):
            print(f"{i}. {title}")
    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")


def command_mode(args):
    """命令行模式"""
    try:
        generator = ScriptGenerator()
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        return 1

    try:
        if args.command == 'generate':
            # 生成脚本
            script = generator.generate_script(
                topic=args.topic,
                template_name=args.template or 'popular_science',
                duration=args.duration,
                custom_requirements=args.requirements
            )

            # 保存脚本
            filepath = generator.save_script(script, args.output)
            print(f"✅ 脚本已保存至: {filepath}")
            return 0

        elif args.command == 'templates':
            # 列出模板
            templates = generator.list_templates()
            print("可用模板:")
            for tmpl in templates:
                print(f"  - {tmpl['name']}: {tmpl['display_name']}")
            return 0

    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='科普视频自动化制作系统',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # generate 命令
    generate_parser = subparsers.add_parser('generate', help='生成视频脚本')
    generate_parser.add_argument('topic', help='视频主题')
    generate_parser.add_argument('-t', '--template', help='使用的模板名称')
    generate_parser.add_argument('-d', '--duration', help='视频时长')
    generate_parser.add_argument('-r', '--requirements', help='额外要求')
    generate_parser.add_argument('-o', '--output', help='输出文件名')

    # templates 命令
    subparsers.add_parser('templates', help='列出所有可用模板')

    args = parser.parse_args()

    # 如果没有提供命令，进入交互模式
    if args.command is None:
        interactive_mode()
    else:
        sys.exit(command_mode(args))


if __name__ == '__main__':
    main()
