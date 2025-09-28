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
        "tips": [
            {
                "title": "1. Trước khi đi",
                "image": "/static/images/1.jpg",
                "content": [
                    "Tìm hiểu thông tin điểm đến: thời tiết, phong tục, tình hình an ninh, phương tiện di chuyển.",
                    "Chuẩn bị giấy tờ: CMND/CCCD, hộ chiếu, vé máy bay/tàu xe, bảo hiểm du lịch (nếu có).",
                    "Sao lưu giấy tờ: chụp ảnh hoặc lưu bản scan để phòng khi thất lạc.",
                    "Kiểm tra sức khỏe: mang theo thuốc cá nhân, giấy tờ y tế cần thiết."
                    ]
            },
            {
                "title": "2. Khi di chuyển",
                "image": "/static/images/2.jpg",
                "content": [
                    "Không để hành lý xa tầm mắt, đặc biệt ở sân bay, bến xe, ga tàu.",
                    "Giữ đồ có giá trị bên người (tiền, điện thoại, hộ chiếu).",
                    "Chọn phương tiện uy tín: taxi, xe công nghệ, hoặc phương tiện công cộng chính thống."
                ]
            },
            {
                "title": "3. Khi lưu trú",
                "image": "/static/images/3.jpg",
                "content": [
                     "Chọn khách sạn/nhà nghỉ an toàn: có đánh giá tốt, hệ thống an ninh.",
                    "Khóa cửa cẩn thận khi ra ngoài và cả khi ở trong phòng.",
                    "Không tiết lộ số phòng với người lạ."
                ]
            },
            {
                "title": "4. Khi tham quan",
                "image": "/static/images/4.jpg",
                "content": [
                    "Không mang theo quá nhiều tiền mặt hoặc đồ quý giá.",
                    "Cẩn thận với túi xách, balo ở nơi đông người (chợ, lễ hội, bến xe).",
                    "Tuân thủ quy định địa phương: không xả rác, không leo trèo nguy hiểm, tôn trọng văn hóa bản địa.",
                    "Luôn đi theo nhóm nếu ở nơi vắng vẻ hoặc không quen thuộc."
                ]
            },
            {
                "title": "5. An toàn công nghệ",
                "image": "/static/images/5.jpg",
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
        "tips": [
            {
                "title": "1. Before going",
                "image": "/static/images/1.jpg",
                "content": [
                    "Find out information about the destination: weather, customs, security situation, means of transportation.",
                    "Prepare documents: ID card/CCCD, passport, plane/train ticket, travel insurance (if any).",
                    "Back up documents: take photos or save scans in case of loss.",
                    "Check your health: bring personal medicine, necessary medical documents."
                    ]
            },
            {
                "title": "2. When traveling",
                "image": "/static/images/2.jpg",
                "content": [
                    "Do not leave luggage out of sight, especially at airports, bus stations, train stations.",
                    "Keep valuables with you (money, phone, passport).",
                    "Choose reputable means of transport: taxi, technology car, or official public transport."
                ]
            },
            {
                "title": "3. When staying",
                "image": "/static/images/3.jpg",
                "content": [    
                    "Choose a safe hotel/guesthouse: with good reviews, security system.",
                    "Lock the door carefully when going out and when in the room.",
                    "Do not reveal the room number to strangers."
                ]
            },
            {
                "title": "4. When visiting",
                "image": "/static/images/4.jpg",
                "content": [
                    "Do not carry too much cash or valuables.",
                    "Be careful with bags and backpacks in crowded places (markets, festivals, bus stations).",
                    "Comply with local regulations: do not litter, do not climb dangerously, respect local culture.",
                    "Always go in groups if in deserted or unfamiliar places."
                ]
            },
            {
                "title": "5. Technology safety",
                "image": "/static/images/5.jpg",
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
        "tips": [
            {
                "title": "1. 출발 전",
                "image": "/static/images/1.jpg",
                "content": [
                    "목적지 정보 확인: 날씨, 세관, 보안 상황, 교통수단",
                    "서류 준비: 신분증/CCCD, 여권, 비행기/기차표, 여행자 보험(있는 경우)",
                    "서류 백업: 분실에 대비하여 사진을 찍거나 스캔본을 저장하세요.",
                    "건강 상태 확인: 개인 의약품, 필요한 의료 서류를 지참하세요."
                ]
            },
            {
                "title": "2. 여행 시",
                "image": "/static/images/2.jpg",
                "content": [
                    "특히 공항, 버스 정류장, 기차역에서 짐을 눈에 띄지 않는 곳에 두지 마세요.",
                    "귀중품(돈, 휴대폰, 여권)은 항상 지참하세요.",
                    "택시, 이동 차량 또는 공식 대중교통 등 신뢰할 수 있는 교통수단을 이용하세요."
                ]
            },
            {
                "title": "3. 숙박 시",
                "image": "/static/images/3.jpg",
                "content": [
                    "안전한 호텔/게스트하우스를 선택하세요: 좋은 후기와 보안 시스템을 갖추고 있어야 합니다.",
                    "외출 시와 객실 내에서는 문을 단단히 잠그세요.",
                    "낯선 사람에게 객실 번호를 알려주지 마세요."
                ]
            },
            {
                "title": "4. 방문 시",
                "image": "/static/images/4.jpg",
                "content": [
                    "현금이나 귀중품을 너무 많이 가지고 다니지 마세요.",
                    "시장, 축제, 버스 정류장 등 사람이 붐비는 장소에서는 가방과 배낭을 조심하세요.",
                    "지역 규정을 준수하세요: 쓰레기를 버리지 마세요, 위험한 등반을 하지 마세요, 지역 문화를 존중하세요.",
                    "사람이 없는 곳이나 낯선 곳에서는 항상 그룹으로 이동하세요."
                ]
            },
            {
                "title": "5. 기술 안전",
                "image": "/static/images/5.jpg",
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
        },
    )
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
