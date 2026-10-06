"""Does Kimodo's LLM2Vec.from_pretrained merge an MNTP-style adapter (keys
base_model.model.layers...) with this venv's transformers and peft? A tiny
random Llama stands in for Llama 3 8B, laid out as McGill's repo is: the
adapter and a config.json in one folder, the base named in adapter_config."""
import json
import os
import shutil
import sys
import tempfile

import torch
from peft import LoraConfig, get_peft_model
from transformers import LlamaConfig, LlamaModel, AutoTokenizer, PreTrainedTokenizerFast

from kimodo.model.llm2vec.llm2vec import LLM2Vec

root = tempfile.mkdtemp()
base_dir = os.path.join(root, "base")
mntp_dir = os.path.join(root, "mntp")
cfg = LlamaConfig(vocab_size=128, hidden_size=32, intermediate_size=64, num_hidden_layers=2, num_attention_heads=4,
                  num_key_value_heads=4, max_position_embeddings=64)
torch.manual_seed(0)
base = LlamaModel(cfg)
base.save_pretrained(base_dir)
# A tokenizer the loader can read (any small one will do).
from tokenizers import Tokenizer, models, pre_tokenizers
tok = Tokenizer(models.WordLevel({"[UNK]": 0, "a": 1, "b": 2}, unk_token="[UNK]"))
tok.pre_tokenizer = pre_tokenizers.Whitespace()
ft = PreTrainedTokenizerFast(tokenizer_object=tok, unk_token="[UNK]", eos_token="[UNK]")
ft.save_pretrained(base_dir)

# The adapter, trained (random B so its effect shows), saved like McGill's.
m = LlamaModel.from_pretrained(base_dir)
lcfg = LoraConfig(r=4, lora_alpha=8, target_modules=["q_proj", "v_proj"], base_model_name_or_path=base_dir)
pm = get_peft_model(m, lcfg)
for n, p in pm.named_parameters():
    if "lora_B" in n:
        torch.nn.init.normal_(p, std=0.5)
pm.save_pretrained(mntp_dir)
shutil.copy(os.path.join(base_dir, "config.json"), os.path.join(mntp_dir, "config.json"))
ft.save_pretrained(mntp_dir)
ac = json.load(open(os.path.join(mntp_dir, "adapter_config.json")))
ac["base_model_name_or_path"] = base_dir
json.dump(ac, open(os.path.join(mntp_dir, "adapter_config.json"), "w"))
with open(os.path.join(mntp_dir, "adapter_config.json")) as f:
    print("adapter base:", json.load(f)["base_model_name_or_path"] == base_dir)
from safetensors import safe_open
with safe_open(os.path.join(mntp_dir, "adapter_model.safetensors"), "pt") as f:
    print("adapter keys like:", sorted(f.keys())[0])

# What the merge should give.
merged_ref = pm.merge_and_unload().layers[0].self_attn.q_proj.weight.detach().clone()
base_w = base.layers[0].self_attn.q_proj.weight.detach().clone()

l2v = LLM2Vec.from_pretrained(mntp_dir, peft_model_name_or_path=None, torch_dtype=torch.float32)
model = l2v.model
w = None
for n, p in model.named_parameters():
    if n.endswith("layers.0.self_attn.q_proj.weight") or n.endswith("layers.0.self_attn.q_proj.base_layer.weight"):
        w = p.detach()
        print("found", n)
print("type:", type(model).__name__)
print("differs from base:", float((w - base_w).abs().max()))
print("matches the merge:", float((w - merged_ref).abs().max()))
shutil.rmtree(root)
