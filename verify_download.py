# File: tools/yike-album/verify_download.py
"""验证所有视频是否下载完成"""
import json
from pathlib import Path
from config import DOWNLOAD_DIR

def main():
    print("=" * 60)
    print("  视频下载完整性验证")
    print("=" * 60)
    
    # 加载原始失败列表
    failed_file = DOWNLOAD_DIR / "_failed.json"
    if not failed_file.exists():
        print(f"\n[错误] 未找到原始失败列表: {failed_file}")
        return
    
    failed_list = json.loads(failed_file.read_text(encoding="utf-8"))
    print(f"\n原始待下载视频数: {len(failed_list)}")
    
    # 加载元数据
    meta_file = DOWNLOAD_DIR / "_photo_meta.json"
    if not meta_file.exists():
        print(f"\n[错误] 未找到元数据文件: {meta_file}")
        return
    
    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
    meta_dict = {str(item["fsid"]): item for item in meta_data}
    
    # 扫描已下载的文件
    downloaded_files = {}
    for ext in ["*.mp4", "*.mov", "*.MP4", "*.MOV"]:
        for f in DOWNLOAD_DIR.glob(ext):
            if not f.name.startswith("_"):
                downloaded_files[f.name] = f
    
    print(f"本地视频文件数: {len(downloaded_files)}")
    
    # 核对每个视频
    print(f"\n{'=' * 60}")
    print("  逐个核对")
    print(f"{'=' * 60}\n")
    
    success_count = 0
    missing_count = 0
    size_mismatch_count = 0
    missing_list = []
    size_mismatch_list = []
    
    for video in failed_list:
        fsid = str(video["fsid"])
        name = video.get("name", f"{fsid}.mp4")
        
        # 检查文件是否存在
        if name not in downloaded_files:
            missing_count += 1
            missing_list.append({"fsid": fsid, "name": name})
            print(f"  [缺失] {name}")
            continue
        
        # 检查文件大小
        local_file = downloaded_files[name]
        actual_size = local_file.stat().st_size
        
        if fsid in meta_dict:
            expected_size = meta_dict[fsid].get("size", 0)
            if expected_size and actual_size != expected_size:
                size_mismatch_count += 1
                size_mismatch_list.append({
                    "fsid": fsid,
                    "name": name,
                    "expected": expected_size,
                    "actual": actual_size
                })
                print(f"  [大小不符] {name}: "
                      f"期望{expected_size:,} 实际{actual_size:,}")
                continue
        
        success_count += 1
    
    # 输出统计
    print(f"\n{'=' * 60}")
    print("  验证结果")
    print(f"{'=' * 60}\n")
    print(f"  待下载总数:   {len(failed_list)}")
    print(f"  下载成功:     {success_count}")
    print(f"  文件缺失:     {missing_count}")
    print(f"  大小不符:     {size_mismatch_count}")
    
    if missing_count == 0 and size_mismatch_count == 0:
        print(f"\n  ✓ 全部下载完成! 所有{len(failed_list)}个视频均已成功下载")
    else:
        print(f"\n  ✗ 发现问题:")
        if missing_count > 0:
            print(f"     - {missing_count}个文件缺失")
        if size_mismatch_count > 0:
            print(f"     - {size_mismatch_count}个文件大小不符")
    
    # 保存问题列表
    if missing_list:
        missing_file = DOWNLOAD_DIR / "_still_missing.json"
        missing_file.write_text(
            json.dumps(missing_list, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n  缺失列表已保存: {missing_file}")
    
    if size_mismatch_list:
        mismatch_file = DOWNLOAD_DIR / "_size_mismatch.json"
        mismatch_file.write_text(
            json.dumps(size_mismatch_list, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"  大小不符列表已保存: {mismatch_file}")
    
    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    main()
