"""Audio-input schemas."""

from pydantic import Field

from tixl_python.api.schemas.common import ApiModel, ResultModel


class AudioDevice(ResultModel):
    name: str
    is_loopback: bool


class GetAudioInputsResult(ResultModel):
    devices: list[AudioDevice] = Field(default_factory=list)
    active: str | None = None
    level: float


class SetAudioInputRequest(ApiModel):
    device: str = ""


class SetAudioInputResult(ResultModel):
    audio_source: str


class AudioRecordingResult(ResultModel):
    path: str | None = None
