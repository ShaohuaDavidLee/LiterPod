#!/usr/bin/env python3
"""
用 Gemini 2.5 Flash TTS 把中文对谈脚本合成为双人 WAV 音频。

输入格式(stdin 或 --script-file):
    Speaker1: 第一段台词
    Speaker2: 第二段台词
    Speaker1: ...

输出:一个 WAV 文件(24kHz, 16-bit PCM, mono)

需要环境变量 GEMINI_API_KEY 或 --api-key 参数。

技术说明:
- 模型: gemini-2.5-flash-preview-tts
- 音色: Speaker1→Kore(稳重男声), Speaker2→Puck(活泼女声)
- 多说话人模式一次调用返回完整 PCM,无需拼接
- 输出采样率 24000Hz,16-bit,单声道
"""

import argparse
import os
import sys
import wave
from pathlib import Path


def synthesize(script: str, api_key: str, output_path: Path,
               speaker1_voice: str = "Kore", speaker2_voice: str = "Puck") -> None:
    """调用 Gemini TTS,把脚本合成音频写入 output_path。"""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print(
            "ERROR: google-genai not installed. Run:\n"
            "  pip install google-genai --break-system-packages",
            file=sys.stderr
        )
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Gemini TTS 多说话人模式:直接把带 Speaker 标签的完整脚本作为 content
    # 模型会自动识别并用对应音色朗读每个 speaker 的段落
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=script,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=[
                            types.SpeakerVoiceConfig(
                                speaker="Speaker1",
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=speaker1_voice
                                    )
                                ),
                            ),
                            types.SpeakerVoiceConfig(
                                speaker="Speaker2",
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=speaker2_voice
                                    )
                                ),
                            ),
                        ]
                    )
                ),
            ),
        )
    except Exception as e:
        print(f"ERROR: Gemini TTS API call failed: {e}", file=sys.stderr)
        print("\nCommon causes:", file=sys.stderr)
        print("  - Invalid API key", file=sys.stderr)
        print("  - Quota exceeded (free tier has rate limits)", file=sys.stderr)
        print("  - Script too long (try splitting into chunks)", file=sys.stderr)
        print("  - Network issue (may need proxy for Gemini API)", file=sys.stderr)
        sys.exit(1)

    # 提取 PCM 数据
    try:
        pcm_data = response.candidates[0].content.parts[0].inline_data.data
    except (AttributeError, IndexError) as e:
        print(f"ERROR: Unexpected response format: {e}", file=sys.stderr)
        sys.exit(1)

    # Gemini TTS 返回原始 PCM(16-bit, 24kHz, mono),需要包装成 WAV
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)        # mono
        wf.setsampwidth(2)        # 16-bit
        wf.setframerate(24000)    # 24kHz
        wf.writeframes(pcm_data)

    size_kb = output_path.stat().st_size / 1024
    print(f"✓ Audio saved to {output_path} ({size_kb:.1f} KB)", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Synthesize a two-speaker Chinese podcast from a script using Gemini TTS"
    )
    parser.add_argument("--script-file", type=Path,
                        help="Path to script file (if not given, reads from stdin)")
    parser.add_argument("--output", type=Path, required=True,
                        help="Output WAV file path")
    parser.add_argument("--api-key", type=str, default=None,
                        help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--speaker1-voice", default="Kore",
                        help="Voice for Speaker1 (default: Kore, steady male)")
    parser.add_argument("--speaker2-voice", default="Puck",
                        help="Voice for Speaker2 (default: Puck, upbeat female)")
    args = parser.parse_args()

    # 拿到 API key
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            "ERROR: No Gemini API key provided.\n"
            "  Either set GEMINI_API_KEY environment variable, or pass --api-key.\n"
            "  Get a free key at: https://aistudio.google.com/apikey",
            file=sys.stderr
        )
        sys.exit(1)

    # 读取脚本
    if args.script_file:
        script = args.script_file.read_text(encoding="utf-8")
    else:
        script = sys.stdin.read()

    if not script.strip():
        print("ERROR: Empty script", file=sys.stderr)
        sys.exit(1)

    # 基本校验:脚本里必须有 Speaker1 和 Speaker2 标签
    if "Speaker1:" not in script or "Speaker2:" not in script:
        print(
            "WARNING: Script doesn't contain 'Speaker1:' and 'Speaker2:' tags. "
            "The model may not assign voices correctly.",
            file=sys.stderr
        )

    synthesize(
        script=script,
        api_key=api_key,
        output_path=args.output,
        speaker1_voice=args.speaker1_voice,
        speaker2_voice=args.speaker2_voice,
    )


if __name__ == "__main__":
    main()
