from fastapi import APIRouter, Depends, HTTPException, Query

from mood_record.controller.request.create_mood_record_request import CreateMoodRecordRequest
from mood_record.service.mood_record_service_impl import MoodRecordServiceImpl

mood_record_router = APIRouter(prefix="/mood-record", tags=["mood-record"])


def inject_mood_record_service() -> MoodRecordServiceImpl:
    return MoodRecordServiceImpl.get_instance()


@mood_record_router.post("/create")
def create_mood_record(
    request: CreateMoodRecordRequest,
    mood_record_service: MoodRecordServiceImpl = Depends(inject_mood_record_service),
    user_id: str | None = None,  # TODO: MP-04 후 JWT Cookie에서 주입 (Depends(get_authenticated_user_id))
):
    """
    감정 기록을 생성합니다.
    - 로그인 시: user_id를 JWT에서 주입 (MP-04 연동 후)
    - 비로그인 시: request.anon_id 사용
    """
    try:
        record = mood_record_service.create(
            mood_emoji=request.mood_emoji,
            intensity=request.intensity,
            mood_text=request.mood_text,
            user_id=user_id,
            anon_id=request.anon_id if not user_id else None,
        )
        return {
            "id": record.id,
            "mood_emoji": record.mood_emoji,
            "intensity": record.intensity,
            "mood_text": record.mood_text,
            "record_date": record.record_date.isoformat(),
            "recorded_at": record.recorded_at.isoformat() if record.recorded_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@mood_record_router.get("/list")
def list_mood_records(
    mood_record_service: MoodRecordServiceImpl = Depends(inject_mood_record_service),
    user_id: str | None = Query(None, description="사용자 ID (MP-04 후 JWT에서 자동 주입)"),
    limit: int | None = Query(None, ge=1, le=100, description="최대 조회 건수"),
):
    """
    해당 사용자의 감정 기록 목록을 조회합니다.
    - MP-04 완료 후: user_id는 JWT 검증으로만 사용 (쿼리 파라미터 비사용)
    """
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide user_id (or JWT cookie after MP-04).",
        )
    try:
        records = mood_record_service.find_by_user(user_id=user_id, limit=limit)
        return {
            "items": [
                {
                    "id": r.id,
                    "mood_emoji": r.mood_emoji,
                    "intensity": r.intensity,
                    "mood_text": r.mood_text,
                    "record_date": r.record_date.isoformat(),
                    "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
                }
                for r in records
            ],
            "total": len(records),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
