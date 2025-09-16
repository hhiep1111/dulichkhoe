import os
import uuid
import sqlite3
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

# Mount static và uploads
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

DB_FILE = "comments.db"

# ---------------- INIT DB ----------------
def init_db():
    os.makedirs("uploads", exist_ok=True)  # tạo thư mục uploads nếu chưa có
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            text TEXT,
            img TEXT,
            token TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- DATA ----------------
content = {
    "vi": {
        "title": "Du lịch Khỏe - Đồng bằng Sông Cửu Long",
        "intro": "Khám phá miền Tây Nam Bộ: sông nước, ẩm thực và văn hóa độc đáo.",
        "menu": {
            "home": "Trang chủ",
            "about": "Giới thiệu",
            "tips": "Lưu ý",
            "lang": "Ngôn ngữ"
        },
        "about": "Xin chào, chúng ta là những người yêu thích du lịch và văn hóa miền Tây.",
        "places": [
            {"name": "Chợ nổi Cái Răng (Cần Thơ)", "img": "cantho.jpg", "desc": "Trải nghiệm chợ nổi buổi sáng, thưởng thức bún riêu và trái cây trên ghe."},
            {"name": "Phú Quốc (Kiên Giang)", "img": "phuquoc.jpg", "desc": "Thiên đường biển đảo với bãi cát trắng, nước trong xanh và hải sản tươi ngon."},
            {"name": "Miếu Bà Chúa Xứ Núi Sam (An Giang)", "img": "angiang.jpg", "desc": "Điểm đến tâm linh nổi tiếng, kết hợp với cảnh núi non hùng vĩ."},
        ],
        "warn": [
            "    1. Trước khi đi",
                "        Tìm hiểu thông tin điểm đến: thời tiết, phong tục, tình hình an ninh, phương tiện di chuyển.",
                "        Chuẩn bị giấy tờ: CMND/CCCD, hộ chiếu, vé máy bay/tàu xe, bảo hiểm du lịch (nếu có).",
                "        Sao lưu giấy tờ: chụp ảnh hoặc lưu bản scan để phòng khi thất lạc.",
                "        Kiểm tra sức khỏe: mang theo thuốc cá nhân, giấy tờ y tế cần thiết.",
            "    2. Khi di chuyển",
                "        Không để hành lý xa tầm mắt, đặc biệt ở sân bay, bến xe, ga tàu.",
                "        Giữ đồ có giá trị bên người (tiền, điện thoại, hộ chiếu).",
                "        Chọn phương tiện uy tín: taxi, xe công nghệ, hoặc phương tiện công cộng chính thống.",
            "    3. Khi lưu trú",
                "        Chọn khách sạn/nhà nghỉ an toàn: có đánh giá tốt, hệ thống an ninh.",
                "        Khóa cửa cẩn thận khi ra ngoài và cả khi ở trong phòng.",
                "        Không tiết lộ số phòng với người lạ.",
            "    4. Khi tham quan",
                "        Không mang theo quá nhiều tiền mặt hoặc đồ quý giá.",
                "        Cẩn thận với túi xách, balo ở nơi đông người (chợ, lễ hội, bến xe).",
                "        Tuân thủ quy định địa phương: không xả rác, không leo trèo nguy hiểm, tôn trọng văn hóa bản địa.",
                "        Luôn đi theo nhóm nếu ở nơi vắng vẻ hoặc không quen thuộc.",
            "        5. An toàn công nghệ",
                "        Không dùng Wi-Fi công cộng để giao dịch tài chính.",
                "        Cẩn thận khi chia sẻ vị trí trên mạng xã hội để tránh kẻ xấu lợi dụng."
        ]
    },
    "en": {
        "title": "Healthy Travel - Mekong Delta",
        "intro": "Explore the Mekong Delta: waterways, cuisine, and unique culture.",
        "menu": {
            "home": "Home",
            "about": "About Us",
            "tips": "Tips",
            "lang": "Language"
        },
        "about": "Hello, we are people who love traveling and Western culture.",
        "places": [
            {"name": "Cai Rang Floating Market (Can Tho)", "img": "cantho.jpg", "desc": "Experience the morning floating market with noodles and fresh fruits."},
            {"name": "Phu Quoc Island (Kien Giang)", "img": "phuquoc.jpg", "desc": "A paradise with white sand beaches, clear water, and fresh seafood."},
            {"name": "Ba Chua Xu Temple (An Giang)", "img": "angiang.jpg", "desc": "A famous spiritual site with majestic mountain scenery."},
        ],
        "warn": [
            "     1. Before going",
"         Find out about the destination: weather, customs, security situation, means of transportation.",
"         Prepare documents: ID card/CCCD, passport, plane/train ticket, travel insurance (if any).",
"         Back up documents: take photos or save scans in case of loss.",
"         Check your health: bring personal medicine, necessary medical documents.",
"     2. When traveling",
"         Do not leave luggage out of sight, especially at airports, bus stations, train stations.",
"         Keep valuables on your person (money, phone, passport).",
"         Choose a reputable means of transportation: taxi, technology car, or official public transportation.",
"     3. When staying",
"         Choose a safe hotel/guesthouse: good reviews, security system.",
"         Lock the door carefully when going out and when in the room.",
"         Do not reveal the room number to others strange.",
"     4. When visiting",
"         Do not carry too much cash or valuables.",
"         Be careful with bags and backpacks in crowded places (markets, festivals, bus stations).",
"         Comply with local regulations: do not litter, do not climb dangerously, respect local culture.",
"         Always go in groups if in deserted or unfamiliar places.",
"     5. Technology safety",
"         Do not use public Wi-Fi for financial transactions.",
"         Be careful when sharing your location on social networks to avoid bad guys taking advantage."
        ]
    },
    "kr": {
        "title": "건강 여행 - 메콩델타",
        "intro": "메콩델타 탐험: 강, 음식, 독특한 문화.",
        "menu": {
            "home": "홈",
            "about": "소개",
            "tips": "여행 유의사항",
            "lang": "언어"
        },
        "about": "안녕하세요, 저희는 여행과 서양 문화를 사랑하는 사람들입니다.",
        "places": [
            {"name": "까이랑 수상시장 (껀터)", "img": "cantho.jpg", "desc": "아침 수상시장에서 국수와 신선한 과일을 즐기세요."},
            {"name": "푸꾸옥 섬 (끼엔장)", "img": "phuquoc.jpg", "desc": "하얀 모래 해변과 맑은 바다, 신선한 해산물의 천국."},
            {"name": "바쭈어쓰 사원 (안장)", "img": "angiang.jpg", "desc": "웅장한 산 풍경과 유명한 영적 명소."},
        ],
        "warn": [
            "    1. 출발 전",
            "        목적지 정보 확인: 날씨, 세관, 보안 상황, 교통수단",
            "        서류 준비: 신분증/CCCD, 여권, 비행기/기차표, 여행자 보험(있는 경우)",
            "        서류 백업: 분실에 대비하여 사진을 찍거나 스캔본을 저장하세요.",
            "        건강 상태 확인: 개인 상비약, 필요한 의료 서류 지참",
            "    2. 여행 시",
            "        특히 공항, 버스 정류장, 기차역에서 짐을 눈에 띄지 않는 곳에 두지 마세요.",
            "        귀중품(현금, 휴대폰, 여권)은 직접 휴대하세요.",
            "        택시, 이동 차량, 또는 대중교통 등 신뢰할 수 있는 교통수단을 선택하세요.",
            "    3. 숙박 시",
            "        안전한 호텔/게스트하우스 선택: 좋은 후기, 보안 시스템",
            "        외출 시와 객실 내에서는 문을 단단히 잠그세요.",
"        낯선 사람에게 객실 번호를 알려주지 마세요.",
"    4. 방문 시",
"        현금이나 귀중품을 너무 많이 가지고 다니지 마세요.",
"        가방 조심 혼잡한 장소(시장, 축제, 버스 정류장)에서는 배낭을 지참하지 마십시오.",
"        지역 규정을 준수하십시오: 쓰레기를 버리지 말고, 위험한 등반을 하지 말고, 지역 문화를 존중하십시오.",
"        인적이 드물거나 낯선 장소에는 항상 무리 지어 다니십시오.",
"    5. 기술 안전",
"        금융 거래 시 공용 Wi-Fi를 사용하지 마십시오.",
"        소셜 네트워크에 위치를 공유할 때는 악의적인 공격에 주의하십시오."
        ]
    }
}

# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, lang: str = "vi", page: str = "home"):
    # Lấy comments từ DB
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, text, img, token FROM comments")
    rows = c.fetchall()
    conn.close()

    comments = [
        {"id": r[0], "name": r[1], "email": r[2], "text": r[3], "img": r[4], "token": r[5]}
        for r in rows
    ]

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "data": content[lang], "lang": lang, "page": page, "comments": comments}
    )

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request, lang: str = "vi"):
    return await home(request, lang=lang, page="about")

@app.get("/tips", response_class=HTMLResponse)
async def tips(request: Request, lang: str = "vi"):
    return await home(request, lang=lang, page="tips")

# ---------------- COMMENT (POST) ----------------
@app.post("/comment")
async def add_comment(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    comment: str = Form(...),
    image: UploadFile = File(None),
):
    img_filename = None
    if image:
        os.makedirs("uploads", exist_ok=True)
        img_filename = f"{uuid.uuid4()}_{image.filename}"
        with open(os.path.join("uploads", img_filename), "wb") as f:
            f.write(await image.read())

    comment_id = str(uuid.uuid4())
    token = str(uuid.uuid4())

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO comments (id, name, email, text, img, token) VALUES (?, ?, ?, ?, ?, ?)",
              (comment_id, name, email, comment, img_filename, token))
    conn.commit()
    conn.close()

    # 🔴 Sau khi thêm xong thì redirect về /comment (không redirect về /)
    return RedirectResponse(url="/comment", status_code=303)
    
# ---------------- GET COMMENT PAGE ----------------
@app.get("/comment", response_class=HTMLResponse)
async def get_comments(request: Request, lang: str = "vi"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, text, img, token FROM comments")
    rows = c.fetchall()
    conn.close()

    comments = [
        {"id": r[0], "name": r[1], "email": r[2], "text": r[3], "img": r[4], "token": r[5]}
        for r in rows
    ]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": {
                "title": "Bình luận",
                "intro": "Xem các bình luận từ người dùng",
                "menu": {
                    "home": "Trang chủ",
                    "about": "Giới thiệu",
                    "tips": "Lưu ý",
                    "lang": "Ngôn ngữ"
                },
                "about": "Trang web chia sẻ du lịch.",
                "places": [],
                "warn": []
            },
            "lang": lang,
            "page": "comments",
            "comments": comments
        }
    )

# ---------------- DELETE COMMENT ----------------
@app.post("/delete_comment")
async def delete_comment(id: str = Form(...), token: str = Form(...)):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT token, img FROM comments WHERE id=?", (id,))
    row = c.fetchone()
    if row and row[0] == token:
        if row[1]:
            img_path = os.path.join("uploads", row[1])
            if os.path.exists(img_path):
                os.remove(img_path)
        c.execute("DELETE FROM comments WHERE id=?", (id,))
        conn.commit()
    conn.close()

    return RedirectResponse(url="/", status_code=303)
