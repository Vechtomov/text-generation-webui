python server.py \
--model-dir ~/models \
--model meta-llama-3-8b-instruct \
--n_ctx 8192 \
--n-gpu-layers 1000 \
--flash-attn \
--tensorcores \
--use_flash_attention_2 \
--trust-remote-code \
--api \
--api-port 9002 \
--listen