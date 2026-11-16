"""경주시 공공데이터 API 3종을 기존 index.html용 events.json으로 정리한다.

실제 API 응답 예제가 제공되지 않았으므로 일부 필드명은 아직 확인되지 않았다.
응답 구조를 인식하지 못하면 빈 성공 결과로 속이지 않고 오류로 종료한다.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree
from zoneinfo import ZoneInfo


SOURCES = {
    "공연": "https://apis.data.go.kr/5050000/gongYeonService/getGongYeon",
    "축제": "https://apis.data.go.kr/5050000/festivalStatusService/getFestivalStatus",
    "전시회": "https://apis.data.go.kr/5050000/exhibitionStatusService/getExhibitionStatus",
}

# 실제 반환 키는 API별 상세 명세/응답 예시 확인 후 추가될 수 있다.
FIELDS = {
    "title": (
        "title", "name", "eventName", "eventNm", "programName", "programNm",
        "prgrmNm", "gongYeonNm", "gongYeonName", "performanceName",
        "prfnm", "shwNm", "festvlNm", "fstvlNm", "festivalNm",
        "festivalName", "exhibitionNm", "exhibitionName", "exhbtnNm",
        "exhbtNm", "exhbtnNm", "exhibitNm", "exhbtnName",
        "공연명", "축제명", "축제명칭", "전시명", "전시회명", "행사명",
    ),
    "location": (
        "location", "place", "placeNm", "eventPlace", "eventPlc",
        "fcltyNm", "venue", "venueNm", "plcNm", "addr", "address",
        "roadAddr", "roadNmAddr", "rdnmadr", "lnmadr", "site", "장소", "주소",
        "행사장소", "축제장소", "공연장소", "전시장소",
    ),
    "start": (
        "startDate", "startDt", "startYmd", "startDe", "strtDate", "strtDt",
        "strtYmd", "strtDe", "beginDate", "beginDe", "bgngDt", "bgngYmd",
        "festivalStartDate", "festvlStartDate", "eventStartDate", "opnDt",
        "performanceStartDate", "prfpdfrom", "fromDate", "시작일", "시작일자",
        "공연시작일", "전시시작일", "개최시작일",
    ),
    "end": (
        "endDate", "endDt", "endYmd", "endDe", "stopDate", "closeDate",
        "finishDate", "finishDt", "endYmd", "lastDate", "lastDe", "endDe",
        "festivalEndDate", "festvlEndDate", "eventEndDate", "prfpdto",
        "performanceEndDate", "toDate", "종료일", "종료일자", "공연종료일",
        "전시종료일", "개최종료일",
    ),
}


def normal_key(key: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]", "", str(key).lower())


def pick(record: dict, names: tuple[str, ...]) -> str:
    """인식 가능한 이름의 첫 번째 *비어 있지 않은* 필드를 찾는다."""
    normalized = {normal_key(k): v for k, v in record.items()}
    for name in names:
        value = normalized.get(normal_key(name))
        if value is not None and not isinstance(value, (dict, list)):
            value = str(value).strip()
            if value:
                return value
    return ""


def parse_date(value: str) -> date | None:
    # 지원 예: 2026-11-04, 20261104, 2026. 11. 04, 2026년 11월 4일
    match = re.search(r"(20\d{2})\D*(\d{1,2})\D*(\d{1,2})", str(value))
    if not match:
        return None
    try:
        return date(*(int(x) for x in match.groups()))
    except ValueError:
        return None


def get_list(node) -> list[dict] | None:
    """공공데이터포털에서 흔한 JSON 래퍼들의 항목 배열을 찾는다."""
    if isinstance(node, list):
        if not node:
            return []
        if all(isinstance(item, dict) for item in node):
            return node
        for item in node:
            result = get_list(item)
            if result is not None:
                return result
        return None

    if not isinstance(node, dict):
        return None

    # 조회 결과가 한 건이면 item이 배열이 아니라 객체로 올 수 있다.
    title_keys = {normal_key(name) for name in FIELDS["title"]}
    if any(normal_key(key) in title_keys for key in node):
        return [node]

    count = node.get("totalCount", node.get("total_count"))
    if count is not None and str(count) == "0":
        return []

    # 'body': {'items': {'item': [...]}} 같은 구조 우선.
    priority = ("response", "body", "items", "item", "data", "list", "rows", "records", "result")
    for field in priority:
        if field in node:
            if field in ("items", "item", "data", "list", "records", "rows") and node[field] is None:
                return []
            result = get_list(node[field])
            if result is not None:
                return result

    for value in node.values():
        if isinstance(value, (list, dict)):
            result = get_list(value)
            if result is not None:
                return result
    return None


def parse_payload(raw: bytes) -> dict | list:
    """JSON 응답 우선; 응답이 XML인 경우도 읽도록 한다."""
    content = raw.decode("utf-8-sig", errors="replace").strip()
    if content.startswith("{") or content.startswith("["):
        return json.loads(content)
    if content.startswith("<"):
        root = ElementTree.fromstring(content)
        # XML 오류 전문을 로그에 무작정 쓰지 않는다(인증키 포함 가능성).
        code = root.findtext(".//resultCode") or root.findtext(".//returnReasonCode")
        message = root.findtext(".//resultMsg") or root.findtext(".//returnAuthMsg")
        if code and code.upper() not in ("00", "0", "SUCCESS", "NORMAL_SERVICE"):
            raise ValueError(f"API 오류코드 {code}: {(message or '')[:120]}")
        items = []
        for item in root.findall(".//item"):
            items.append({element.tag: element.text for element in item})
        return {"items": items}
    raise ValueError("JSON 또는 XML 형식이 아닌 API 응답")


def ensure_success(payload) -> None:
    if not isinstance(payload, dict):
        return
    header = payload.get("response", {}).get("header", {}) if isinstance(payload.get("response"), dict) else {}
    if not header and isinstance(payload.get("header"), dict):
        header = payload["header"]
    if isinstance(header, dict):
        code = header.get("resultCode") or header.get("result_code")
        if code is not None and str(code).upper() not in ("00", "0", "SUCCESS", "NORMAL_SERVICE"):
            raise ValueError(f"API 응답 오류코드 {code}")


def fetch_source(kind: str, endpoint: str, key: str) -> list[dict]:
    # 인증키가 'Encoding' 형태로 저장되었어도 이중 URL 인코딩하지 않도록 한 번 해제.
    params = urlencode({"serviceKey": unquote(key), "pageNo": "1", "numOfRows": "1000"})
    request = Request(f"{endpoint}?{params}", headers={"Accept": "application/json", "User-Agent": "TodayGyeongju-EventUpdater/1.0"})
    try:
        with urlopen(request, timeout=35) as response:
            raw = response.read(8_000_000)
    except HTTPError as exc:
        # URL이나 예외 객체를 출력하면 인증키가 로그에 남을 수 있으니 상태 코드만 출력.
        raise RuntimeError(f"{kind}: HTTP {exc.code}") from None
    except URLError as exc:
        raise RuntimeError(f"{kind}: 네트워크 연결 실패 ({type(exc.reason).__name__})") from None

    data = parse_payload(raw)
    ensure_success(data)
    items = get_list(data)
    if items is None:
        raise RuntimeError(f"{kind}: 응답에서 목록(items)을 찾지 못함. API 응답 구조 확인 필요")
    return items


def normalize_items(kind: str, items: list[dict], today: date) -> list[dict]:
    normalized = []
    keys_seen = set()
    for item in items:
        keys_seen.update(item.keys())
        title = pick(item, FIELDS["title"])
        start = parse_date(pick(item, FIELDS["start"]))
        end = parse_date(pick(item, FIELDS["end"])) or start
        if not title or not start or not end:
            continue
        if end < today or start > today + timedelta(days=365):
            continue
        normalized.append({
            "type": kind,
            "title": title,
            "location": pick(item, FIELDS["location"]),
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
        })

    print(f"[{kind}] 원본 {len(items)}건 → 날짜와 이름을 인식하고 현재/향후 1년 내인 데이터 {len(normalized)}건")
    if items and not normalized:
        # 과거 이벤트만 있는 API도 있으므로 모든 원본 항목에 제목/날짜가 있는지 확인.
        has_parsable = any(
            pick(row, FIELDS["title"]) and parse_date(pick(row, FIELDS["start"]))
            for row in items
        )
        if not has_parsable:
            # 응답 데이터 샘플 자체는 출력하지 않는다(개인 연락처 등 포함 가능).
            print(f"[{kind}] 인식되지 않은 응답 필드명: {', '.join(sorted(keys_seen))[:550]}")
            raise RuntimeError(f"{kind}: 원본 데이터는 있지만 제목/날짜 필드명이 맞지 않음. API 상세 응답 예시 확인 필요")
    return normalized


def main() -> int:
    key = os.environ.get("DATA_GO_KR_SERVICE_KEY", "").strip()
    if not key:
        print("오류: GitHub Secrets에 DATA_GO_KR_SERVICE_KEY를 등록해 주세요.", file=sys.stderr)
        return 1

    today = datetime.now(ZoneInfo("Asia/Seoul")).date()
    events = []
    try:
        for kind, url in SOURCES.items():
            events.extend(normalize_items(kind, fetch_source(kind, url, key), today))
    except (ValueError, RuntimeError, json.JSONDecodeError, ElementTree.ParseError) as exc:
        print(f"행사 데이터 갱신 실패: {exc}", file=sys.stderr)
        return 1

    unique = {(x["type"], x["title"], x["startDate"], x["location"]): x for x in events}
    events = list(unique.values())
    # 오늘 진행 중인 행사 우선, 이후 시작 날짜 순서.
    events.sort(key=lambda e: (e["startDate"] > today.isoformat(), e["startDate"], e["title"]))
    output = Path("events.json")
    output.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{output}: {len(events)}건 생성 완료 (기준일 {today.isoformat()}, KST)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
