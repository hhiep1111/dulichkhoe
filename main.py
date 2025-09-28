import os
import uuid
import sqlite3
import smtplib
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
        status TEXT DEFAULT 'pending'
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
        "comment": row[3],
        "img": row[4],
        "status": row[5],
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
        "menu": {"home": "Trang chủ", "about": "Giới thiệu", "tips": "Lưu ý", "checklist": "Check-list", "lang": "Ngôn ngữ"},
        "about": "Xin chào, chúng ta là những người yêu thích du lịch và văn hóa miền Tây.",
        "places": [
            {"name": "Chợ nổi Cái Răng (Cần Thơ)", "img": "cantho.jpg",
             "desc": "Trải nghiệm chợ nổi buổi sáng, thưởng thức bún riêu và trái cây trên ghe."},
            {"name": "Phú Quốc (Kiên Giang)", "img": "phuquoc.jpg",
             "desc": "Thiên đường biển đảo với bãi cát trắng, nước trong xanh và hải sản tươi ngon."},
            {"name": "Miếu Bà Chúa Xứ Núi Sam (An Giang)", "img": "angiang.jpg",
             "desc": "Điểm đến tâm linh nổi tiếng, kết hợp với cảnh núi non hùng vĩ."},
        ],
        "warn": [
            "1. Trước khi đi",
            "Tìm hiểu thông tin điểm đến: thời tiết, phong tục, tình hình an ninh, phương tiện di chuyển.",
            "Chuẩn bị giấy tờ: CMND/CCCD, hộ chiếu, vé máy bay/tàu xe, bảo hiểm du lịch (nếu có).",
            "Sao lưu giấy tờ: chụp ảnh hoặc lưu bản scan để phòng khi thất lạc.",
            "Kiểm tra sức khỏe: mang theo thuốc cá nhân, giấy tờ y tế cần thiết.",
            "2. Khi di chuyển",
            "Không để hành lý xa tầm mắt, đặc biệt ở sân bay, bến xe, ga tàu.",
            "Giữ đồ có giá trị bên người (tiền, điện thoại, hộ chiếu).",
            "Chọn phương tiện uy tín: taxi, xe công nghệ, hoặc phương tiện công cộng chính thống.",
            "3. Khi lưu trú",
            "Chọn khách sạn/nhà nghỉ an toàn: có đánh giá tốt, hệ thống an ninh.",
            "Khóa cửa cẩn thận khi ra ngoài và cả khi ở trong phòng.",
            "Không tiết lộ số phòng với người lạ.",
            "4. Khi tham quan",
            "Không mang theo quá nhiều tiền mặt hoặc đồ quý giá.",
            "Cẩn thận với túi xách, balo ở nơi đông người (chợ, lễ hội, bến xe).",
            "Tuân thủ quy định địa phương: không xả rác, không leo trèo nguy hiểm, tôn trọng văn hóa bản địa.",
            "Luôn đi theo nhóm nếu ở nơi vắng vẻ hoặc không quen thuộc.",
            "5. An toàn công nghệ",
            "Không dùng Wi-Fi công cộng để giao dịch tài chính.",
            "Cẩn thận khi chia sẻ vị trí trên mạng xã hội để tránh kẻ xấu lợi dụng."
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
        ]
    },

    "en": {
        "title": "Healthy Travel - Mekong Delta",
        "intro": "Explore Southern Vietnam: rivers, cuisine, and unique culture.",
        "menu": {"home": "Home", "about": "About", "tips": "Tips", "checklist": "Check-list", "lang": "Language"},
        "about": "Hello, we are passionate about traveling and the culture of Southern Vietnam.",
        "places": [
            {"name": "Cai Rang Floating Market (Can Tho)", "img": "cantho.jpg",
             "desc": "Experience the morning floating market, enjoy Bun Rieu and fruits on boats."},
            {"name": "Phu Quoc Island (Kien Giang)", "img": "phuquoc.jpg",
             "desc": "Island paradise with white sandy beaches, clear waters, and fresh seafood."},
            {"name": "Ba Chua Xu Temple (Sam Mountain, An Giang)", "img": "angiang.jpg",
             "desc": "Famous spiritual destination with majestic mountains."},
        ],
        "warn": [
            "1. Before you go",
            "Research your destination: weather, customs, security situation, transportation.",
            "Prepare documents: ID card, passport, tickets, travel insurance (if any).",
            "Backup documents: take photos or scan copies in case of loss.",
            "Check health: bring personal medicine and necessary medical papers.",
            "2. During travel",
            "Do not leave luggage unattended, especially at airports, bus stations, or train stations.",
            "Keep valuables with you (money, phone, passport).",
            "Choose reliable transportation: taxi, ride-hailing, or official public transport.",
            "3. Accommodation",
            "Choose safe hotels/hostels: good reviews, security system.",
            "Lock doors carefully when going out and inside rooms.",
            "Do not disclose room number to strangers.",
            "4. Sightseeing",
            "Do not carry too much cash or valuables.",
            "Be careful with bags and backpacks in crowded places (markets, festivals, stations).",
            "Follow local regulations: no littering, avoid dangerous climbing, respect local culture.",
            "Always travel in groups if in unfamiliar or deserted areas.",
            "5. Technology safety",
            "Do not use public Wi-Fi for financial transactions.",
            "Be cautious when sharing your location on social media to avoid malicious use."
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
        "menu": {"home": "홈", "about": "소개", "tips": "유의사항", "checklist": "체크리스트", "lang": "언어"},
        "about": "안녕하세요, 우리는 남부 베트남의 여행과 문화를 사랑하는 사람들입니다.",
        "places": [
            {"name": "카이랑 수상시장 (깐토)", "img": "cantho.jpg",
             "desc": "아침 수상시장을 체험하고, 보트 위에서 분리유와 과일을 즐기세요."},
            {"name": "푸꾸옥 섬 (끼엔장)", "img": "phuquoc.jpg",
             "desc": "하얀 모래사장, 맑은 바닷물, 신선한 해산물이 있는 섬의 천국."},
            {"name": "바추슈 사원 (삼산, 안장)", "img": "angiang.jpg",
             "desc": "장엄한 산과 함께 유명한 영적 명소."},
        ],
        "warn": [
            "1. 여행 전",
            "목적지 조사: 날씨, 관습, 안전 상황, 교통편.",
            "서류 준비: 신분증, 여권, 티켓, 여행자 보험(있다면).",
            "서류 백업: 분실 대비 사진 또는 스캔본 보관.",
            "건강 체크: 개인 약품 및 필요한 의료 서류 지참.",
            "2. 이동 중",
            "짐을 방치하지 말 것, 특히 공항, 버스터미널, 기차역에서.",
            "귀중품은 항상 소지할 것 (돈, 휴대폰, 여권).",
            "신뢰할 수 있는 교통수단 선택: 택시, 라이드헤일링, 공식 대중교통.",
            "3. 숙박",
            "안전한 호텔/호스텔 선택: 좋은 리뷰, 보안 시스템.",
            "외출 시와 방 안에서도 문 잠금 주의.",
            "낯선 사람에게 객실 번호를 공개하지 말 것.",
            "4. 관광",
            "너무 많은 현금이나 귀중품을 소지하지 말 것.",
            "사람이 많은 장소(시장, 축제, 역)에서 가방과 배낭 주의.",
            "현지 규정 준수: 쓰레기 투기 금지, 위험한 등반 피하기, 지역 문화 존중.",
            "익숙하지 않거나 인적 드문 지역에서는 항상 그룹으로 이동.",
            "5. 기술 안전",
            "금융 거래에 공용 Wi-Fi 사용 금지.",
            "SNS에 위치 공유 시 악용될 수 있으니 주의."
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
# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, lang: str = "vi"):
    data = content.get(lang, content["vi"])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, comment, img, status FROM comments")
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
    c.execute("SELECT id, name, email, comment, img, status FROM comments")
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
    c.execute("SELECT id, name, email, comment, img, status FROM comments")
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
    c.execute("SELECT id, name, email, comment, img, status FROM comments")
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
        },
    )
# ---------------- COMMENT ----------------
@app.post("/comment")
async def comment(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    comment: str = Form(...),
    lang: str = Form("vi"),
    image: UploadFile = File(None),
):
    filename = None
    if image:
        filename = f"{uuid.uuid4()}_{image.filename}"
        filepath = os.path.join("uploads", filename)
        with open(filepath, "wb") as buffer:
            buffer.write(await image.read())

    token = str(uuid.uuid4())
    comment_id = str(uuid.uuid4())
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO comments (id, name, email, comment, img, token, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (comment_id, name, email, comment, filename, token, "pending"),
    )
    conn.commit()
    conn.close()

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
    c.execute("SELECT id, name, email, comment, img, status FROM comments")
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
@app.post("/delete/{comment_id}")
async def delete_comment(
    comment_id: str,
    lang: str = "vi",
    credentials: HTTPBasicCredentials = Depends(security),
):
    if not (credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS):
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM comments WHERE id=?", (comment_id,))
    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/admin?lang={lang}", status_code=303)


# ---------------- VERIFY EMAIL ----------------

@app.get("/verify_email")
async def verify_email(token: str, lang: str = "vi"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE comments SET status='active' WHERE token=?", (token,))
    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/?lang={lang}", status_code=303)

@app.post("/admin_verify_email")
async def admin_verify_email(
    id: str = Form(...),
    credentials: HTTPBasicCredentials = Depends(security),
):
    if not (credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS):
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE comments SET status='active' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    
    return RedirectResponse(url="/admin", status_code=303)
