---
name: lipvoice-tts
description: Lipvoice 在线语音合成，支持文本转语音、音色克隆、情绪控制、语速调节。当用户提出生成语音、合成音频、文本配音、TTS、语音克隆等需求时使用。触发词：合成语音、生成语音、配音、TTS、语音合成、文字转语音、音色克隆、Lipvoice。
agent_created: true
---

# Lipvoice 语音合成

Lipvoice 在线语音合成技能。通过 CLI 脚本调用 LipVoice API，支持音色克隆、情绪控制和语速调节。

## 前置条件

用户需要提供 Lipvoice API Key（联系 LipVoice 获取）。

配置方式（任选其一）：
1. 设置环境变量 `LIPVOICE_API_KEY`
2. 运行时交互式输入

## 命令

脚本路径：`scripts/tts.py`。运行前需安装 Python 3，无额外依赖。

### 列出音色模型

```bash
python scripts/tts.py list
```

返回所有已创建的克隆音色模型及其 ID。

### 合成语音

```bash
python scripts/tts.py tts \
  --text "要合成的文本" \
  --audio-id "模型ID" \
  --style 1 \
  --speed 1.0
```

**参数说明：**

| 参数 | 必填 | 说明 |
|------|------|------|
| --text | 是 | 配音文本，最长 500 字 |
| --audio-id | 是 | 音色模型 ID（来自 list 命令） |
| --style | 否 | 1=基础, 2=专业, 3=多语言（默认 1） |
| --genre | 否 | 0=纯语音, 1=情绪控制, 2=参考音频 |
| --speed | 否 | 语速 0.5-1.5，默认 1.0 |
| --happy ~ --calm | 否 | 8 种情绪强度 0-1（genre=1 时使用） |

### 情绪控制

当 genre=1 时，可指定 8 种情绪参数：
--happy（开心）, --angry（愤怒）, --sad（悲伤）, --afraid（恐惧）,
--disgusted（厌恶）, --melancholic（忧郁）, --surprised（惊讶）, --calm（平静）

每个参数取值 0-1，0 表示无，1 表示最强。

### 上传音色

```bash
python scripts/tts.py upload --file "sample.mp3" --name "我的音色"
```

支持 mp3 / wav / m4a 格式，音频需 10-60 秒。

### 查询任务

```bash
python scripts/tts.py query --task-id "任务ID"
```

### 删除音色

```bash
python scripts/tts.py delete --audio-id "模型ID"
```

## 执行流程

1. 如果用户未提供 API Key，提示用户设置环境变量或输入
2. 如果用户未指定模型，先运行 `list` 列出可用模型
3. 根据用户需求组装参数，运行 `tts` 命令
4. 脚本自动等待合成完成并下载音频文件
5. 将生成的 `.wav` 文件路径返回给用户

## 注意事项

- API Key 不要硬编码在对话中，敏感信息
- 生成的音频文件保存在当前工作目录，格式为 `tts_<taskId前8位>.wav`
- 基础模型合成约 8 秒，专业模型+情绪控制约 20-30 秒
