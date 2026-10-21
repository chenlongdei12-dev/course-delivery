#!/usr/bin/env python3
"""切点吸附辅助：候选语义切点 → ±15s 窗口相对音量谷
用法: python3 find_cut_points.py <audio_rms_1s.csv> <候选秒1> <候选秒2> ...
输出: 每个候选点的吸附结果（可直接填入 render_manifest.json）
背景: 腾讯会议录音底噪普遍高于 -60dB，绝对静音谷检测失效，
      本脚本用「窗口中位数 -2dB 以下的最小值」找相对停顿。
"""
import sys, csv, statistics


def main():
    csv_path = sys.argv[1]
    candidates = [int(float(x)) for x in sys.argv[2:]]
    rows = list(csv.reader(open(csv_path)))
    vals = [(int(r[0]), float(r[1])) for r in rows[1:]]  # [1:] 跳过表头 second,rms_db

    for c in candidates:
        win = [(t, d) for (t, d) in vals if abs(t - c) <= 15]
        if not win:
            print(f"{c}s -> 无数据"); continue
        med = statistics.median([d for _, d in win])
        low = [x for x in win if x[1] < med - 2]
        pick = min(low, key=lambda x: x[1]) if low else min(win, key=lambda x: x[1])
        m, s = divmod(pick[0], 60)
        print(f"{c}s -> {pick[0]}s ({m}:{s:02d}, {pick[1]:.1f}dB)")


if __name__ == '__main__':
    main()
