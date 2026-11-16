const fs = require('fs');

// Vercel 환경 변수에서 각각의 키 불러오기
const FESTIVAL_KEY = "";
const PERFORMANCE_KEY = process.env.GYEONGJU_Performance_API_KEY;
const EXHIBITION_KEY = process.env.GYEONGJU_Exhibition_API_KEY;

async function fetchAllData() {
    try {
        console.log("🔍 경주 축제, 공연, 전시 통합 데이터 수집 시작...");

        // 1. 축제 데이터 요청 URL
        const festivalUrl = `https://apis.data.go.kr/5050000/festivalStatusService/getFestivalStatus?serviceKey=${FESTIVAL_KEY}&pageNo=1&numOfRows=10&resultType=JSON`;
        
        // 2. 공연 데이터 요청 URL (엔드포인트는 실제 포털 명세에 맞춰 확인 필요)
        const performanceUrl = `https://apis.data.go.kr/5050000/gongYeonService/getGongYeonList?serviceKey=${PERFORMANCE_KEY}&pageNo=1&numOfRows=10&resultType=JSON`;

        // 3. 동시 요청 전송
        const [festivalRes, performanceRes] = await Promise.all([
            fetch(festivalUrl),
            fetch(performanceUrl)
        ]);

        const festivalData = await festivalRes.json();
        const performanceData = await performanceRes.json();

        console.log("--------------------------------------------------");
        console.log("🎉 수집된 축제 데이터:", festivalData);
        console.log("🎭 수집된 공연 데이터:", performanceData);
        console.log("--------------------------------------------------");

    } catch (error) {
        console.error("❌ 데이터 통신 중 오류가 발생했습니다:", error);
    }
}

fetchAllData();