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
        "about": "Xin chào, tôi là Hiep, người yêu thích du lịch và văn hóa miền Tây.",
        "places": [
            {"name": "Chợ nổi Cái Răng (Cần Thơ)", "img": "cantho.jpg", "desc": "Trải nghiệm chợ nổi buổi sáng, thưởng thức bún riêu và trái cây trên ghe."},
            {"name": "Phú Quốc (Kiên Giang)", "img": "phuquoc.jpg", "desc": "Thiên đường biển đảo với bãi cát trắng, nước trong xanh và hải sản tươi ngon."},
            {"name": "Miếu Bà Chúa Xứ Núi Sam (An Giang)", "img": "angiang.jpg", "desc": "Điểm đến tâm linh nổi tiếng, kết hợp với cảnh núi non hùng vĩ."},
        ],
        "warn": [
            "Không xả rác xuống sông.",
            "Hạn chế chen lấn ở chợ nổi.",
            "Luôn hỏi giá trước khi mua đồ lưu niệm."
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
        "about": "Hello, I'm Hiep, a travel enthusiast passionate about Mekong Delta culture.",
        "places": [
            {"name": "Cai Rang Floating Market (Can Tho)", "img": "cantho.jpg", "desc": "Experience the morning floating market with noodles and fresh fruits."},
            {"name": "Phu Quoc Island (Kien Giang)", "img": "phuquoc.jpg", "desc": "A paradise with white sand beaches, clear water, and fresh seafood."},
            {"name": "Ba Chua Xu Temple (An Giang)", "img": "angiang.jpg", "desc": "A famous spiritual site with majestic mountain scenery."},
        ],
        "warn": [
            "Do not litter in rivers.",
            "Avoid crowding in floating markets.",
            "Always ask the price before shopping souvenirs."
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
        "about": "안녕하세요, 저는 메콩델타 여행과 문화를 좋아하는 히엡입니다.",
        "places": [
            {"name": "까이랑 수상시장 (껀터)", "img": "cantho.jpg", "desc": "아침 수상시장에서 국수와 신선한 과일을 즐기세요."},
            {"name": "푸꾸옥 섬 (끼엔장)", "img": "phuquoc.jpg", "desc": "하얀 모래 해변과 맑은 바다, 신선한 해산물의 천국."},
            {"name": "바쭈어쓰 사원 (안장)", "img": "angiang.jpg", "desc": "웅장한 산 풍경과 유명한 영적 명소."},
        ],
        "warn": [
            "강에 쓰레기를 버리지 마세요.",
            "수상시장에서 혼잡을 피하세요.",
            "기념품을 살 때 반드시 가격을 확인하세요."
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
