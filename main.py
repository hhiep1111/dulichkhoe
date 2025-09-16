from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Dữ liệu đa ngôn ngữ
content = {
    "vi": {
        "title": "Du lịch Khỏe - Đồng bằng Sông Cửu Long",
        "intro": "Khám phá miền Tây Nam Bộ: sông nước, ẩm thực và văn hóa độc đáo.",
        "about": "Xin chào! Tôi là hướng dẫn viên du lịch miền Tây. Trang web này chia sẻ các địa điểm, văn hóa và ẩm thực nổi bật.",
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
        "about": "Hello! I am a travel guide in the Mekong Delta. This website shares places, culture, and local food.",
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
        "about": "안녕하세요! 저는 메콩델타 여행 가이드입니다. 이 웹사이트는 여행지, 문화, 음식을 공유합니다.",
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

# Home
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, lang: str = "vi"):
    return templates.TemplateResponse("index.html", {"request": request, "page": "home", "data": content[lang], "lang": lang})

# About
@app.get("/about", response_class=HTMLResponse)
async def about(request: Request, lang: str = "vi"):
    return templates.TemplateResponse("index.html", {"request": request, "page": "about", "data": content[lang], "lang": lang})

# Tips
@app.get("/tips", response_class=HTMLResponse)
async def tips(request: Request, lang: str = "vi"):
    return templates.TemplateResponse("index.html", {"request": request, "page": "tips", "data": content[lang], "lang": lang})

# Nhận bình luận
@app.post("/comment")
async def comment(name: str = Form(...), email: str = Form(...), comment: str = Form(...)):
    print(f"📩 New comment from {name} ({email}): {comment}")
    return RedirectResponse("/", status_code=303)
