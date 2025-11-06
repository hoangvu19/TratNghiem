from flask import Flask, request, jsonify
import os
try:
    from flask_cors import CORS
except Exception:
    CORS = None

app = Flask(__name__)
if CORS is not None:
    CORS(app)

try:
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer('all-MiniLM-L6-v2')
    USE_EMBED = True
except Exception:
    model = None
    USE_EMBED = False

try:
    from rapidfuzz import fuzz
    USE_RAPIDFUZZ = True
except Exception:
    USE_RAPIDFUZZ = False

def score_with_embeddings(ref, cand):
    if not USE_EMBED:
        return None
    emb = model.encode([ref, cand], convert_to_tensor=True)
    sim = util.pytorch_cos_sim(emb[0], emb[1]).item()
    # convert -1..1 to 0..100
    return int(round((sim + 1) / 2 * 100))

def score_with_rapidfuzz(ref, cand):
    if not USE_RAPIDFUZZ:
        return None
    # token set ratio is good for order-insensitive match
    return int(round(fuzz.token_set_ratio(ref, cand)))

def suggest_study_tips(ref):
    # naive tips generator: extract keywords (split by common separators)
    words = [w for w in ref.replace('\n',' ').split() if len(w)>3]
    kws = list(dict.fromkeys(words))[:8]
    tips = []
    if kws:
        tips.append('Hãy tách thành các cụm nhỏ và nhẩm/viết lại: ' + ', '.join(kws))
    tips.append('Lặp lại theo phương pháp spaced-repetition: học ngắn, xen kẽ, lặp lại nhiều lần.')
    tips.append('Tạo flashcards cho các ý chính và tự kiểm tra bằng cách trả lời ngắn trong 1 phút.')
    return tips

@app.route('/ai/grade', methods=['POST'])
def grade():
    data = request.get_json(force=True)
    ref = data.get('answer','') or ''
    cand = data.get('response','') or ''
    text_check = bool(data.get('text_check', False))
    # Prefer embeddings
    score = None
    if USE_EMBED and ref and cand:
        try:
            score = score_with_embeddings(ref, cand)
        except Exception:
            score = None
    if score is None and USE_RAPIDFUZZ and ref and cand:
        try:
            score = score_with_rapidfuzz(ref, cand)
        except Exception:
            score = None
    if score is None:
        # basic token overlap
        rset = set([w.lower() for w in ref.split() if len(w)>2])
        cset = set([w.lower() for w in cand.split() if len(w)>2])
        inter = len(rset & cset)
        uni = len(rset | cset) or 1
        score = int(round(inter/uni*100))

    verdict = 'Đạt' if score>=70 else 'Chưa đạt'
    feedback = f'Điểm tương đồng: {score}%'
    tips = suggest_study_tips(ref)
    return jsonify({'score': score, 'verdict': verdict, 'feedback': feedback, 'tips': tips})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port)
