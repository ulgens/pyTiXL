"""
"Audio Input" group from TiXL docs

https://github.com/tixl3d/tixl/blob/b6cc584406c76aebf61910f58d1562bf55c4884e/.agentic/DEBUG_PROTOCOL.md#methods
"""

from ..schemas import (
    AudioRecordingResult,
    GetAudioInputsResult,
    SetAudioInputRequest,
    SetAudioInputResult,
)
from .main import (
    BridgeDep,
    invoke,
    router,
)

__all__ = (
    "get_audio_inputs",
    "set_audio_input",
    "start_audio_recording",
    "stop_audio_recording",
)

TAG = "Audio Input"


@router.get(
    path="/audio-inputs",
    response_model=GetAudioInputsResult,
    tags=(TAG,),
)
async def get_audio_inputs(bridge: BridgeDep):
    return await invoke(bridge, "getAudioInputs")


@router.post(
    path="/set-audio-input",
    response_model=SetAudioInputResult,
    tags=(TAG,),
)
async def set_audio_input(body: SetAudioInputRequest, bridge: BridgeDep):
    return await invoke(bridge, "setAudioInput", body)


@router.post(
    path="/start-audio-recording",
    response_model=AudioRecordingResult,
    tags=(TAG,),
)
async def start_audio_recording(bridge: BridgeDep):
    return await invoke(bridge, "startAudioRecording")


@router.post(
    path="/stop-audio-recording",
    response_model=AudioRecordingResult,
    tags=(TAG,),
)
async def stop_audio_recording(bridge: BridgeDep):
    return await invoke(bridge, "stopAudioRecording")
