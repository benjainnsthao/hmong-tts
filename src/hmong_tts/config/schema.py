"""Pydantic schemas for committed starter configurations."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SplitConfig(StrictModel):
    train: float = Field(gt=0, lt=1)
    development: float = Field(gt=0, lt=1)
    test: float = Field(gt=0, lt=1)

    @model_validator(mode="after")
    def ratios_sum_to_one(self) -> SplitConfig:
        if abs(self.train + self.development + self.test - 1.0) > 1e-9:
            raise ValueError("split ratios must sum to 1.0")
        return self


class AudioDataConfig(StrictModel):
    master_sample_rate_hz: Literal[48000]
    master_bit_depth: Literal[24]
    channels: Literal[1]
    processed_sample_rate_hz: Literal[16000]
    min_duration_seconds: float = Field(gt=0)
    max_duration_seconds: float = Field(gt=0)

    @model_validator(mode="after")
    def duration_order(self) -> AudioDataConfig:
        if self.max_duration_seconds <= self.min_duration_seconds:
            raise ValueError("maximum duration must exceed minimum duration")
        return self


class DataConfig(StrictModel):
    schema_version: Literal[1]
    data_root_env: Literal["HMONG_TTS_DATA_ROOT"]
    allow_repository_data: Literal[False]
    primary_training_speaker_id: Literal["spk01"]
    evaluation_speaker_id: Literal["reviewer02"]
    audio: AudioDataConfig
    splits: SplitConfig
    split_key: Literal["normalized_prompt_hash_and_feature_group"]
    real_data_allowed_in_tests: Literal[False]


class CheckpointRef(StrictModel):
    repository: str = Field(min_length=1)
    revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    license: str = Field(min_length=1)
    approved_for_use: bool


class TokenizerConfig(StrictModel):
    type: Literal["character"]
    lowercase: Literal[True]
    preserve_validated_tone_markers: Literal[True]
    normalization_status: Literal["blocked_pending_native_validation"]


class ModelConfig(StrictModel):
    schema_version: Literal[1]
    architecture: Literal["vits"]
    implementation: Literal["transformers_mms"]
    primary_initialization: CheckpointRef
    control_initialization: CheckpointRef
    output_sample_rate_hz: Literal[16000]
    single_speaker: Literal[True]
    tokenizer: TokenizerConfig


class TrainingConfig(StrictModel):
    schema_version: Literal[1]
    precision: Literal["fp16"]
    per_device_batch_size: int = Field(ge=1)
    gradient_accumulation_steps: int = Field(ge=1)
    max_audio_seconds: float = Field(gt=0)
    length_bucketing: Literal[True]
    gradient_clip_norm: float = Field(gt=0)
    learning_rate: float = Field(gt=0)
    save_every_optimizer_steps: int = Field(gt=0)
    evaluate_every_optimizer_steps: int = Field(gt=0)
    keep_best_checkpoints: int = Field(gt=0)
    keep_latest_checkpoint: Literal[True]
    seed: int = Field(ge=0)
    tracker_mode: Literal["local_or_offline_only"]
    sealed_test_set_for_selection: Literal[False]


class EvaluationSetConfig(StrictModel):
    novel_sentences: Literal[100]
    diagnostic_items_minimum: Literal[160]
    application_sentences: Literal[30]
    numbers_names_borrowings: Literal[20]
    stress_inputs: Literal[20]
    invalid_api_inputs: Literal[10]


class EvaluationThresholdConfig(StrictModel):
    normalized_cer_max: float
    word_accuracy_min: float
    pronunciation_acceptable_min: float
    tone_overall_min: float
    tone_each_category_min: float
    naturalness_mos_min: float
    speaker_similarity_mos_min: float
    catastrophic_failure_rate_max: float
    long_input_complete_min: Literal[18]
    api_success_rate_min: float
    gpu_realtime_factor_max: float
    training_vram_gib_max: float

    @model_validator(mode="after")
    def preserve_project_thresholds(self) -> EvaluationThresholdConfig:
        expected = {
            "normalized_cer_max": 0.10,
            "word_accuracy_min": 0.85,
            "pronunciation_acceptable_min": 0.90,
            "tone_overall_min": 0.90,
            "tone_each_category_min": 0.80,
            "naturalness_mos_min": 3.5,
            "speaker_similarity_mos_min": 4.0,
            "catastrophic_failure_rate_max": 0.02,
            "api_success_rate_min": 0.99,
            "gpu_realtime_factor_max": 0.5,
            "training_vram_gib_max": 11.5,
        }
        for field, value in expected.items():
            if getattr(self, field) != value:
                raise ValueError(
                    f"{field} must preserve the authoritative project threshold {value}"
                )
        return self


class EvaluationConfig(StrictModel):
    schema_version: Literal[1]
    selection_split: Literal["development"]
    sealed_test_use: Literal["final_evaluation_only"]
    principal_evaluator: Literal["reviewer02"]
    systems_blinded: Literal[True]
    thresholds_status: Literal["provisional_pending_native_validation"]
    sets: EvaluationSetConfig
    thresholds: EvaluationThresholdConfig


class InferenceConfig(StrictModel):
    schema_version: Literal[1]
    host: str
    port: int = Field(ge=1, le=65535)
    max_input_characters: int = Field(gt=0)
    max_normalized_tokens: int = Field(gt=0)
    workers: Literal[1]
    gpu_queue_concurrency: Literal[1]
    request_timeout_seconds: float = Field(gt=0)
    model_instances: Literal[1]
    seeded_generation: Literal[True]
    public_deployment_enabled: Literal[False]
    normalization_endpoint_public: Literal[False]
    log_request_text: Literal[False]
    log_client_ip: Literal[False]


CONFIG_MODELS: dict[str, type[StrictModel]] = {
    "data": DataConfig,
    "model": ModelConfig,
    "train": TrainingConfig,
    "eval": EvaluationConfig,
    "inference": InferenceConfig,
}
