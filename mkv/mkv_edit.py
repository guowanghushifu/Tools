#!/usr/bin/env python3
import json
import subprocess
import os
import sys
from typing import List, Dict, Any, Optional

# ... (其他函数 check_mkvtoolnix, get_mkv_info, display_tracks, select_tracks_to_keep 保持不变) ...
# display_tracks 确保存在，这里省略以减少篇幅，实际代码中需要它

def check_mkvtoolnix():
    """检查 mkvmerge 是否可用"""
    try:
        subprocess.run(['mkvmerge', '--version'], capture_output=True, check=True)
    except FileNotFoundError:
        print("错误：mkvmerge 未找到。请确保 mkvtoolnix 已安装并在 PATH 中。")
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("错误：mkvmerge 执行失败，请检查 mkvtoolnix 安装。")
        sys.exit(1)

def get_mkv_info(filepath: str) -> Optional[Dict[str, Any]]:
    """使用 mkvmerge -J 获取 mkv 文件信息"""
    try:
        process = subprocess.run(
            ['mkvmerge', '-J', filepath],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(process.stdout)
    except subprocess.CalledProcessError as e:
        print(f"错误：无法读取 MKV 文件信息: {filepath}")
        print(f"mkvmerge 错误: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print("错误：解析 mkvmerge 输出的 JSON 失败。")
        return None

def display_tracks(tracks_data: List[Dict[str, Any]], title: str = "轨道信息"):
    """打印轨道信息"""
    if not tracks_data:
        print(f"\n--- {title} ---")
        print("  (没有轨道信息可显示)")
        print("-------------------------------------------------------------------------------")
        return

    print(f"\n--- {title} ---")
    w_num = 3; w_type = 10; w_id = 3; w_lang = 5; w_codec = 18; w_name = 30; w_def = 6
    header = (
        f"{'编号':<{w_num-1}}| {'类型':<{w_type-2}} | {'ID':<{w_id}} | {'语言':<{w_lang-2}} | "
        f"{'编解码':<{w_codec-3}} | {'名称':<{w_name-2}} | {'默认轨':<{w_def-3}}"
    )
    print(header)
    separator = (
        f"{'-'*w_num}-+-{'-'*w_type}-+-{'-'*w_id}-+-{'-'*w_lang}-+-"
        f"{'-'*w_codec}-+-{'-'*w_name}-+-{'-'*w_def}"
    )
    print(separator)

    for i, track in enumerate(tracks_data):
        track_type = track['type'].capitalize()
        track_id = track['id']
        lang = track['properties'].get('language', '未知')
        codec_orig = track['codec']
        name_orig = track['properties'].get('track_name', '无')
        is_default = track['properties'].get('default_track', False)

        codec_display = codec_orig[:w_codec-3] + "..." if len(codec_orig) > w_codec else codec_orig
        name_display = name_orig[:w_name-3] + "..." if len(name_orig) > w_name else name_orig
        default_display = '是' if is_default else '否'

        print(
            f"{i+1:<{w_num}} | {track_type:<{w_type}} | {track_id:<{w_id}} | {lang:<{w_lang}} | "
            f"{codec_display:<{w_codec}} | {name_display:<{w_name}} | {default_display:<{w_def}}"
        )
    print("-" * len(separator))

def select_tracks_to_keep(all_tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """让用户选择要保留的音轨和字幕轨"""
    video_tracks = [t for t in all_tracks if t['type'] == 'video']
    audio_tracks = [t for t in all_tracks if t['type'] == 'audio']
    subtitle_tracks = [t for t in all_tracks if t['type'] == 'subtitles']

    track_map_to_original_data = {} 
    current_display_num = 1
    
    print("\n视频轨道 (默认全部保留):")
    if not video_tracks:
        print("  (此文件中没有视频轨道)")
    for track in video_tracks:
        track_map_to_original_data[current_display_num] = track
        print(f"  {current_display_num}. ID: {track['id']}, 语言: {track['properties'].get('language', 'N/A')}, "
              f"编解码: {track['codec']}, 名称: {track['properties'].get('track_name', 'N/A')}")
        current_display_num += 1
    
    kept_tracks = list(video_tracks) 

    audio_selection_start_num = current_display_num
    audio_selection_end_num = audio_selection_start_num

    if audio_tracks:
        print("\n音频轨道:")
        for track in audio_tracks:
            track_map_to_original_data[current_display_num] = track
            print(f"  {current_display_num}. ID: {track['id']}, 语言: {track['properties'].get('language', 'N/A')}, "
                  f"编解码: {track['codec']}, 名称: {track['properties'].get('track_name', 'N/A')}")
            current_display_num += 1
        audio_selection_end_num = current_display_num

        while True:
            prompt_range_audio = f"{audio_selection_start_num}"
            if audio_selection_end_num - 1 > audio_selection_start_num:
                prompt_range_audio = f"从 {audio_selection_start_num} 到 {audio_selection_end_num - 1}"
            elif not audio_tracks :
                prompt_range_audio = "无可用"
            
            raw_input_audio = input(
                f"\n请输入要保留的音频轨道编号 ({prompt_range_audio}), 用逗号分割,\n"
                f"或输入 'all' 保留全部, 'none' 不保留 (直接回车等同于 'none'): "
            ).strip()
            selected_audio_indices = []
            valid_input = True
            if raw_input_audio.lower() == 'all':
                selected_audio_indices = list(range(audio_selection_start_num, audio_selection_end_num))
            elif raw_input_audio.lower() == 'none' or not raw_input_audio:
                selected_audio_indices = []
            elif raw_input_audio:
                try:
                    selected_audio_indices = [int(x.strip()) for x in raw_input_audio.split(',')]
                    for i_val in selected_audio_indices:
                        if not (audio_selection_start_num <= i_val < audio_selection_end_num):
                            print(f"无效的音频轨道编号: {i_val}")
                            valid_input = False
                            break
                except ValueError:
                    print("输入格式错误，请输入数字并用逗号分割。")
                    valid_input = False
            
            if valid_input:
                for i_val in selected_audio_indices:
                    if i_val in track_map_to_original_data:
                        kept_tracks.append(track_map_to_original_data[i_val])
                    else:
                        print(f"警告: 尝试添加未映射的轨道编号 {i_val}")
                break
    else:
        print("\n此文件中没有音频轨道可供选择。")

    subtitle_selection_start_num = current_display_num
    subtitle_selection_end_num = subtitle_selection_start_num

    if subtitle_tracks:
        print("\n字幕轨道:")
        for track in subtitle_tracks:
            track_map_to_original_data[current_display_num] = track
            print(f"  {current_display_num}. ID: {track['id']}, 语言: {track['properties'].get('language', 'N/A')}, "
                  f"编解码: {track['codec']}, 名称: {track['properties'].get('track_name', 'N/A')}")
            current_display_num += 1
        subtitle_selection_end_num = current_display_num

        while True:
            prompt_range_subs = f"{subtitle_selection_start_num}"
            if subtitle_selection_end_num -1 > subtitle_selection_start_num:
                prompt_range_subs = f"从 {subtitle_selection_start_num} 到 {subtitle_selection_end_num - 1}"
            elif not subtitle_tracks:
                prompt_range_subs = "无可用"

            raw_input_subs = input(
                f"\n请输入要保留的字幕轨道编号 ({prompt_range_subs}), 用逗号分割,\n"
                f"或输入 'all' 保留全部, 'none' 不保留 (直接回车等同于 'none'): "
            ).strip()
            selected_subtitle_indices = []
            valid_input = True
            if raw_input_subs.lower() == 'all':
                selected_subtitle_indices = list(range(subtitle_selection_start_num, subtitle_selection_end_num))
            elif raw_input_subs.lower() == 'none' or not raw_input_subs:
                selected_subtitle_indices = []
            elif raw_input_subs:
                try:
                    selected_subtitle_indices = [int(x.strip()) for x in raw_input_subs.split(',')]
                    for i_val in selected_subtitle_indices:
                        if not (subtitle_selection_start_num <= i_val < subtitle_selection_end_num):
                            print(f"无效的字幕轨道编号: {i_val}")
                            valid_input = False
                            break
                except ValueError:
                    print("输入格式错误，请输入数字并用逗号分割。")
                    valid_input = False

            if valid_input:
                for i_val in selected_subtitle_indices:
                    if i_val in track_map_to_original_data:
                        kept_tracks.append(track_map_to_original_data[i_val])
                    else:
                        print(f"警告: 尝试添加未映射的轨道编号 {i_val}")
                break
    else:
        print("\n此文件中没有字幕轨道可供选择。")
            
    kept_tracks.sort(key=lambda t: t['id'])
    return kept_tracks

def modify_track_properties(tracks_to_modify: List[Dict[str, Any]]):
    """让用户修改轨道的名称和默认标记，交互简化版"""
    if not tracks_to_modify:
        print("\n没有选定轨道用于输出，跳过属性修改。")
        return

    # 首先询问用户是否要进入修改模式
    initial_choice = input("\n是否需要修改所选轨道的名称或默认标记? (y/n, 直接回车表示 n): ").strip().lower()
    if initial_choice != 'y':
        return

    while True: # 主循环，用于连续修改轨道
        print("\n--- 当前轨道配置 (可供修改) ---")
        # 重新排序并显示，确保编号是基于当前 tracks_to_modify 列表
        # tracks_to_modify.sort(key=lambda t: (t['type'], t['id'])) # 排序以保持一致性
        display_tracks(tracks_to_modify, "待修改/输出的轨道")
        
        prompt_message = (
            f"请输入要修改的轨道编号 (1-{len(tracks_to_modify)}), "
            "或输入 'f' 完成所有修改并继续下一步: "
        )
        track_num_str = input(prompt_message).strip()

        if track_num_str.lower() == 'f':
            print("完成轨道属性修改。")
            break # 退出主修改循环

        try:
            track_idx = int(track_num_str) - 1
            if not (0 <= track_idx < len(tracks_to_modify)):
                print("无效的轨道编号。请重新输入。")
                continue # 继续主循环，提示用户重新输入

            selected_track = tracks_to_modify[track_idx]
            print(f"\n--- 正在修改轨道 {track_idx+1} (ID: {selected_track['id']}, 类型: {selected_track['type'].capitalize()}) ---")
            
            # 修改名称
            current_name = selected_track['properties'].get('track_name', '')
            new_name_prompt = f"  新名称 (当前: '{current_name if current_name else '无'}', 直接回车不修改, 输入 '-' 删除名称): "
            new_name_input = input(new_name_prompt).strip()

            if new_name_input == '-':
                if 'track_name' in selected_track['properties']:
                    del selected_track['properties']['track_name']
                print(f"  轨道 {track_idx+1} 的名称已删除。")
            elif new_name_input: # User entered something other than '-' or empty
                selected_track['properties']['track_name'] = new_name_input
            # If new_name_input is empty, do nothing (keep current_name)

            # 修改默认标记 (仅对音频和字幕轨道)
            if selected_track['type'] in ['audio', 'subtitles']:
                current_default = selected_track['properties'].get('default_track', False)
                default_str = input(f"  设为默认轨道? (y/n, 当前: {'是' if current_default else '否'}, 直接回车不修改): ").strip().lower()
                if default_str == 'y':
                    selected_track['properties']['default_track'] = True
                    # 如果设为默认，确保同类型的其他轨道不是默认
                    for i, t in enumerate(tracks_to_modify):
                        if t['type'] == selected_track['type'] and i != track_idx:
                            if 'default_track' in t['properties']: # Only change if key exists
                                t['properties']['default_track'] = False
                            # If key doesn't exist, mkvmerge would treat it as not default anyway
                    print(f"  轨道 {track_idx+1} 已设为默认。同类型的其他轨道已取消默认标记（如有）。")
                elif default_str == 'n':
                    selected_track['properties']['default_track'] = False
            
            print(f"--- 轨道 {track_idx+1} 修改完毕 ---")
            # 循环将自动重新显示列表

        except ValueError:
            print("无效的输入，请输入数字或 'f'。")
        except Exception as e:
            print(f"修改轨道时发生错误: {e}")
            # 可以选择是 continue 还是 break，这里选择 continue

def build_mkvmerge_command(input_filepath: str, output_filepath: str, final_tracks: List[Dict[str, Any]], original_mkv_data: Dict[str, Any]) -> List[str]:
    """构建 mkvmerge 命令"""
    command = ['mkvmerge', '-q'] 
    command.extend(['-o', output_filepath])

    original_tracks_info = original_mkv_data.get('tracks', [])

    video_track_ids = [str(t['id']) for t in final_tracks if t['type'] == 'video']
    audio_track_ids = [str(t['id']) for t in final_tracks if t['type'] == 'audio']
    subtitle_track_ids = [str(t['id']) for t in final_tracks if t['type'] == 'subtitles']

    # Track selection arguments
    if video_track_ids:
        command.extend(['--video-tracks', ','.join(video_track_ids)])
    elif any(t['type'] == 'video' for t in original_tracks_info): 
        command.extend(['--no-video'])

    if audio_track_ids:
        command.extend(['--audio-tracks', ','.join(audio_track_ids)])
    elif any(t['type'] == 'audio' for t in original_tracks_info):
        command.extend(['--no-audio'])

    if subtitle_track_ids:
        command.extend(['--subtitle-tracks', ','.join(subtitle_track_ids)])
    elif any(t['type'] == 'subtitles' for t in original_tracks_info):
        command.extend(['--no-subtitles'])

    # Track property arguments
    for track in final_tracks:
        track_id_str = str(track['id'])
        
        track_name_to_set = track['properties'].get('track_name')
        if track_name_to_set is not None : # Handles empty string as clearing, None as not set or explicitly cleared
            command.extend(['--track-name', f"{track_id_str}:{track_name_to_set}"])
        elif 'track_name' not in track['properties']: # Explicitly no name
             command.extend(['--track-name', f"{track_id_str}:"])


        is_default_explicitly_set = 'default_track' in track['properties']
        is_default = track['properties'].get('default_track', False)

        if is_default_explicitly_set: 
             command.extend(['--default-track', f"{track_id_str}:{'1' if is_default else '0'}"])
        # else: If 'default_track' property is not present, mkvmerge will use its own defaults
        # or the original file's flags if the track was simply passed through without this property being touched.

    command.append(input_filepath)
    return command

def main():
    check_mkvtoolnix()

    while True:
        mkv_filepath = input("请输入 MKV 文件路径: ").strip()
        if not os.path.isfile(mkv_filepath):
            print(f"错误: 文件 '{mkv_filepath}' 不存在或不是一个文件。请重新输入。")
        elif not mkv_filepath.lower().endswith('.mkv'):
            warn_msg = f"警告: 文件 '{mkv_filepath}' 可能不是 MKV 文件。"
            if input(f"{warn_msg} 是否继续? (y/n): ").lower() != 'y':
                continue
            break
        else:
            break
            
    mkv_data_original = get_mkv_info(mkv_filepath) # Store original data
    if not mkv_data_original or 'tracks' not in mkv_data_original:
        print("无法获取轨道信息，脚本终止。")
        return

    all_tracks_original = mkv_data_original.get('tracks', [])
    if not all_tracks_original:
        print("MKV 文件中未找到任何轨道。")
        return
        
    all_tracks_original.sort(key=lambda t: t['id'])
    display_tracks(all_tracks_original, "原始 MKV 轨道信息")

    kept_tracks_after_selection = select_tracks_to_keep(all_tracks_original)
    
    if not kept_tracks_after_selection:
        print("\n没有选择任何轨道保留。操作中止。")
        return

    print("\n--- 用户选择后保留的轨道 ---")
    kept_tracks_after_selection.sort(key=lambda t: t['id']) # Sort for consistent display
    display_tracks(kept_tracks_after_selection, "用户选择后保留的轨道")

    # 调用修改后的函数
    modify_track_properties(kept_tracks_after_selection) # This will modify the list in-place

    print("\n--- 最终轨道配置 ---")
    kept_tracks_after_selection.sort(key=lambda t: t['id']) # Sort again after potential modifications
    display_tracks(kept_tracks_after_selection, "最终轨道配置 (用于生成新文件)")

    base, ext = os.path.splitext(mkv_filepath)
    output_filepath_base = f"{base}_modified"
    output_filepath = f"{output_filepath_base}{ext}"
    
    count = 1
    while os.path.exists(output_filepath):
        overwrite_choice = input(f"输出文件 '{output_filepath}' 已存在。是否覆盖(o), 重命名(r), 或取消(c)? [o/r/c]: ").lower()
        if overwrite_choice == 'o':
            break
        elif overwrite_choice == 'r':
            output_filepath = f"{output_filepath_base}_{count}{ext}"
            count += 1
        elif overwrite_choice == 'c':
            print("操作取消。")
            return
        else:
            print("无效选择。")

    # Pass original mkv_data to build_mkvmerge_command for --no-... logic
    mkvmerge_cmd = build_mkvmerge_command(mkv_filepath, output_filepath, kept_tracks_after_selection, mkv_data_original)
    
    print("\n将执行以下 mkvmerge 命令:")
    print(" ".join([f'"{c}"' if (" " in c or ":" in c) and not c.startswith('-') else c for c in mkvmerge_cmd]))
    
    confirm_run = input("\n是否继续执行? (y/n): ").strip().lower()
    if confirm_run == 'y':
        print(f"\n正在生成新的 MKV 文件: {output_filepath} ...")
        try:
            process = subprocess.Popen(mkvmerge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                print("成功!")
                if stdout and stdout.strip(): print("mkvmerge 标准输出:\n", stdout)
                if stderr and stderr.strip(): print("mkvmerge 警告/信息:\n", stderr)
            else:
                print("\n错误: mkvmerge 执行失败。 返回码:", process.returncode)
                if stdout and stdout.strip(): print("mkvmerge 标准输出:\n", stdout)
                if stderr and stderr.strip(): print("mkvmerge 错误信息:\n", stderr)

        except Exception as e:
            print(f"\n执行mkvmerge时发生未知错误: {e}")
    else:
        print("操作已取消。")

if __name__ == "__main__":
    main()
