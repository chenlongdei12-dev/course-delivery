#!/usr/bin/env python3
"""逐字稿质检：时间戳单调性、说话人标注、占位符统计、完整率
用法: python3 check_transcript.py <transcript-checked.md>
退出码 0=通过, 1=需人工复核
"""
import sys, re

def main():
    path = sys.argv[1]
    text = open(path, encoding='utf-8').read()
    issues = []

    # 时间戳
    stamps = [(m.group(1), m.start()) for m in re.finditer(r'\((\d{2}:\d{2}:\d{2})\)', text)]
    secs = []
    for s, _ in stamps:
        h, m, sec = map(int, s.split(':'))
        secs.append(h * 3600 + m * 60 + sec)
    back = [i for i in range(1, len(secs)) if secs[i] < secs[i - 1]]
    if back:
        issues.append(f"时间戳回退 {len(back)} 处（首处在第 {back[0]+1} 个时间戳）")

    # 说话人
    speakers = re.findall(r'^([^\s(]{1,20})\(', text, re.M)
    if stamps and len(speakers) < len(stamps) * 0.8:
        issues.append(f"说话人标注率偏低: {len(speakers)}/{len(stamps)}")

    # 占位符
    q = text.count('【？】') + text.count('【?】')
    if q > 20:
        issues.append(f"不确定标注 {q} 处，建议人工复核")

    # 空段
    paras = [p for p in text.split('\n\n') if p.strip()]
    if len(paras) < 10:
        issues.append(f"段落数过少: {len(paras)}")

    print(f"时间戳 {len(stamps)} 个，说话人 {len(speakers)} 个，段落 {len(paras)} 个，不确定标注 {q} 处")
    if issues:
        print("⚠️ " + '；'.join(issues))
        sys.exit(1)
    print("✅ 质检通过")


if __name__ == '__main__':
    main()
