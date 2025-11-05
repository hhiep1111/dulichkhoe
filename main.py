import datetime
import os 
import uuid
import sqlite3
import smtplib
from fastapi import BackgroundTasks
from pydantic import EmailStr
from email.mime.text import MIMEText
from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI()

# Mount static & uploads
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

DB_FILE = "comments.db"
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "123456")
security = HTTPBasic()

# ---------------- DATABASE INIT ----------------
os.makedirs("uploads", exist_ok=True)
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
# create table with email column (if not exists)
c.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        comment TEXT NOT NULL,
        img TEXT,
        token TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
# If the table existed before without email, add email column (safe)
c.execute("PRAGMA table_info(comments)")
cols = [row[1] for row in c.fetchall()]
if "email" not in cols:
    try:
        c.execute("ALTER TABLE comments ADD COLUMN email TEXT")
    except Exception:
        pass
        
conn.commit()
conn.close()
# ---------------- HELPER ----------------
#def is_admin_user(credentials: HTTPBasicCredentials = Depends(security)):
#    return credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS

def dict_from_row(row):
    """Chuyển tuple DB thành dict cho template dễ đọc"""
    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "comment": row[3],   # dùng trong index.html
        "text": row[3],      # dùng trong admin.html
        "img": row[4],
        "token": row[5],
        "status": row[6],
    }
# def send_email(to_email: str, link: str):
#    try:
#       server = smtplib.SMTP("smtp.gmail.com", 587)
#        server.starttls()
#        server.login(EMAIL_USER, EMAIL_PASS)
#        msg = f"Subject: Xác nhận email\n\nClick link để xác nhận: {link}"
#        server.sendmail(EMAIL_USER, to_email, msg)
#       server.quit()
#    except Exception as e:
#       print("Error sending email:", e)


# ---------------- DATA ----------------
content = {
    "vi": {
        "title": "Du lịch Khỏe - Đồng bằng Sông Cửu Long",
        "intro": "Khám phá miền Tây Nam Bộ: sông nước, ẩm thực và văn hóa độc đáo.",
        "menu": {"home": "Trang chủ", "about": "Giới thiệu", "tips": "Lưu ý", "checklist": "Check-list", "lang": "Ngôn ngữ", "food": "Ẩm Thực", "health": "Hỗ trợ Y Tế"},
        "about": "Xin chào, chúng ta là những người yêu thích du lịch và văn hóa miền Tây.",
        "places": [
            {"name": "Cần Thơ", "img": "cantho.jpg",
             "desc": "Thủ phủ miền Tây, nổi tiếng với chợ nổi sông nước, miệt vườn trù phú và nét văn hóa miệt vườn thân tình. Trải nghiệm chợ nổi buổi sáng, thưởng thức bún riêu và trái cây trên ghe."},
            {"name": "An Giang", "img": "angiang.jpg",
             "desc": "Điểm đến tâm linh nổi tiếng, kết hợp với cảnh núi non hùng vĩ."},
            {"name": "Cà Mau", "img": "camau.jpg",
            "desc": "Cà Mau là tỉnh cực Nam của Việt Nam, có ba mặt giáp biển, nổi bật với hệ sinh thái rừng ngập mặn, đầm phá, đảo nhỏ và điểm cực Nam thiêng liêng của Tổ quốc. Thiên nhiên hoang sơ, văn hóa sông nước và ẩm thực phong phú là những điểm hấp dẫn của du lịch Cà Mau"},
            {"name": "Vĩnh Long", "img": "vinhlong.jpg",
            "desc": "texttttttttttttttttttttttttttt"},
            {"name": "Đồng Tháp", "img": "dongthap.jpg",
            "desc": "Đồng Tháp nổi bật với sen, làng hoa Sa Đéc, di tích Óc Eo Gò Tháp, cùng mô hình du lịch cộng đồng xanh, bền vững."}  
        ],
        "tips": [
            {
                "title": "1. Trước khi đi",
                "img": "/static/images/1.jpg",
                "content": [
                    "Tìm hiểu thông tin điểm đến: thời tiết, phong tục, tình hình an ninh, phương tiện di chuyển.",
                    "Chuẩn bị giấy tờ: CMND/CCCD, hộ chiếu, vé máy bay/tàu xe, bảo hiểm du lịch (nếu có).",
                    "Sao lưu giấy tờ: chụp ảnh hoặc lưu bản scan để phòng khi thất lạc.",
                    "Kiểm tra sức khỏe: mang theo thuốc cá nhân, giấy tờ y tế cần thiết."
                    ]
            },
            {
                "title": "2. Khi di chuyển",
                "img": "/static/images/2.jpg",
                "content": [
                    "Không để hành lý xa tầm mắt, đặc biệt ở sân bay, bến xe, ga tàu.",
                    "Giữ đồ có giá trị bên người (tiền, điện thoại, hộ chiếu).",
                    "Chọn phương tiện uy tín: taxi, xe công nghệ, hoặc phương tiện công cộng chính thống."
                ]
            },
            {
                "title": "3. Khi lưu trú",
                "img": "/static/images/3.jpg",
                "content": [
                     "Chọn khách sạn/nhà nghỉ an toàn: có đánh giá tốt, hệ thống an ninh.",
                    "Khóa cửa cẩn thận khi ra ngoài và cả khi ở trong phòng.",
                    "Không tiết lộ số phòng với người lạ."
                ]
            },
            {
                "title": "4. Khi tham quan",
                "img": "/static/images/4.jpg",
                "content": [
                    "Không mang theo quá nhiều tiền mặt hoặc đồ quý giá.",
                    "Cẩn thận với túi xách, balo ở nơi đông người (chợ, lễ hội, bến xe).",
                    "Tuân thủ quy định địa phương: không xả rác, không leo trèo nguy hiểm, tôn trọng văn hóa bản địa.",
                    "Luôn đi theo nhóm nếu ở nơi vắng vẻ hoặc không quen thuộc."
                ]
            },
            {
                "title": "5. An toàn công nghệ",
                "img": "/static/images/5.jpg",
                "content": [
                    "Không dùng Wi-Fi công cộng để giao dịch tài chính.",
                    "Cẩn thận khi chia sẻ vị trí trên mạng xã hội để tránh kẻ xấu lợi dụng."
                ]
            }    
        ],
        "checklist": [
            {"title": "Quần áo", "items": ["Đồ lót", "Tất", "Vớ/bít tất", "Áo blouse", "Áo (tops)", "Quần, jeans, legging",
                                          "Chân váy", "Váy đầm", "Đồ ngủ", "Mũ ngủ", "Khăn tắm", "Áo cardigan", "Áo khoác",
                                          "Đồ bơi: áo tắm, kính bơi, mũ, dép tông",
                                          "Đồ tập: áo ngực thể thao, quần short, áo tập, giày tập"]},
            {"title": "Phụ kiện", "items": ["Giày đi bộ", "Giày cao gót hoặc đế xuồng", "Sneakers", "Thắt lưng",
                                           "Trang sức không đắt giá", "Phụ kiện tóc", "Mũ hoặc nón", "Kính đọc sách",
                                           "Kính mát", "Túi xách, ba lô, ví cầm tay", "Ô/dù"]},
            {"title": "Mùa đông", "items": ["Áo len", "Mũ len", "Khăn quàng", "Găng tay", "Áo khoác ấm",
                                          "Tất giữ nhiệt", "Đồ lót giữ nhiệt", "Boots/Ủng"]},
            {"title": "Mùa hè", "items": ["Quần short", "Áo nhẹ, áo thun", "Đồ bơi, bikini, áo bơi", "Khăn tắm biển",
                                          "Dép tông", "Sandals", "Kính mát", "Sarong", "Mũ hoặc nón",
                                          "Áo khoác nhẹ chống nắng", "Áo khoác nhẹ hoặc cardigan", "Khăn choàng",
                                          "Đồ bơm hơi bãi biển", "Đồ chơi & trò chơi bãi biển"]},
        ],
        "food_list": [
        {    "id": "banhcong",
             "title": "Bánh Cống Cần Thơ",
             "img": "/static/images/cantho.jpg",
             "short": "Giòn rụm, nhân tôm thịt thơm béo.",
             "desc": """
                 <p>Bánh cống là món ăn dân dã nổi tiếng của Cần Thơ.</p>
                 <img src="/static/images/chuadoi.jpg" class="detail-img"/>
                 <p>📍 Địa chỉ gợi ý: Quán Bánh cống Đại Tâm</p>
             """
         },
        {    "id": "hutieu",
             "title": "Hủ Tiếu Sa Đéc",
             "img": "/static/images/dongthap.jpg",
             "short": "Nước ngọt thanh, sợi dai, đậm vị miền Tây.",
             "desc": """
                 <p>Một trong những món hủ tiếu đặc sắc nhất miền Tây.</p>
                 <img src="/static/images/chuaang.jpg" class="detail-img"/>
                 <p>📍 Gợi ý: Khu ẩm thực chợ Xuân Khánh</p>
             """
         }
    ]
    },
    "en": {
        "title": "Healthy Travel - Mekong Delta",
        "intro": "Explore Southern Vietnam: rivers, cuisine, and unique culture.",
        "menu": {"home": "Home", "about": "About", "tips": "Tips", "checklist": "Check-list", "lang": "Language", "food": "Cuisine", "health": "Medical Support"},
        "about": "Hello, we are passionate about traveling and the culture of Southern Vietnam.",
        "places": [
            {"name": "Can Tho", "img": "cantho.jpg",
             "desc": "The capital of the Western region, famous for its floating markets, rich orchards and friendly orchard culture. Experience the morning floating market, enjoy vermicelli soup and fruit on a boat."},
            {"name": "An Giang", "img": "angiang.jpg",
             "desc": "A famous spiritual destination, combined with majestic mountain scenery."},
            {"name": "Ca Mau", "img": "camau.jpg",
             "desc": "Ca Mau is the southernmost province of Vietnam, bordering the sea on three sides, famous for its mangrove ecosystem, lagoons, small islands and the sacred southernmost point of the country. Unspoiled nature, river culture and rich cuisine are the attractions of Ca Mau tourism"},
            {"name": "Vinh Long", "img": "vinhlong.jpg",
             "desc": "texttttttttttttttttttttttttttttt"},
            {"name": "Dong Thap", "img": "dongthap.jpg",
             "desc": "Dong Thap is famous for lotus, Sa Dec flower village, Oc Eo Go Thap relic, and green, sustainable community tourism model."}
        ],
        "tips": [
            {
                "title": "1. Before going",
                "img": "/static/images/1.jpg",
                "content": [
                    "Find out information about the destination: weather, customs, security situation, means of transportation.",
                    "Prepare documents: ID card/CCCD, passport, plane/train ticket, travel insurance (if any).",
                    "Back up documents: take photos or save scans in case of loss.",
                    "Check your health: bring personal medicine, necessary medical documents."
                    ]
            },
            {
                "title": "2. When traveling",
                "img": "/static/images/2.jpg",
                "content": [
                    "Do not leave luggage out of sight, especially at airports, bus stations, train stations.",
                    "Keep valuables with you (money, phone, passport).",
                    "Choose reputable means of transport: taxi, technology car, or official public transport."
                ]
            },
            {
                "title": "3. When staying",
                "img": "/static/images/3.jpg",
                "content": [    
                    "Choose a safe hotel/guesthouse: with good reviews, security system.",
                    "Lock the door carefully when going out and when in the room.",
                    "Do not reveal the room number to strangers."
                ]
            },
            {
                "title": "4. When visiting",
                "img": "/static/images/4.jpg",
                "content": [
                    "Do not carry too much cash or valuables.",
                    "Be careful with bags and backpacks in crowded places (markets, festivals, bus stations).",
                    "Comply with local regulations: do not litter, do not climb dangerously, respect local culture.",
                    "Always go in groups if in deserted or unfamiliar places."
                ]
            },
            {
                "title": "5. Technology safety",
                "img": "/static/images/5.jpg",
                "content": [
                    "Do not use public Wi-Fi for financial transactions.",
                    "Be careful when sharing your location on social networks to avoid bad guys taking advantage."
                ]
            }
                ],
        "checklist": [
            {"title": "Clothes", "items": ["Underwear", "Socks", "Tights", "Blouse", "Tops", "Pants, jeans, leggings",
                                          "Skirts", "Dresses", "Sleepwear", "Nightcap", "Towel", "Cardigan", "Jacket",
                                          "Swimwear: swimsuit, goggles, cap, flip-flops",
                                          "Sportswear: sports bra, shorts, workout top, sneakers"]},
            {"title": "Accessories", "items": ["Walking shoes", "Heels or platform shoes", "Sneakers", "Belt",
                                           "Non-expensive jewelry", "Hair accessories", "Hat or cap", "Reading glasses",
                                           "Sunglasses", "Bag, backpack, clutch", "Umbrella"]},
            {"title": "Winter", "items": ["Sweater", "Wool hat", "Scarf", "Gloves", "Warm jacket",
                                          "Thermal socks", "Thermal underwear", "Boots"]},
            {"title": "Summer", "items": ["Shorts", "Light shirt, T-shirt", "Swimwear, bikini", "Beach towel",
                                          "Flip-flops", "Sandals", "Sunglasses", "Sarong", "Hat or cap",
                                          "Light jacket for sun protection", "Light cardigan or jacket", "Scarf",
                                          "Inflatable beach toys", "Beach toys & games"]},
        ]
    },

    "kr": {
        "title": "건강한 여행 - 메콩 델타",
        "intro": "남부 베트남 탐험: 강, 음식, 독특한 문화.",
        "menu": {"home": "홈", "about": "소개", "tips": "유의사항", "checklist": "체크리스트", "lang": "언어", "food": "음식", "health": "의료 지원"},
        "about": "안녕하세요, 우리는 남부 베트남의 여행과 문화를 사랑하는 사람들입니다.",
        "places": [
            {"name": "깐토", "img": "cantho.jpg",
             "desc": "서부 지역의 수도로, 수상 시장, 풍성한 과수원, 그리고 정겨운 과수원 문화로 유명합니다. 아침 수상 시장을 경험하고, 배 위에서 당면 수프와 과일을 즐겨보세요."},
            {"name": "안장", "img": "angiang.jpg",
             "desc": "웅장한 산의 경치와 어우러진 유명한 영적 여행지입니다."},
            {"name": "까마우", "img": "camau.jpg",
             "desc": "까마우는 베트남 최남단 성으로, 삼면이 바다에 접해 있으며, 맹그로브 생태계, 석호, 작은 섬들, 그리고 베트남 최남단의 성지로 유명합니다. 훼손되지 않은 자연, 강 문화, 그리고 풍부한 음식은 까마우 관광의 매력입니다."},
            {"name": "빈롱", "img": "vinhlong.jpg",
             "desc": "texttttttttttttttttttttttttttttttt"},
            {"name": "동탑", "img": "dongthap.jpg",
             "desc": "동탑은 연꽃, 사덱 꽃 마을, 옥 에오 고탑 유적, 그리고 친환경적이고 지속 가능한 지역 사회 관광 모델로 유명합니다."}
        ],
        "tips": [
            {
                "title": "1. 출발 전",
                "img": "/static/images/1.jpg",
                "content": [
                    "목적지 정보 확인: 날씨, 세관, 보안 상황, 교통수단",
                    "서류 준비: 신분증/CCCD, 여권, 비행기/기차표, 여행자 보험(있는 경우)",
                    "서류 백업: 분실에 대비하여 사진을 찍거나 스캔본을 저장하세요.",
                    "건강 상태 확인: 개인 의약품, 필요한 의료 서류를 지참하세요."
                ]
            },
            {
                "title": "2. 여행 시",
                "img": "/static/images/2.jpg",
                "content": [
                    "특히 공항, 버스 정류장, 기차역에서 짐을 눈에 띄지 않는 곳에 두지 마세요.",
                    "귀중품(돈, 휴대폰, 여권)은 항상 지참하세요.",
                    "택시, 이동 차량 또는 공식 대중교통 등 신뢰할 수 있는 교통수단을 이용하세요."
                ]
            },
            {
                "title": "3. 숙박 시",
                "img": "/static/images/3.jpg",
                "content": [
                    "안전한 호텔/게스트하우스를 선택하세요: 좋은 후기와 보안 시스템을 갖추고 있어야 합니다.",
                    "외출 시와 객실 내에서는 문을 단단히 잠그세요.",
                    "낯선 사람에게 객실 번호를 알려주지 마세요."
                ]
            },
            {
                "title": "4. 방문 시",
                "img": "/static/images/4.jpg",
                "content": [
                    "현금이나 귀중품을 너무 많이 가지고 다니지 마세요.",
                    "시장, 축제, 버스 정류장 등 사람이 붐비는 장소에서는 가방과 배낭을 조심하세요.",
                    "지역 규정을 준수하세요: 쓰레기를 버리지 마세요, 위험한 등반을 하지 마세요, 지역 문화를 존중하세요.",
                    "사람이 없는 곳이나 낯선 곳에서는 항상 그룹으로 이동하세요."
                ]
            },
            {
                "title": "5. 기술 안전",
                "img": "/static/images/5.jpg",
                "content": [
                    "공용 Wi-Fi를 사용하여 금융 거래를 하지 마세요.",
                    "소셜 네트워크에 위치를 공유할 때는 악의적인 사용자가 악용하지 않도록 주의하세요."
                ]
            }    
            ],
        "checklist": [
            {"title": "의류", "items": ["속옷", "양말", "타이츠", "블라우스", "상의", "바지, 청바지, 레깅스",
                                          "치마", "드레스", "잠옷", "수면 모자", "수건", "가디건", "재킷",
                                          "수영복: 수영복, 고글, 모자, 슬리퍼",
                                          "운동복: 스포츠 브라, 반바지, 운동 상의, 운동화"]},
            {"title": "액세서리", "items": ["워킹 슈즈", "하이힐 또는 플랫폼 슈즈", "스니커즈", "벨트",
                                           "비싼 장신구 아님", "헤어 액세서리", "모자 또는 캡", "안경",
                                           "선글라스", "가방, 백팩, 클러치", "우산"]},
            {"title": "겨울", "items": ["스웨터", "울 모자", "스카프", "장갑", "따뜻한 재킷",
                                          "보온 양말", "보온 속옷", "부츠"]},
            {"title": "여름", "items": ["반바지", "가벼운 셔츠, 티셔츠", "수영복, 비키니", "비치 타월",
                                          "슬리퍼", "샌들", "선글라스", "사롱", "모자 또는 캡",
                                          "햇빛 차단용 가벼운 재킷", "가벼운 가디건 또는 재킷", "스카프",
                                          "비치용 에어토이", "비치용 장난감 및 게임"]},
        ]
    }
}
place_details_data = {
    "vi": {
        "Cần Thơ": [
        {   "title": "Bến Ninh Kiều – Biểu Tượng Thành Phố", 
            "desc": """
            <p>Biểu tượng của Cần Thơ bên dòng sông Hậu hiền hòa, là nơi tản bộ, ngắm cảnh và chụp ảnh tuyệt đẹp.</p>
            <img src="/static/images/benninhkieu.jpg" class="detail-img" alt="Toàn cảnh bến Ninh Kiều">
            <p>📍 Vị trí: Trung tâm TP. Cần Thơ, bên bờ sông Hậu.</p>
            <p>Điểm nổi bật:</p>
            <ul>
                <li>Cầu đi bộ Ninh Kiều rực rỡ ánh đèn ban đêm.</li>
                <li>Bến tàu đi chợ nổi, du thuyền trên sông Hậu.</li>
                <li>Tượng Bác Hồ và công viên thoáng mát.</li>
            </ul>
            <img src="/static/images/bac_ho.jpg" class="detail-img" alt="Tượng Bác Hồ tại công viên Cần Thơ">
            <p>Gợi ý:</p>
            <ul>
                <li>Giờ tham quan: Cả ngày (đẹp nhất vào buổi tối).</li>
                <li>Kết hợp ăn tối trên du thuyền để ngắm sông về đêm.</li>
                <li>Buổi tối cuối tuần có múa nhạc đường phố.</li>
            </ul>
            """},
        {   "title": "Chợ nổi Cái Răng – Biểu tượng miền Tây", 
            "desc": """ 
            <p>Một trong những chợ nổi lớn nhất miền Tây, sôi động từ tờ mờ sáng, chuyên bán trái cây và đặc sản miền sông nước.</p>
            <p>Điểm nổi bật:</p>
            <ul>
                <li>Ghe thuyền treo “bẹo” (mẫu hàng treo trên sào) để rao bán.</li>
                <li>Trái cây, nông sản tươi, món ăn sáng như hủ tiếu, cà phê bán ngay trên thuyền.</li>
                <img src="/static/images/chocairang.jpg" class="detail-img" alt="Chợ Nổi Cái Răng Cần Thơ">

            </ul>
            <p>Gợi ý:</p>
            <ul>
                <li>Giờ tham quan: 5h00 – 9h00 sáng.</li>
                <li>Nên đi tour ghe nhỏ để len lỏi vào chợ.</li>
                <li>Trải nghiệm ăn hủ tiếu trên ghe là “must-try”.</li>
            </ul>
            """},
            {   "title": "Chùa Dơi – Ngôi chùa Khmer độc đáo (Sóc Trăng cũ)", 
                "desc": """ 
                <p>Ngôi chùa Khmer cổ kính hơn 400 năm, nổi tiếng với hàng ngàn con dơi treo mình trên những tán cây trong khuôn viên.</p>
                <p>📍Vị trí: Phường 3, TP. Sóc Trăng, cách trung tâm khoảng 2 km.</p>
                <p>Lịch sử & kiến trúc:</p>
                <ul>
                    <li>Xây dựng từ thế kỷ 16, là ngôi chùa Khmer Nam Tông tiêu biểu.</li>
                    <li>Chánh điện mang kiến trúc Khmer đặc trưng, mái cong nhiều tầng, hoa văn tinh xảo.</li>
                    <li>Trong chùa còn lưu giữ nhiều tượng Phật cổ quý giá.</li>
                    <img src="/static/images/chuadoi.jpg" class="detail-img" alt="Chùa Dơi tại Sóc Trăng">
                </ul>
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Hàng ngàn con dơi quạ (loài lớn, sải cánh đến 1m) sống trong khuôn viên.</li>
                    <li>Dơi chỉ treo mình ban ngày, chiều tối bay đi kiếm ăn → tạo nên cảnh tượng độc đáo hiếm thấy.</li>
                </ul>
                <p>Gợi ý:</p>
                <ul>
                    <li>Giờ mở cửa: Tự do tham quan cả ngày, tốt nhất buổi sáng hoặc chiều mát.</li>
                    <li>Nên ăn mặc lịch sự khi vào chùa.</li>
                    <li>Giữ yên tĩnh, không làm phiền đàn dơi.</li>
                </ul>
                """},
            {   "title": "Khu bảo tồn thiên nhiên Lung Ngọc Hoàng (Hậu Giang cũ)", 
                "desc": """ 
                <p>Lung Ngọc Hoàng được xem là “lá phổi xanh” của miền Tây, sở hữu hệ sinh thái rừng ngập nước phong phú với kênh rạch dày đặc, thảm thực vật rậm tạp, không gian hoang sơ, mát lành, rất thích hợp cho du lịch sinh thái, đi xuồng khám phá rừng, ngắm chim và chụp ảnh cảnh rừng – sông tự nhiên.</p>
                <p>📍Vị trí: Thuộc huyện Phụng Hiệp, tỉnh Hậu Giang.</p>
                <img src="/static/images/lungngochoang.jpg" class="detail-img" alt="Khu bảo tồn thiên nhiên Lung Ngọc Hoàng">
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Diện tích lớn (hơn 2.800 ha) rừng tràm ngập nước. Không gian thiên nhiên hoang sơ, kênh rạch len lỏi, rất hợp đi tham quan sinh thái, ngắm chim, tản bộ giữa rừng tràm.</li>
                    <li>Giá trị thiên nhiên rất lớn — bảo tồn đa dạng sinh học quý hiếm.</li>
                </ul>
                <p>Gợi ý:</p>
                <ul>
                    <li>Thời điểm tốt: sáng sớm hoặc gần chiều để tránh nắng gắt và tận hưởng không gian yên tĩnh.</li>
                    <li>Mang theo đồ chống côn trùng, giày dép chống trượt vì có thể đường hơi ướt hoặc bùn.</li>
                    <li>Vì là khu bảo tồn thiên nhiên, nên giữ gìn vệ sinh, không xâm phạm khu vực động vật hoang dã.</li>
                </ul>
                """}
         ],
        "Cà Mau": [
            {   "title": "Mũi Cà Mau – Cột mốc cực Nam", 
                "desc": """ 
                <p>Mũi Cà Mau là điểm cực Nam của Tổ quốc, nơi dải đất Việt Nam vươn ra biển lớn. Đến đây, bạn có thể check-in tại cột mốc GPS 0001, biểu tượng con thuyền và ngắm khung cảnh rừng ngập mặn – biển trời mênh mông.</p>
                <p>📍Vị trí: Mũi Cà Mau nằm ở xã Đất Mũi, huyện Ngọc Hiển, tỉnh Cà Mau, thuộc cực Nam đất liền của Việt Nam.</p>
                <img src="/static/images/muicamau.jpg" class="detail-img" alt="Mũi Cà Mau cột mốc cực Nam">

                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Đây là một trong những nơi hiếm hoi có thể ngắm bình minh biển Đông và hoàng hôn biển Tây ngay tại cùng vị trí, mang lại cảm giác thiêng liêng và tự hào khi chạm “tận cùng đất Việt”.</li>
                    <li>Công trình biểu tượng như cột mốc đường Hồ Chí Minh Km 2436 tại mũi Cà Mau, biểu tượng chủ quyền và vị trí cực Nam.</li>
                    <li>Hệ sinh thái rừng ngập mặn: cây mắm, cây đước phát triển trên đất bồi phù sa, rễ mắm đâm ngược lên giữ đất.</li>
                </ul>
                <p>Gợi ý:</p>
                <ul>
                    <li>Thích hợp đi sớm buổi sáng hoặc chiều muộn để ngắm biển và ánh sáng đẹp.</li>
                    <li>Đi đường bộ tới Đất Mũi có thể hơi xa – chuẩn bị chu đáo phương tiện, nhiên liệu, đồ ăn nhẹ.</li>
                    <li>Tôn trọng môi trường: không xả rác, giữ gìn cảnh quan thiên nhiên.</li>
                </ul>
                """},
            {   "title": "Rừng ngập mặn U Minh Hạ", 
                "desc": """ 
                <p>Rừng U Minh Hạ là hệ sinh thái rừng tràm – ngập mặn đặc trưng miền Tây, được ví như “lá phổi xanh” của Cà Mau. Không gian hoang sơ với kênh rạch chằng chịt, thảm thực vật dày đặc và nhiều loài chim thú quý hiếm.</p>
                <p>📍Vị trí: Vườn Quốc gia U Minh Hạ nằm ở tỉnh Cà Mau, thuộc vùng rừng ngập mặn – rừng tràm.</p>
                <img src="/static/images/rungngapman.jpg" class="detail-img" alt="Rừng ngập mặn U Minh Hạ">

                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Rừng tràm ngập nước, hệ sinh thái phong phú với nhiều loài động – thực vật và kênh rạch đan xen.</li>
                    <li>Có đài quan sát cao để ngắm toàn cảnh rừng U Minh Hạ.</li>
                    <li>Các hoạt động tham quan như đi thuyền xuồng len lỏi qua kênh rạch, nghe “khung rừng” – rất khác biệt so với du lịch bãi biển thông thường.</li>
                </ul>
                <p>Gợi ý:</p>
                <ul>
                    <li>Khu rừng có thể tham quan quanh năm nhưng thời điểm tốt là mùa khô (ít mưa) hoặc mùa nước lên khi muốn đi thuyền sâu hơn.</li>
                    <li>Mặc áo dài tay + kem chống côn trùng nếu đi vào khu rừng vì muỗi và côn trùng có thể nhiều.</li>
                    <li>Nếu đi vào mùa nước lên, có thể thuê xuồng tham quan; vào mùa khô, đường bộ sẽ thuận lợi hơn.</li>
                </ul>
                """},
            {"title": "Quan Âm Phật Đài (Mẹ Nam Hải)", 
                "desc": """ 
                <p>Quan Âm Phật Đài (còn gọi là “Mẹ Nam Hải”) là một quần thể tâm linh lớn nằm ở ven biển tỉnh Bạc Liêu – miền Tây Nam Bộ. Đây không chỉ là nơi thờ tự của tín đồ Phật giáo mà còn là điểm đến du lịch tâm linh nổi bật với biểu tượng tượng Quán Thế Âm Bồ Tát hướng ra biển, mang ý nghĩa che chở và ban bình an cho người dân biển.</p>
                <p>📍Vị trí: hóm Bờ Tây, phường Nhà Mát, thành phố Bạc Liêu, tỉnh Bạc Liêu. Nằm cách trung tâm thành phố Bạc Liêu khoảng 8 km về phía hướng ra biển.</p>
                <p>Lịch sử & kiến trúc:</p>
                <ul>
                    <li>Khởi lập từ năm 1973 với ý tưởng của Hòa thượng Thích Trí Đức.</li>
                    <li>Kiến trúc mang phong cách Phật giáo Bắc Tông, với các chi tiết hoa văn, cổng tam quan, đại điện cao lớn, tạo cảm giác trang nghiêm.</li>
                </ul>
                <img src="/static/images/menamhai.jpg" class="detail-img" alt="Quan Âm Phật Đài">
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Tượng Quán Thế Âm Bồ Tát cao khoảng 11 m đặt trên bệ sen lớn, hướng tầm nhìn ra biển, là điểm nhấn của khu tâm linh này.</li>
                    <li>Mang ý nghĩa mạnh mẽ về tín ngưỡng: tượng Phật hướng ra biển như che chở cho ngư dân, người dân vùng biển khỏi sóng gió.</li>
                    <li>Không gian thiên nhiên kết hợp với kiến trúc tâm linh – khuôn viên rộng thoáng, gần biển, nhiều cây xanh và đường hãng thuận để tham quan, chụp ảnh.</li>
                </ul>
                <p>Gợi ý:</p>
                <ul>
                    <li>Trang phục lịch sự vì đây là nơi linh thiêng, dành thời gian để chiêm bái và tĩnh tâm.</li>
                    <li>Mang theo mũ, kem chống nắng vì khu vực gần biển có ánh nắng mạnh và gió biển.</li>
                    <li>Có bãi giữ xe miễn phí và dịch vụ cơm nước chay dành cho khách chiêm bái tại một số thời điểm.</li>
                </ul>
                """}
        ],
        "Vĩnh Long": [
            {   "title": "Chùa Âng: Angkorajaborey (Trà Vinh cũ)", 
                "desc": """ 
                <p>Chùa Âng là một trong những ngôi chùa Khmer cổ kính và nổi tiếng nhất Trà Vinh, nằm cạnh Ao Bà Om. Ngôi chùa mang đậm kiến trúc Khmer Nam Bộ với các mái cong nhiều lớp, cột trụ chạm khắc tinh xảo và tông vàng nổi bật.</p>
                <p>📍Vị trí: Thuộc khóm 4, phường 8, thành phố Trà Vinh, tỉnh Trà Vinh.</p>
                <p>Lịch sử & kiến trúc:</p>
                <ul>
                    <li>Chùa Âng (còn gọi là Wat Angkor Raig Borei) rộng khoảng 3,5 ha.</li>
                    <li>Kiến trúc là sự kết hợp giữa truyền thống Khmer cổ và một số yếu tố kiến trúc hiện đại – giữ nét nghệ thuật điêu khắc đầu chim, thần rắn Naga, mái cong đặc trưng.</li>
                    <li>Mang giá trị văn hoá, lịch sử của đồng bào Khmer Nam Bộ, là nơi sinh hoạt tôn giáo, lưu giữ truyền thống.</li>
                </ul>
                <img src="/static/images/chuaang.jpg" class="detail-img" alt="Chùa Âng (Angkorajaborey) – Trà Vinh">
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Ngôi chùa cổ của người Khmer Nam Bộ, được xem là ngôi chùa đẹp nhất Trà Vinh.</li>
                    <li>Kiến trúc mang đậm nét Khmer và Angkor: mái chùa, phù điêu, tượng thần rắn Naga, không gian linh thiêng vững chắc.</li>
                    <li>Môi trường xung quanh xanh mát với cây cổ thụ, sân chùa rộng, tạo cảm giác thanh tịnh.</li>
                </ul>
                <p>Gợi ý:</p>
                <ul>
                    <li>Vào chùa nên mặc trang phục lịch sự, đi nhẹ nhàng vì đây là nơi linh thiêng.</li>
                    <li>Mang mũ/nón, kem chống nắng nếu đi buổi trưa; tốt nhất đi sáng hoặc chiều để ánh sáng đẹp và thời tiết dễ chịu.</li>
                    <li>Nếu muốn tìm hiểu sâu về văn hóa Khmer, hỏi hướng dẫn địa phương hoặc xem thông tin trước.</li>
                </ul>
                """}
                ],
        "Đồng Tháp": [
            {   "title": "Đồng Sen Tháp Mười", 
                "desc": """ 
                <p>Đồng Sen Tháp Mười là một trong những cánh đồng sen lớn và đẹp nhất miền Tây, nổi tiếng với không gian mênh mông hoa sen nở rộ, mang đậm nét mộc mạc, thanh bình của vùng Đồng Tháp Mười.</p>
                <p>📍Vị trí: Xã Mỹ Hòa, huyện Tháp Mười, tỉnh Đồng Tháp. Cách TP. Cao Lãnh khoảng 40km</p>
                <p>Lịch sử & kiến trúc:</p>
                <img src="/static/images/dongthap.jpg" class="detail-img" alt="Đồng Sen Tháp Mười">
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Đồng sen bát ngát, đẹp nhất vào mùa sen (tháng 5 đến 10).</li>
                    <li>Các dịch vụ trải nghiệm: đi xuồng chụp ảnh, mặc áo bà ba, hái sen, check-in cầu tre.</li>
                    <li>Ẩm thực từ sen: cơm sen, gỏi ngó sen, chè sen, trà sen.</li>
                </ul>
                <p>Gợi ý:</p>
                <ul>
                    <li>Nên đi sớm 6:30 – 9:00 hoặc chiều mát 15:30 – 17:30</li>
                    <li>Mang theo mũ, kem chống nắng; đi giày thấp/ dép.</li>
                    <li>Tránh đi sau mưa vì đường đất có thể trơn</li>
                </ul>
                """},
        {
            "title": "Làng Hoa Sa Đéc", 
                "desc": """ 
                <p>Làng hoa Sa Đéc là “Thủ phủ hoa miền Tây”, nổi bật với hàng ngàn loài hoa kiểng được trồng trên giàn nổi độc đáo, là điểm du lịch văn hóa – sinh thái, chụp ảnh và mua hoa nổi tiếng quanh năm.</p>
                <p>📍Vị trí: Phường Tân Quy Đông, TP. Sa Đéc, Đồng Tháp. Cách Cao Lãnh khoảng 30km.</p>
                <p>Lịch sử & kiến trúc:</p>
                <ul>
                    <li>Hình thành cuối thế kỷ 19 – đầu thế kỷ 20</li>
                    <li>Là làng hoa truyền thống lâu đời ở miền Tây.</li>
                    <li>Nét kiến trúc: nhà cổ, làng nghề truyền thống, dàn kệ hoa nổi đặc trưng.</li>
                </ul>
                <img src="/static/images/langhoa.jpg" class="detail-img" alt="Làng Hoa Sa Đéc">
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Làng hoa hơn 100 năm tuổi.</li>
                    <li>Hàng ngàn giống hoa & kiểng: cúc, hồng, bonsai, kiểng cổ.</li>
                    <li>Có khu check-in, cầu gỗ, nhà kính, nhà làng nghề làm bánh, mứt.</li>
                </ul>
                <p>Gợi ý:</p>
                <ul>
                    <li>Thời điểm đẹp nhất: tháng 12 – tháng 1 âm lịch.</li>
                    <li>Nên đi buổi sáng sớm hoặc chiều hoàng hôn.</li>
                    <li>Tôn trọng người trồng hoa – không bẻ hoa khi chụp ảnh.</li>
                </ul>
                """}
        ]
    },
    "en": {
        "Can Tho": [
            {"title": "Ninh Kieu Wharf",
            "desc": """
                <p>The symbol of Can Tho on the gentle Hau River, is a beautiful place to walk, sightsee and take photos.</p>
                <img": src="/static/images/test1.jpg" class="detail-img"/>

                <p>📍 Location: Can Tho City Center, on the banks of Hau River.</p>
                <p>Highlights:</p>
                <ul>
                    <li>Ninh Kieu pedestrian bridge is brightly lit at night.</li>
                    <li>Wharf to go to the floating market, cruise on Hau River.</li>
                    <li>Uncle Ho's statue and airy park.</li>
                </ul>
            """
       # "Can Tho": [
            #{"title": "Ninh Kieu Wharf", "desc": "The symbol of Can Tho on the gentle Hau River, a place for walking, sightseeing and taking beautiful photos.", "img": "test1.png"},
            #{"title": "Cai Rang Floating Market", "desc": "One of the largest floating markets in the West, bustling from dawn, specializing in selling fruits and specialties of the river region.", "img": "test2.png"},
            #{"title": "Binh Thuy Ancient House", "desc": "The ancient house combines French and Asian architecture, built in the 19th century, is a famous tourist attraction.", "img": "test3.png"}
            }
             ]
    },
    "kr": {
        "깐토": [
            {"title": "닌끼우 부두", "desc": "잔잔한 하우 강변에 위치한 깐토의 상징으로, 산책과 관광, 아름다운 사진 촬영을 즐기기에 좋은 곳입니다.", "img": "test1.png"},
            #{"title": "까이랑 수상시장", "desc": "서부 최대 규모의 수상시장 중 하나로, 새벽부터 활기가 넘치며 강변 지역의 과일과 특산품을 전문으로 판매합니다.", "img": "test2.png"},
            #{"title": "빈투이 고택", "desc": "19세기에 지어진 이 고택은 프랑스와 아시아 건축 양식이 결합된 곳으로, 유명한 관광 명소입니다.", "img": "test3.png"}
        ]
    }
}
# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, lang: str = "vi"):
    data = content.get(lang, content["vi"])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, comment, img, token, status FROM comments WHERE status='active'")
    rows = c.fetchall()
    conn.close()

    comments = [dict_from_row(r) for r in rows]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data,
            "lang": lang,
            "comments": comments,
            "is_admin": False,  # mặc định khách
            "page": "home",
        },
    )
# About page
@app.get("/about", response_class=HTMLResponse)
async def about(request: Request, lang: str = "vi"):
    data = content.get(lang, content["vi"])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, comment, img, token, status FROM comments WHERE status='active'")
    rows = c.fetchall()
    conn.close()

    comments = [dict_from_row(r) for r in rows]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data,
            "lang": lang,
            "comments": comments,
            "is_admin": False,
            "page": "about",   # 👈 quan trọng
        },
    )
# Route cảnh báo
@app.get("/tips", response_class=HTMLResponse)
async def warn(request: Request, lang: str = "vi"):
    data = content.get(lang, content["vi"])

    # Lấy comment (nếu muốn gắn chung hệ thống comment)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, comment, img, token, status FROM comments WHERE status='active'")
    rows = c.fetchall()
    conn.close()
    comments = [dict_from_row(r) for r in rows]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data,
            "page": "tips",   # flag để template biết đang ở trang warn
            "lang": lang,
            "comments": comments,
            "is_admin": False,
        },
    )
# Route checklist
@app.get("/checklist", response_class=HTMLResponse)
async def checklist(request: Request, lang: str = "vi"):
    data = content.get(lang, content["vi"])

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, comment, img, token, status FROM comments WHERE status='active'")
    rows = c.fetchall()
    conn.close()
    comments = [dict_from_row(r) for r in rows]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data,
            "page": "checklist",
            "lang": lang,
            "comments": comments,
            "is_admin": False,
        })
@app.get("/food", response_class=HTMLResponse)
async def checklist(request: Request, lang: str = "vi"):
    data = content.get(lang, content["vi"])
    food_list = data.get("food", [])

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, comment, img, token, status FROM comments WHERE status='active'")
    rows = c.fetchall()
    conn.close()
    comments = [dict_from_row(r) for r in rows]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data,
            "page": "food",
            "lang": lang,
            "food_list": food_list,
            "comments": comments,
            "is_admin": False,
        })
@app.get("/health", response_class=HTMLResponse)
async def checklist(request: Request, lang: str = "vi"):
    data = content.get(lang, content["vi"])

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, comment, img, token, status FROM comments WHERE status='active'")
    rows = c.fetchall()
    conn.close()
    comments = [dict_from_row(r) for r in rows]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data,
            "page": "health",
            "lang": lang,
            "comments": comments,
            "is_admin": False,
        })
# ---------------- COMMENT ----------------
@app.post("/comment")
async def comment(
    request: Request,
    name: str = Form(...),
    email: EmailStr = Form(...),   # validate email
    comment: str = Form(...),
    lang: str = Form("vi"),
    image: UploadFile = File(None),
):
    filename = None
    if image:
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid.uuid4()}_{image.filename}"
        filepath = os.path.join("uploads", filename)
        with open(filepath, "wb") as buffer:
            buffer.write(await image.read())

    token = str(uuid.uuid4())
    comment_id = str(uuid.uuid4())
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO comments (id, name, email, comment, img, token, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (comment_id, name, email, comment, filename, token, "pending", datetime.datetime.utcnow()),
    )
    conn.commit()
    conn.close()
    
     #Gửi email xác minh
    try:
        send_verification_email(email, token, lang)
    except Exception as e:
        print("⚠️ Không gửi được email:", e)
    
    return RedirectResponse(url=f"/?lang={lang}", status_code=303)

# ---------------- ADMIN ----------------
@app.get("/admin", response_class=HTMLResponse)
async def admin(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    lang: str = "vi",
):
    if not (credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS):
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})

    data = content.get(lang, content["vi"])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, comment, img, token, status FROM comments")
    rows = c.fetchall()
    conn.close()

    comments = [dict_from_row(r) for r in rows]
    return templates.TemplateResponse(
        "admin.html",  # dùng trang admin
        {
            "request": request,
            "data": data,
            "lang": lang,
            "comments": comments,
            "is_admin": True,
            "page": "admin",
        },
    )

# ---------------- DELETE ----------------
@app.post("/delete_comment")
async def delete_comment(
    id: str = Form(...),
    token: str = Form(...),
    credentials: HTTPBasicCredentials = Depends(security),
):
    # Kiểm tra đăng nhập admin
    if not (credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"}
        )

    # Xóa comment đúng id + token
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM comments WHERE id=? AND token=?", (id, token))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/admin", status_code=303)

# ---------------- VERIFY EMAIL ----------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "phhiep6264@gmail.com"
SMTP_PASS = "cmphyfvggxvrhviw"

def send_verification_email(email: str, token: str, lang: str = "vi"):
    subject = {
        "vi": "Xác minh bình luận của bạn",
        "en": "Verify your comment",
        "kr": "댓글 확인"
    }.get(lang, "Verify your comment")

    verify_link = f"https://dulichkhoe.onrender.com/verify_email?token={token}&lang={lang}"

    body = {
        "vi": f"Xin chào,\n\nVui lòng nhấp vào liên kết sau để xác minh bình luận của bạn:\n{verify_link}\n\nCảm ơn!",
        "en": f"Hello,\n\nPlease click the following link to verify your comment:\n{verify_link}\n\nThank you!",
        "kr": f"안녕하세요,\n\n아래 링크를 클릭하여 댓글을 확인해 주세요:\n{verify_link}\n\n감사합니다!"
    }.get(lang, f"Please verify your comment: {verify_link}")

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [email], msg.as_string())
            print(f"✅ Verification email sent to {email}")
    except Exception as e:
        print("❌ Error sending email:", e)
        
# ---------------- ADMIN TRIGGER VERIFY ----------------
@app.post("/admin_verify_email")
async def admin_verify_email(
    id: str = Form(...),
    token: str = Form(...),
    lang: str = "vi",
    credentials: HTTPBasicCredentials = Depends(security),
):
    # Kiểm tra đăng nhập admin
    if not (credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"}
        )

    # Lấy email user theo id + token
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT email FROM comments WHERE id=? AND token=?", (id, token))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Comment not found")

    user_email = row[0]

    # Gửi mail xác thực
    send_verification_email(user_email, token, lang)

    # Quay lại trang admin
    return RedirectResponse(url=f"/admin?lang={lang}", status_code=303)
    
# ---------------- USER CLICK LINK XÁC THỰC ----------------
@app.get("/verify_email")
async def verify_email(token: str, lang: str = "vi"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, status FROM comments WHERE token=?", (token,))
    row = c.fetchone()

    if not row:
        conn.close()
        return HTMLResponse("<h2>❌ Token không hợp lệ.</h2>")

    comment_id, status = row

    if status == "active":
        conn.close()
        return HTMLResponse("<h2>✅ Bình luận đã được xác minh trước đó.</h2>")

    # Update thành active
    c.execute("UPDATE comments SET status='active' WHERE id=?", (comment_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/?lang={lang}", status_code=303)
# ---------------- ADMIN APPROVE COMMENT ----------------
@app.post("/approve_comment")
async def approve_comment(
    id: str = Form(...),
    credentials: HTTPBasicCredentials = Depends(security),
    lang: str = "vi"
):
    # Kiểm tra đăng nhập admin
    if not (credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"}
        )

    # Duyệt trực tiếp comment
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE comments SET status='active' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    # Quay lại trang admin
    return RedirectResponse(url=f"/admin?lang={lang}", status_code=303)
#-------------------trang chi tiet-------------------------
@app.get("/place/{name}", response_class=HTMLResponse)
async def place_detail(request: Request, name: str, lang: str = "vi"):
    # Lấy dữ liệu ngôn ngữ
    data = content.get(lang, content["vi"])

    # Tìm địa điểm theo slug
    place = next((p for p in data["places"] if p["name"].lower() == name.lower()), None)
    if not place:
        raise HTTPException(status_code=404, detail="Địa điểm không tồn tại")
        
    # Lấy chi tiết địa điểm (nếu có)
    details_by_lang = place_details_data.get(lang, place_details_data["vi"])
    details = details_by_lang.get(place["name"], [])
    return templates.TemplateResponse("place_detail.html", {
        "request": request,
        "lang": lang,
        "menu": data["menu"],
        "place": place,
        "details": details
    })

    # Lấy danh sách bình luận đang active
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, comment, img, token, status FROM comments WHERE status='active'")
    rows = c.fetchall()
    conn.close()
    comments = [dict_from_row(r) for r in rows]

    # Render ra index.html, truyền thêm biến page = "place_detail"
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data,
            "lang": lang,
            "comments": comments,
            "place": place,
            "place_details": place_details,
            "is_admin": False,
            "page": "place_detail"
        },
    )
