import os
import uuid
import sqlite3
from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import smtplib

app = FastAPI()

# Mount static và uploads
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

DB_FILE = "comments.db"
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "123456")

security = HTTPBasic()

# ---------------- INIT DB ----------------
os.makedirs("uploads", exist_ok=True)
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    text TEXT,
    img TEXT,
    token TEXT,
    status TEXT DEFAULT 'pending'
)
""")
conn.commit()
conn.close()

# ---------------- HELPER: Check admin ----------------
def is_admin_user(credentials: HTTPBasicCredentials = Depends(security)):
    return credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS

def send_email(to_email: str, link: str):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("your_email@gmail.com", "your_password")
        msg = f"Subject: Xác nhận email\n\nClick link để xác nhận: {link}"
        server.sendmail("your_email@gmail.com", to_email, msg)
        server.quit()
    except Exception as e:
        print("Error sending email:", e)

# ---------------- DATA ----------------
content = {
    "vi": {
        "title": "Du lịch Khỏe - Đồng bằng Sông Cửu Long",
        "intro": "Khám phá miền Tây Nam Bộ: sông nước, ẩm thực và văn hóa độc đáo.",
        "menu": {"home": "Trang chủ", "about": "Giới thiệu", "tips": "Lưu ý", "lang": "Ngôn ngữ"},
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
    # Nội dung "en" và "kr" tương tự, giữ nguyên như bạn gửi
}

# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, lang: str = "vi", page: str = "home"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, text, img, token, status FROM comments WHERE status='active'")
    rows = c.fetchall()
    conn.close()

    comments = []
    for r in rows:
        comments.append({
            "id": r[0],
            "name": r[1],
            "email": None,
            "text": r[3],
            "img": r[4],
            "token": r[5],
            "is_owner": False,
            "verified": r[6] == "active"
        })

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": content.get(lang, content["vi"]),
            "lang": lang,
            "page": page,
            "comments": comments,
            "is_admin": False
        }
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
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    email: str = Form(...),
    comment: str = Form(...),
    image: UploadFile = File(None),
    lang: str = Form("vi")
):
    img_filename = None
    if image and image.filename:
        os.makedirs("uploads", exist_ok=True)
        img_filename = f"{uuid.uuid4()}_{image.filename}"
        with open(os.path.join("uploads", img_filename), "wb") as f:
            f.write(await image.read())

    comment_id = str(uuid.uuid4())
    token = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """INSERT INTO comments (id, name, email, text, img, token, status) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (comment_id, name, email, comment, img_filename, token, "pending")
    )
    conn.commit()
    conn.close()

    verify_link = f"http://localhost:8000/verify_email?token={token}&lang={lang}"
    background_tasks.add_task(send_email, email, verify_link)

    return RedirectResponse(url="/comment", status_code=303)

# ---------------- GET COMMENT PAGE ----------------
@app.get("/comment", response_class=HTMLResponse)
async def get_comments(request: Request, lang: str = "vi"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, text, img, token, status FROM comments")
    rows = c.fetchall()
    conn.close()

    comments = []
    for r in rows:
        comments.append({
            "id": r[0],
            "name": r[1],
            "email": None,
            "text": r[3],
            "img": r[4],
            "token": r[5],
            "verified": r[6] == "active",
            "is_owner": False
        })

    return templates.TemplateResponse(
        "index .html",
{
"request": request,
"data": {
"title": "Bình luận",
"intro": "Xem các bình luận từ người dùng",
"menu": content["vi"]["menu"],
"about": "Trang web chia sẻ du lịch.",
"places": [],
"warn": [],
"checklist": []
},
"lang": lang,
"page": "comments",
"comments": comments,
"is_admin": False
}
)

---------------- VERIFY EMAIL ----------------

@app.get("/verify_email")
async def verify_email(token: str, lang: str = "vi"):
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("UPDATE comments SET status='active' WHERE token=?", (token,))
conn.commit()
conn.close()
return RedirectResponse(url=f"/comment?lang={lang}", status_code=303)
@app.post("/admin_verify_email")
async def admin_verify_email(
id: str = Form(...),
credentials: HTTPBasicCredentials = Depends(security)
):
if credentials.username != ADMIN_USER or credentials.password != ADMIN_PASS:
return RedirectResponse(url="/", status_code=401) 
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("UPDATE comments SET status='active' WHERE id=?", (id,))
conn.commit()
conn.close()
return RedirectResponse(url="/admin", status_code=303)
---------------- DELETE COMMENT ----------------

@app.post("/delete_comment")
async def delete_comment(
id: str = Form(...),
token: str = Form(...),
credentials: HTTPBasicCredentials = Depends(security)
):
is_admin = credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("SELECT token, img FROM comments WHERE id=?", (id,))
row = c.fetchone()
if row and (row[0] == token or is_admin):
if row[1]:
img_path = os.path.join("uploads", row[1])
if os.path.exists(img_path):
os.remove(img_path)
c.execute("DELETE FROM comments WHERE id=?", (id,))
conn.commit()
conn.close()
return RedirectResponse(url="/comment", status_code=303)

---------------- ADMIN PAGE ----------------

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(credentials: HTTPBasicCredentials = Depends(security)):
if credentials.username != ADMIN_USER or credentials.password != ADMIN_PASS:
return RedirectResponse(url="/", status_code=401) 
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("SELECT id, name, email, text, img, token, status FROM comments")
rows = c.fetchall()
conn.close()

comments = []
for r in rows:
    comments.append({
        "id": r[0],
        "name": r[1],
        "email": r[2],
        "text": r[3],
        "img": r[4],
        "token": r[5],
        "status": r[6],
    })

return templates.TemplateResponse(
    "admin.html",
    {
        "request": {},
        "comments": comments,
        "lang": "vi"
    }
)
