#!/usr/bin/env python3
"""夸克网盘 Cookie 获取/验证/Chrome 解密
用法:
  python3 quark_cookie.py --check            # 验证现有 cookie（打印容量）
  python3 quark_cookie.py --from-chrome      # 从本机 Chrome 解密提取（需 Keychain 授权）
  python3 quark_cookie.py --from-chrome --check
实测要点:
- Chrome v10 cookie = AES-CBC(PBKDF2(keychain 'Chrome Safe Storage', b'saltysalt', 1003, 16B), iv=16空格)
- 新版 Chrome 解密后前 32 字节是 SHA256 hash 前缀，需剥掉
- AppleScript 控制 Chrome 会报 -10004 权限违例，别走那条路
"""
import sys, os, subprocess, sqlite3, hashlib, tempfile, urllib.request, json

HERE = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(HERE, 'cookie.txt')
NEED = ['__pus', '__puus', '__kp', '__kps']


def from_chrome():
    src = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies')
    if not os.path.exists(src):
        print('未找到 Chrome Cookie 库', file=sys.stderr); return 1
    r = subprocess.run(['security', 'find-generic-password', '-w', '-s', 'Chrome Safe Storage'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print('读取 Keychain 失败（需授权）: ' + r.stderr.strip()[:100], file=sys.stderr); return 1
    key = hashlib.pbkdf2_hmac('sha1', r.stdout.strip().encode(), b'saltysalt', 1003, dklen=16)

    try:
        from Crypto.Cipher import AES
    except ImportError:
        print('缺少 pycryptodome: pip install pycryptodome', file=sys.stderr); return 1

    fd, db = tempfile.mkstemp(suffix='.db'); os.close(fd)
    shutil_copy(src, db)
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT host_key, name, encrypted_value, value FROM cookies WHERE host_key LIKE '%quark.cn'"
    ).fetchall()
    conn.close(); os.unlink(db)

    def decrypt(enc):
        if enc[:3] in (b'v10', b'v20'):
            dec = AES.new(key, AES.MODE_CBC, b' ' * 16).decrypt(enc[3:])
            pad = dec[-1]
            if isinstance(pad, int) and 1 <= pad <= 16:
                dec = dec[:-pad]
            if len(dec) > 32:
                dec = dec[32:]  # 剥 hash 前缀
            return dec.decode('utf-8', 'ignore')
        return (enc or b'').decode('utf-8', 'ignore')

    pairs = []
    for host, name, enc, val in rows:
        v = val if val else decrypt(enc)
        if v and host.endswith('quark.cn'):
            pairs.append((name, v))
    cookie = '; '.join(f'{n}={v}' for n, v in pairs)
    core = [n for n in NEED if n in dict(pairs)]
    if len(core) < 2:
        print(f'核心登录字段不足（{core}）——Chrome 可能未登录夸克，先登录再跑', file=sys.stderr); return 1
    with open(COOKIE_FILE, 'w') as f:
        f.write(cookie)
    print(f'OK {len(pairs)} 字段 -> {COOKIE_FILE}')
    return 0


def shutil_copy(src, dst):
    import shutil; shutil.copyfile(src, dst)


def check():
    if not os.path.exists(COOKIE_FILE):
        print('无 cookie.txt，先 --from-chrome 或手动写入', file=sys.stderr); return 1
    cookie = open(COOKIE_FILE).read().strip()
    req = urllib.request.Request(
        'https://drive-pc.quark.cn/1/clouddrive/member?pr=ucpro&fr=pc&fetch_share=true',
        headers={'Cookie': cookie, 'Referer': 'https://pan.quark.cn/', 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        if d.get('code') == 0:
            m = d['data']
            print(f"OK 已登录，容量 {m['use_capacity']/2**30:.1f}GB / {m['total_capacity']/2**30:.0f}GB")
            return 0
        print('Cookie 失效: ' + str(d.get('message')), file=sys.stderr); return 1
    except Exception as e:
        print(f'请求失败: {e}', file=sys.stderr); return 1


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--check' in args:
        sys.exit(check())
    if '--from-chrome' in args:
        rc = from_chrome()
        if rc == 0 and '--check' in args:
            rc = check()
        sys.exit(rc)
    print(__doc__); sys.exit(2)
