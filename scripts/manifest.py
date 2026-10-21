#!/usr/bin/env python3
"""manifest 进度维护器：阶段幂等与断点续跑的核心
用法:
  python3 manifest.py <工作目录> init
  python3 manifest.py <工作目录> set <stage> done [--kv k=v ...]
  python3 manifest.py <工作目录> get <stage>
  python3 manifest.py <工作目录> next          # 打印下一个未完成阶段
"""
import sys, json, os

STAGES = ['stage1', 'stage2', 'stage3', 'stage4', 'stage5', 'stage6']
MANIFEST = 'manifest.json'


def load(workdir):
    p = os.path.join(workdir, MANIFEST)
    return json.load(open(p)) if os.path.exists(p) else {}


def save(workdir, m):
    with open(os.path.join(workdir, MANIFEST), 'w') as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def main():
    workdir = sys.argv[1]
    cmd = sys.argv[2]
    m = load(workdir)
    if cmd == 'init':
        m = {s: 'pending' for s in STAGES}
        save(workdir, m)
        print(f"init: {STAGES}")
    elif cmd == 'set':
        stage, val = sys.argv[3], sys.argv[4]
        m[stage] = val
        for kv in sys.argv[5:]:
            if kv.startswith('--kv'):
                continue
            if '=' in kv:
                k, v = kv.split('=', 1)
                try:
                    v = json.loads(v)
                except Exception:
                    pass
                m[k] = v
        save(workdir, m)
        print(f"{stage} -> {val}")
    elif cmd == 'get':
        print(m.get(sys.argv[3], 'pending'))
    elif cmd == 'next':
        for s in STAGES:
            if m.get(s) != 'done':
                print(s)
                return
        print('all-done')


if __name__ == '__main__':
    main()
