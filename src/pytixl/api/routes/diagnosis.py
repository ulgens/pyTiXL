from ... import __version__
from ..schemas import EmptyResult, GetMetricsResult, HealthResponse
from .main import (
    BridgeDep,
    CapturesDep,
    invoke,
    router,
)

TAG = "Diagnosis"

__all__ = (
    "get_metrics",
    "health",
    "ping",
)


@router.get(
    path="/metrics",
    response_model=GetMetricsResult,
    tags=(TAG,),
)
async def get_metrics(bridge: BridgeDep):
    return await invoke(bridge, "getMetrics")


@router.get(
    path="/health",
    response_model=HealthResponse,
    tags=(TAG,),
)
async def health(bridge: BridgeDep, captures_dir: CapturesDep):
    info = await bridge.version_info()

    return HealthResponse(
        status="ok" if bridge.connected else "degraded",
        connected=bridge.connected,
        tixl_host=bridge.host,
        tixl_port=bridge.port,
        api_version=__version__,
        captures_dir=str(captures_dir),
        protocol_version=info.protocol_version,
        editor_version=info.editor_version,
        requests_sent=bridge.request_count,
        last_error=bridge.last_error,
    )


@router.post(
    path="/ping",
    response_model=EmptyResult,
    tags=(TAG,),
)
async def ping(bridge: BridgeDep):
    return await invoke(bridge, "ping")
