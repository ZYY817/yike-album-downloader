# File: tools/yike-album/main.py
"""一刻相册批量下载工具 - 统一入口"""
import sys

def print_banner():
    print("=" * 70)
    print("  一刻相册批量下载工具 v1.0.0")
    print("=" * 70)
    print()

def print_menu():
    print("请选择操作：")
    print("  1. 完整流程（推荐）- 登录→下载→验证→整理")
    print("  2. 仅登录获取Cookie")
    print("  3. 仅下载照片")
    print("  4. 仅下载视频")
    print("  5. 验证下载完整性")
    print("  6. 按日期整理照片")
    print("  7. 查看下载统计")
    print("  8. 核对数量")
    print("  0. 退出")
    print()

def run_full_workflow():
    print("\n开始完整流程...")
    print("\n[步骤1/5] 登录获取Cookie")
    import probe
    probe.main()
    print("\n[步骤2/5] 下载照片")
    import download
    download.main()
    print("\n[步骤3/5] 下载视频")
    import download_video_final
    download_video_final.main()
    print("\n[步骤4/5] 验证完整性")
    import verify_download
    verify_download.main()
    print("\n[步骤5/5] 按日期整理")
    choice = input("\n是否按日期整理照片？(y/n): ").strip().lower()
    if choice == 'y':
        import organizer
        organizer.main()
    print("\n✓ 全部完成！")

def main():
    print_banner()
    while True:
        print_menu()
        choice = input("请输入选项 (0-8): ").strip()
        if choice == '0':
            print("\n再见！")
            sys.exit(0)
        elif choice == '1':
            run_full_workflow()
        elif choice == '2':
            import probe
            probe.main()
        elif choice == '3':
            import download
            download.main()
        elif choice == '4':
            import download_video_final
            download_video_final.main()
        elif choice == '5':
            import verify_download
            verify_download.main()
        elif choice == '6':
            import organizer
            organizer.main()
        elif choice == '7':
            import stats
            stats.main()
        elif choice == '8':
            import check_integrity
            check_integrity.main()
        else:
            print("\n无效选项，请重新输入")
        input("\n按回车键继续...")
        print("\n" * 2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断，退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)
