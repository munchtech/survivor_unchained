"""Licence fields of candidate local image models, from Hugging Face's API (via curl)."""
import json
import subprocess

MODELS = ['black-forest-labs/FLUX.1-schnell', 'Qwen/Qwen-Image', 'HiDream-ai/HiDream-I1-Full',
          'Tongyi-MAI/Z-Image-Turbo', 'stabilityai/stable-diffusion-xl-base-1.0',
          'black-forest-labs/FLUX.1-dev', 'stabilityai/stable-diffusion-3.5-large',
          'black-forest-labs/FLUX.2-dev', 'Qwen/Qwen-Image-2512']
for m in MODELS:
    raw = subprocess.run(['curl', '-s', 'https://huggingface.co/api/models/' + m], capture_output=True, text=True).stdout
    try:
        d = json.loads(raw)
    except ValueError:
        print(m, 'no answer')
        continue
    cd = d.get('cardData') or {}
    print('%-45s %-14s %-30s %s %s' % (m, cd.get('license'), cd.get('license_name', ''), (d.get('lastModified') or '')[:10],
                                        'gated' if d.get('gated') else ''))
