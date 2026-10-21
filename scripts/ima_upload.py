#!/usr/bin/env python3
"""ima COS 直传（凭据来自 mcp__ima-mcp__create_media 的 cos_credential）
用法: python3 ima_upload.py <cred.json> <本地文件>
实测要点已内置：
- secret_key 用原始字符串（不要 base64 解码）
- FormatString 末尾 = headers 段自带 \n，不再补
- 只签 host 头；带 x-cos-security-token
"""
import sys, json, hmac, hashlib, time, urllib.request, urllib.error, re


def upload(cred_file, local_path):
    with open(cred_file) as f:
        cred = json.load(f)
    with open(local_path, 'rb') as f:
        data = f.read()

    secret_id = cred['secret_id']
    secret_key = cred['secret_key']  # 原样使用！
    token = cred['token']
    host = f"{cred['bucket_name']}.cos.{cred['region']}.myqcloud.com"
    key = cred['cos_key'].lstrip('/')

    now = int(time.time())
    qt = f"{now};{now + 600}"
    fmt = f"put\n/{key}\n\nhost={host}\n"
    s1 = hashlib.sha1(fmt.encode()).hexdigest()
    sts = f"sha1\n{qt}\n{s1}\n"
    kk = hmac.new(secret_key.encode(), qt.encode(), hashlib.sha1).hexdigest()
    sig = hmac.new(kk.encode(), sts.encode(), hashlib.sha1).hexdigest()
    auth = (f"q-sign-algorithm=sha1&q-ak={secret_id}&q-sign-time={qt}"
            f"&q-key-time={qt}&q-header-list=host&q-url-param-list=&q-signature={sig}")

    req = urllib.request.Request(f"https://{host}/{key}", data=data, method='PUT')
    req.add_header('Authorization', auth)
    req.add_header('x-cos-security-token', token)
    req.add_header('Content-Type', 'text/markdown')
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            print(f"SUCCESS {r.status}")
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'ignore')
        code = re.search(r'<Code>(.*?)</Code>', body)
        print(f"FAIL HTTP {e.code}: {code.group(1) if code else body[:200]}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(upload(sys.argv[1], sys.argv[2]))
