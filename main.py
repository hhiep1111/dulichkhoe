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

# ---------------- HELPER ----------------
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

def is_admin_user(credentials: HTTPBasicCredentials = Depends(security)):
    return credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS

# ---------------- DATA ----------------
content = {
    "vi": {
        "title": "Du lịch Khỏe - Đồng bằng Sông Cửu Long",
        "intro": "Khám phá miền Tây Nam Bộ: sông nước, ẩm thực và văn hóa độc đáo.",
        "menu": {"home":"Trang chủ","about":"Giới thiệu","tips":"Lưu ý","lang":"Ngôn ngữ"},
        "about": "Xin chào, chúng ta là những người yêu thích du lịch và văn hóa miền Tây.",
        "places": [
            {"name": "Chợ nổi Cái Răng (Cần Thơ)", "img": "cantho.jpg", "desc": "Trải nghiệm chợ nổi buổi sáng, thưởng thức bún riêu và trái cây trên ghe."},
            {"name": "Phú Quốc (Kiên Giang)", "img": "phuquoc.jpg", "desc": "Thiên đường biển đảo với bãi cát trắng, nước trong xanh và hải sản tươi ngon."},
            {"name": "Miếu Bà Chúa Xứ Núi Sam (An Giang)", "img": "angiang.jpg", "desc": "Điểm đến tâm linh nổi tiếng, kết hợp với cảnh núi non hùng vĩ."}
        ],
        "warn": [
            {"text":"1. Trước khi đi","img":None},
            {"text":"Tìm hiểu thông tin điểm đến: thời tiết, phong tục, tình hình an ninh, phương tiện di chuyển.","img":None},
            {"text":"Chuẩn bị giấy tờ: CMND/CCCD, hộ chiếu, vé máy bay/tàu xe, bảo hiểm du lịch (nếu có).","img":None},
            {"text":"Sao lưu giấy tờ: chụp ảnh hoặc lưu bản scan để phòng khi thất lạc.","img":None},
            {"text":"Kiểm tra sức khỏe: mang theo thuốc cá nhân, giấy tờ y tế cần thiết.","img":None},
            {"text":"2. Khi di chuyển","img":None},
            {"text":"Không để hành lý xa tầm mắt, đặc biệt ở sân bay, bến xe, ga tàu.","img":None},
            {"text":"Giữ đồ có giá trị bên người (tiền, điện thoại, hộ chiếu).","img":None},
            {"text":"Chọn phương tiện uy tín: taxi, xe công nghệ, hoặc phương tiện công cộng chính thống.","img":None}
        ],
        "checklist": [
            {"title":"Quần áo","items":["Đồ lót","Tất","Vớ/bít tất","Áo blouse","Áo (tops)","Quần, jeans, legging"]},
            {"title":"Phụ kiện","items":["Giày đi bộ","Giày cao gót","Sneakers","Thắt lưng"]},
        ]
    },
    "en": {
        "title": "Healthy Travel - Mekong Delta",
        "intro": "Explore the Mekong Delta: waterways, cuisine, and unique culture.",
        "menu": {"home":"Home","about":"About Us","tips":"Tips","lang":"Language"},
        "about": "Hello, we are people who love traveling and Western culture.",
        "places": [
            {"name":"Cai Rang Floating Market (Can Tho)","img":"cantho.jpg","desc":"Experience the morning floating market with noodles and fresh fruits."}
        ],
        "warn":[
            {"text":"1. Before going","img":None},
            {"text":"Find out about the destination: weather, customs, security situation, transportation.","img":None}
        ],
        "checklist":[
            {"title":"Clothes","items":["Underwear","Socks","Tops"]},
        ]
    },
    "kr": {
        "title": "건강 여행 - 메콩델타",
        "intro": "메콩델타 탐험: 강, 음식, 독특한 문화.",
        "menu":{"home":"홈","about":"소개","tips":"여행 유의사항","lang":"언어"},
        "about":"안녕하세요, 저희는 여행과 서양 문화를 사랑하는 사람들입니다.",
        "places":[
            {"name":"까이랑 수상시장 (껀터)","img":"cantho.jpg","desc":"아침 수상시장에서 국수와 신선한 과일을 즐기세요."}
        ],
        "warn":[
            {"text":"1. 출발 전","img":None},
            {"text":"목적지 정보 확인: 날씨, 세관, 보안 상황, 교통수단","img":None}
        ],
        "checklist":[
            {"title":"의류","items":["속옷","양말","상의"]},
        ]
    }
}

# ---------------- ROUTES ----------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, lang: str = "vi", page: str = "home"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id,name,email,text,img,token,status FROM comments WHERE status='active'")
    rows = c.fetchall()
    conn.close()

    comments=[]
    for r in rows:
        comments.append({
            "id": r[0], "name": r[1], "email": r[2], "text": r[3], "img": r[4],
            "token": r[5], "verified": r[6]=="active", "is_owner": False
        })

    return templates.TemplateResponse(
        "index.html",
        {"request":request, "data":content.get(lang, content["vi"]),
         "lang":lang, "page":page, "comments":comments, "is_admin":False}
    )

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request, lang: str="vi"):
    return await home(request, lang=lang, page="about")

@app.get("/tips", response_class=HTMLResponse)
async def tips(request: Request, lang: str="vi"):
    return await home(request, lang=lang, page="tips")

# ---------------- COMMENT ----------------
@app.post("/comment")
async def add_comment(request: Request, background_tasks: BackgroundTasks,
                      name: str = Form(...), email: str = Form(...),
                      comment: str = Form(...), image: UploadFile = File(None),
                      lang: str = Form("vi")):
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
    c.execute("INSERT INTO comments (id,name,email,text,img,token,status) VALUES (?,?,?,?,?,?,?)",
              (comment_id,name,email,comment,img_filename,token,"pending"))
    conn.commit()
    conn.close()

    verify_link = f"http://localhost:8000/verify_email?token={token}&lang={lang}"
    background_tasks.add_task(send_email,email,verify_link)

    return RedirectResponse(url="/comment", status_code=303)

@app.get("/comment", response_class=HTMLResponse)
async def get_comments(request: Request, lang:str="vi"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id,name,email,text,img,token,status FROM comments")
    rows=c.fetchall()
    conn.close()

    comments=[]
    for r in rows:
        comments.append({
            "id": r[0], "name": r[1], "email": r[2], "text": r[3],
            "img": r[4], "token": r[5], "verified": r[6]=="active", "is_owner":False
        })

    return templates.TemplateResponse(
        "index.html",
        {"request":request,
         "data":{"title":"Bình luận","intro":"Xem các bình luận từ người dùng",
                 "menu":content["vi"]["menu"],"about":"Trang web chia sẻ du lịch",
                 "places":[],"warn":[],"checklist":[]},
         "lang":lang,"page":"comments","comments":comments,"is_admin":False}
    )

@app.get("/verify_email")
async def verify_email(token:str, lang:str="vi"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE comments SET status='active' WHERE token=?", (token,))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/comment?lang={lang}", status_code=303)

@app.post("/delete_comment")
async def delete_comment(id:str=Form(...), token:str=Form(...),
                         credentials: HTTPBasicCredentials=Depends(security)):
    is_admin = credentials.username==ADMIN_USER and credentials.password==ADMIN_PASS
    conn=sqlite3.connect(DB_FILE)
    c=conn.cursor()
    c.execute("SELECT token,img FROM comments WHERE id=?", (id,))
    row=c.fetchone()
    if row and (row[0]==token or is_admin):
        if row[1]:
            img_path=os.path.join("uploads",row[1])
            if os.path.exists(img_path):
                os.remove(img_path)
        c.execute("DELETE FROM comments WHERE id=?", (id,))
        conn.commit()
    conn.close()
    return RedirectResponse(url="/comment", status_code=303)
