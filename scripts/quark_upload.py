#!/usr/bin/env python3
"""夸克网盘直传上传器（自研，协议来自 alist quark_uc 驱动实测复刻）
用法:
  python3 quark_upload.py <本地文件> <目标父目录fid>
  python3 quark_upload.py <本地目录> <目标父目录fid>      # 目录内全部文件串行
依赖: 同目录 cookie.txt（quark_cookie.py 生成）
协议: pre → 分片auth(auth_key) → PUT OSS(ETag用响应头) → update/hash → commit(XML+callback)
"""
import sys, os, time, json, hashlib, base64, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
COOKIE = open(os.path.join(HERE, 'cookie.txt')).read().strip() if os.path.exists(os.path.join(HERE, 'cookie.txt')) \
    else os.environ.get('QUARK_COOKIE', '')
UA = {'Cookie': COOKIE, 'Referer': 'https://pan.quark.cn/',
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0',
      'Content-Type': 'application/json'}
BASE = 'https://drive-pc.quark.cn/1/clouddrive'


def call(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}?pr=ucpro&fr=pc", data=data, headers=UA,
                                 method='POST' if data else 'GET')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {'code': e.code, 'message': e.read().decode('utf-8', 'ignore')[:200]}


def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.status, r.headers, r.read()


def upload_file(path, pdir_fid):
    name = os.path.basename(path)
    size = os.path.getsize(path)
    now = int(time.time() * 1000)
    mime = 'video/mp4' if name.endswith('.mp4') else 'application/octet-stream'

    pre = call('/file/upload/pre', {
        'ccp_hash_update': True, 'dir_name': '', 'file_name': name,
        'format_type': mime, 'l_created_at': now, 'l_updated_at': now,
        'pdir_fid': pdir_fid, 'size': size})
    if pre.get('code') != 0:
        raise RuntimeError(f"pre: {pre.get('message')}")
    d = pre['data']
    part_size = pre.get('metadata', {}).get('part_size', 4 * 1024 * 1024)
    total = (size + part_size - 1) // part_size
    print(f"[{name}] {size//2**20}MB, {total} 分片")

    md5a, sha1a, etags = hashlib.md5(), hashlib.sha1(), []
    OSS_UA = 'aliyun-sdk-js/6.6.1 Chrome 98.0.4758.80 on Windows 10 64-bit'
    with open(path, 'rb') as f:
        pn = 0
        while True:
            chunk = f.read(part_size)
            if not chunk:
                break
            pn += 1
            md5a.update(chunk); sha1a.update(chunk)
            ts = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
            meta = (f"PUT\n\n{mime}\n{ts}\nx-oss-date:{ts}\nx-oss-user-agent:{OSS_UA}\n"
                    f"/{d['bucket']}/{d['obj_key']}?partNumber={pn}&uploadId={d['upload_id']}")
            a = call('/file/upload/auth', {'auth_info': d['auth_info'], 'auth_meta': meta, 'task_id': d['task_id']})
            if a.get('code') != 0:
                raise RuntimeError(f"auth p{pn}: {a.get('message')}")
            url = f"https://{d['bucket']}.{d['upload_url'][7:]}/{d['obj_key']}?partNumber={pn}&uploadId={d['upload_id']}"
            st, h, _ = http(url, data=chunk, headers={
                'Authorization': a['data']['auth_key'], 'Content-Type': mime,
                'Date': ts, 'x-oss-date': ts, 'x-oss-user-agent': OSS_UA}, method='PUT')
            if st != 200:
                raise RuntimeError(f"PUT p{pn} HTTP {st}")
            etags.append((h.get('ETag') or '').strip('"'))
            print(f"  [{pn}/{total}] ok")

    r = call('/file/update/hash', {'md5': md5a.hexdigest(), 'sha1': sha1a.hexdigest(), 'task_id': d['task_id']})
    if r.get('code') != 0:
        print(f"  [hash] warn: {r.get('message')}")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<CompleteMultipartUpload>\n'
    for i, e in enumerate(etags):
        xml += f"<Part>\n<PartNumber>{i+1}</PartNumber>\n<ETag>{e}</ETag>\n</Part>\n"
    xml += '</CompleteMultipartUpload>'
    cmd5 = base64.b64encode(hashlib.md5(xml.encode()).digest()).decode()
    cb64 = base64.b64encode(json.dumps(d['callback']).encode()).decode()
    ts = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
    meta = (f"POST\n{cmd5}\napplication/xml\n{ts}\nx-oss-callback:{cb64}\nx-oss-date:{ts}\n"
            f"x-oss-user-agent:{OSS_UA}\n/{d['bucket']}/{d['obj_key']}?uploadId={d['upload_id']}")
    a = call('/file/upload/auth', {'auth_info': d['auth_info'], 'auth_meta': meta, 'task_id': d['task_id']})
    if a.get('code') != 0:
        raise RuntimeError(f"commit-auth: {a.get('message')}")
    url = f"https://{d['bucket']}.{d['upload_url'][7:]}/{d['obj_key']}?uploadId={d['upload_id']}"
    st, _, _ = http(url, data=xml.encode(), headers={
        'Authorization': a['data']['auth_key'], 'Content-Type': 'application/xml',
        'Content-MD5': cmd5, 'Date': ts, 'x-oss-callback': cb64, 'x-oss-date': ts,
        'x-oss-user-agent': OSS_UA}, method='POST')
    if st not in (200, 203):
        raise RuntimeError(f"commit HTTP {st}")

    for i in range(30):
        r = call(f"/task?pr=ucpro&fr=pc&task_id={d['task_id']}&retry_index={i}")
        if r.get('code') == 0 and r['data'].get('status') == 2:
            print(f"[{name}] 完成")
            return
        if r.get('code') == 0 and (r['data'].get('status', 0) in (3,) or r['data'].get('status', 1) < 0):
            raise RuntimeError(f"task fail: {r['data']}")
        time.sleep(1.5)
    print(f"[{name}] 任务轮询超时（可能已成功，请 list 验证）")


def main():
    if not COOKIE:
        print('缺 cookie：先跑 quark_cookie.py --from-chrome', file=sys.stderr); return 1
    src, fid = sys.argv[1], sys.argv[2]
    if os.path.isdir(src):
        files = sorted(os.listdir(src))
        fail = []
        for fn in files:
            for attempt in range(2):
                try:
                    upload_file(os.path.join(src, fn), fid); break
                except Exception as e:
                    print(f"  尝试{attempt+1}失败: {e}")
                    if attempt:
                        fail.append(fn)
            time.sleep(2)
        if fail:
            print('失败: ' + ', '.join(fail), file=sys.stderr); return 1
        return 0
    upload_file(src, fid)
    return 0


if __name__ == '__main__':
    sys.exit(main())
