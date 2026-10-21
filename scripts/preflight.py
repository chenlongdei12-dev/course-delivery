#!/usr/bin/env python3
"""环境自检：课程交付流水线依赖盘点
用法: python3 preflight.py [--fix 提示模式]
输出每项 ✓/✗ 与修复指引；全部 ✓ 即可跑全流程。
"""
import sys, subprocess, shutil, platform

OK, MISS = '✓', '✗'


def check(cmd, name, how, fix):
    has = shutil.which(cmd) is not None
    if not has:  # 一些不是 PATH 命令的特判
        pass
    print(f"{OK if has else MISS} {name:24} {how if has else '→ ' + fix}")
    return has


def main():
    print(f"平台: {platform.system()} {platform.release()}")
    if platform.system() != 'Darwin':
        print("⚠️ 视频切片(Swift/AVFoundation)仅 macOS；其余阶段可用")
    results = []
    results.append(check('swift', 'Swift（视频切片）', '系统自带', 'xcode-select --install'))
    results.append(check('node', 'Node 18+', '已装', '官网 https://nodejs.org 安装 LTS'))
    results.append(check('git', 'git', '已装', 'brew install git 或官网'))
    results.append(check('tmeet', 'tmeet CLI（会议导出）', '已装', 'npm install -g @tencentcloud/tmeet@latest'))
    results.append(check('lark-cli', 'lark-cli（飞书）', '已装', '安装飞书连接器，或参考 lark-cli 官方文档'))
    results.append(check('bdpan', 'bdpan（百度网盘）', '已装', 'bash scripts/install-bdpan.sh（需确认）'))
    # python 库
    try:
        import Crypto  # noqa
        print(f"{OK} pycryptodome          已装   （夸克 Cookie 解密用）")
        py_crypto = True
    except ImportError:
        print(f"{MISS} pycryptodome          → pip install pycryptodome")
        py_crypto = False
    results.append(py_crypto)

    # 登录态
    print("\n--- 登录态 ---")
    for cmd, label in [('tmeet auth status', '腾讯会议'), ('lark-cli auth status', '飞书')]:
        r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
        logged = ('logged' in r.stdout.lower()) or ('已登录' in r.stdout) or ('valid' in r.stdout.lower())
        print(f"{OK if logged else MISS} {label:22} {'已登录' if logged else '→ 运行相应 auth login'}")
    r = subprocess.run(['python3', __file__.replace('preflight.py', 'quark_cookie.py'), '--check'],
                       capture_output=True, text=True, timeout=30)
    logged = 'OK' in r.stdout
    print(f"{OK if logged else MISS} {'夸克网盘':22} {'已登录' if logged else '→ python3 scripts/quark_cookie.py --from-chrome'}")
    r = subprocess.run(['bdpan', 'whoami'], capture_output=True, text=True, timeout=30)
    logged = '已登录' in r.stdout
    print(f"{OK if logged else MISS} {'百度网盘':22} {'已登录' if logged else '→ bash scripts/bdpan-login.sh'}")

    n_miss = results.count(False)
    print(f"\n{'✅ 环境就绪' if n_miss == 0 else f'⚠️ 缺 {n_miss} 项，按上面指引补齐'}")
    return 0 if n_miss == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
