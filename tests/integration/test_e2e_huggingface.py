# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""End-to-end HuggingFace stack happy path (Story F.f).

Exercises `transformers` + `datasets` + `peft` against the refreshed Phase F
stack: loads a tiny pretrained GPT-2 (`sshleifer/tiny-gpt2`, ~5MB), wraps it
with a `peft` LoRA adapter, builds a synthetic 3-example `datasets.Dataset`,
and runs one forward pass.

The test is gated behind `@pytest.mark.hardware`; `pyve test` skips it by
default (see pyproject.toml `addopts = "-m 'not hardware'"`). Run it
explicitly on developer Apple Silicon hardware:

    pyve test tests/integration/test_e2e_huggingface.py -m hardware

Developer-hardware run procedure (one-time per release):

    1. Build a fresh micromamba-backed env from the refreshed templates env:
           mkdir hf-smoke && cd hf-smoke
           cp <repo>/src/nbfoundry/templates/environment.yml .
           pyve init --backend micromamba

    2. Install nbfoundry from PyPI into that env (not editable from the
       working tree -- per project-essentials, F.c-F.j install from PyPI to
       validate the published surface):
           pyve run pip install nbfoundry==<latest-published>

    3. Run the smoke from inside the repo:
           pyve test tests/integration/test_e2e_huggingface.py -m hardware

Budget: under 90s on M-series silicon. The first run downloads the model
(~5MB) into `~/.cache/huggingface/hub`; subsequent runs read from cache and
finish in well under 30s. If you are behind a corporate proxy or are running
in an environment without internet access, set the `HF_HUB_OFFLINE=1` env
var only *after* the cache has been warmed at least once.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.hardware]

_MODEL_ID = "sshleifer/tiny-gpt2"


def test_tokenizer_round_trip() -> None:
    transformers = pytest.importorskip("transformers")

    tokenizer = transformers.AutoTokenizer.from_pretrained(_MODEL_ID)
    text = "the quick brown fox"
    encoded = tokenizer(text, return_tensors="pt")
    decoded = tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=True)
    assert decoded.strip() == text, f"tokenizer round-trip failed: {decoded!r} != {text!r}"


def test_peft_lora_shrinks_trainable_params_and_forward_pass_works() -> None:
    transformers = pytest.importorskip("transformers")
    datasets = pytest.importorskip("datasets")
    peft = pytest.importorskip("peft")
    torch = pytest.importorskip("torch")

    tokenizer = transformers.AutoTokenizer.from_pretrained(_MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = transformers.AutoModelForCausalLM.from_pretrained(_MODEL_ID)
    base_total = sum(p.numel() for p in base_model.parameters())
    assert base_total > 0

    ds = datasets.Dataset.from_dict(
        {"text": ["hello world", "the quick brown fox", "lorem ipsum dolor sit amet"]}
    )
    assert len(ds) == 3

    lora_config = peft.LoraConfig(
        task_type=peft.TaskType.CAUSAL_LM,
        r=4,
        lora_alpha=8,
        lora_dropout=0.0,
        target_modules=["c_attn"],  # GPT-2 combined Q/K/V projection
    )
    peft_model = peft.get_peft_model(base_model, lora_config)

    trainable = sum(p.numel() for p in peft_model.parameters() if p.requires_grad)
    assert 0 < trainable < base_total / 10, (
        f"LoRA-trainable params ({trainable}) should be materially smaller than "
        f"the base model's total ({base_total}); LoRA is misconfigured if not."
    )

    encoded = tokenizer(ds[0]["text"], return_tensors="pt")
    peft_model.eval()
    with torch.no_grad():
        output = peft_model(**encoded)

    vocab_size = base_model.config.vocab_size
    assert output.logits.shape == (1, encoded["input_ids"].shape[1], vocab_size), (
        f"unexpected logits shape {tuple(output.logits.shape)}; "
        f"expected (1, seq_len={encoded['input_ids'].shape[1]}, vocab={vocab_size})"
    )
