const fs = require('fs');
const https = require('https');

// GitHub Secrets로 등록한 API 키를 가져옵니다. 
// 로컬 테스트 시 임시로 여기에 키를 넣거나, 터미널 환경변수로 설정해야 합니다.
const API_KEY = process.env.GYEONGJU_API_KEY || "여기에_임시_발급받은_키_입력"; 

async function fetchEvents() {
    if (!API_KEY || API_KEY === "여기에_임시_발급받은_키_입력") {
        console.error("❌ API 키가 없습니다. GYEONGJU_API_KEY를 설정하거나 스크립트에 임시로 넣어주세요.");
        return;
    }

    try {
        console.log("🔍 경주시 행사 데이터 수집 시작...");

        // 1. 공공데이터 API 호출 (경주시 공연/전시/축제 중 축제 API 예시)
        // 실제 API 가이드의 엔드포인트 URL로 맞춰야 합니다.
        const url = `https://api.data.go.kr/openapi/tn_pubr_public_cltur_fstvl_api?serviceKey=${API_KEY}&pageNo=1&numOfRows=50&type=json`;
        
        // Node 18 이상에서는 fetch를 바로 쓸 수 있습니다.
        const response = await fetch(url);
        const data = await response.json();
        
        const rawEvents = data.response.body.items;
        
        // 2. 데이터 가공: 경주시 행사만 필터링하고 필요한 항목만 추출
        const processedEvents = rawEvents
            .filter(event => event.rdnmadr && event.rdnmadr.includes('경주시')) // 경주 주소 필터링
            .map(event => ({
                id: event.fstvlId || Math.random().toString(36).substr(2, 9),
                title: event.fstvlNm,         // 행사 이름
                location: event.opar,         // 개최 장소
                startDate: event.fstvlStartDate, // 시작일
                endDate: event.fstvlEndDate,   // 종료일
                type: '축제', // 카테고리 태그용
                description: event.fstvlCo || '경주에서 열리는 신나는 축제'
            }));

        // 3. JSON 파일로 저장
        fs.writeFileSync('events.json', JSON.stringify(processedEvents, null, 2), 'utf-8');
        console.log(`✅ ${processedEvents.length}개의 행사 데이터를 events.json에 성공적으로 저장했습니다!`);

    } catch (error) {
        console.error("❌ 데이터를 가져오는 중 오류가 발생했습니다:", error);
    }
}

fetchEvents();
