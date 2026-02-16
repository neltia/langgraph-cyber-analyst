# langgraph-cyber-analyst
- 사이버보안을 위한 langgraph agent

### Local LLM
ENV
- Windows 11 WSL2
- Core i7-12700
- RAM 32GB
- RTX 3060

WSL2 install
```
wsl --list --online
wsl --install Ubuntu-24.04
wsl
```

vLLM install
```
curl -LsSf https://astral.sh/uv/install.sh | sh
uv init
uv add vllm fastapi uvicorn
uv run python3 -c 'import vllm; print("vLLM 설치 완료!")'
```

model run with vLLM
- gpt-oss-20b
```
uv run vllm serve openai/gpt-oss-20b
```

- gpt-oss-20b gptq-4bit
```
vllm serve SEOKDONG/gpt-oss-safeguard-20b-kor-enterprise-gptq-4bit \
  --quantization gptq \
  --gpu-memory-utilization 0.9 \
  --max-model-len 2048 \
  --enforce-eager
```

- Qwen/Qwen2.5-14B-Instruct-AWQ
```
uv run vllm serve "Qwen/Qwen2.5-14B-Instruct-AWQ" \
    --port 8000 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 2048 \
    --max-num-seqs 16 \
    --enforce-eager \
    --disable-log-stats
```
