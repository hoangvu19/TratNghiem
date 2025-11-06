import json

def normalize(s):
    if not s: return ''
    try:
        s = s.lower()
    except Exception:
        pass
    return s

def token_score(ref, cand):
    rset = set([w for w in normalize(ref).split() if len(w)>2])
    cset = set([w for w in normalize(cand).split() if len(w)>2])
    if not rset and not cset: return 0
    inter = len(rset & cset)
    uni = len(rset | cset)
    return int(round(inter/uni*100))

def handler(request):
    # Vercel passes a 'request' object with get_data()
    try:
        raw = request.get_data()
        data = json.loads(raw.decode('utf-8')) if raw else {}
    except Exception:
        return ({'error':'invalid json'}, 400, {'Content-Type':'application/json', 'Access-Control-Allow-Origin':'*'})
    ref = data.get('answer','') or ''
    cand = data.get('response','') or ''
    score = token_score(ref, cand)
    verdict = 'Đạt' if score>=70 else 'Chưa đạt'
    feedback = f'Điểm tương đồng: {score}%'
    tips = []
    if ref:
        kws = [w for w in ref.split() if len(w)>3][:6]
        if kws:
            tips.append('Học theo nhóm từ/ý: ' + ', '.join(kws))
    tips.append('Lặp lại theo phương pháp spaced repetition và viết lại các ý chính.')
    body = {'score':score,'verdict':verdict,'feedback':feedback,'tips':tips}
    headers = {'Content-Type':'application/json', 'Access-Control-Allow-Origin':'*'}
    return (json.dumps(body), 200, headers)
