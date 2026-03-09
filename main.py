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
        "about": [
			{"title": "Về Chúng Tôi",
			"decs": """
			<p>Cảm ơn bạn đã ghé thăm Travel Healing!</p>
			<p>Chúng tôi ở đây để giúp bạn khám phá vùng đất Đồng bằng sông Cửu Long – nơi của những dòng sông hiền hòa, nụ cười thân thiện và những trải nghiệm địa phương khó quên.</p>
			<p>Mục tiêu của chúng tôi rất đơn giản: giúp bạn “cảm nhận miền Tây – chứ không chỉ ghé qua nó.</p>
			<p>Nếu bạn có bất kỳ thắc mắc, góp ý hoặc cần tư vấn du lịch, đừng ngần ngại liên hệ với chúng tôi.</p>
			<p>Chúng tôi là một nhóm sinh viên yêu thích du lịch, văn hóa và kể chuyện, với niềm tin rằng mỗi chuyến đi đều có thể chữa lành tâm hồn.</p>
			"""},
			{"title": "Về Dự Án",
			 "decs": """
			 <p>Travel Healing là một dự án do sinh viên thực hiện, nhằm quảng bá hình ảnh du lịch an toàn – xanh – gần gũi cộng đồng tại khu vực Đồng bằng sông Cửu Long.</p>
			 <p>Chúng tôi mong muốn:</p>
			 <ul>
			 <li>Giới thiệu những điểm đến ít người biết nhưng đầy thú vị.</li>
			 <li>Kết nối du khách với người dân địa phương, homestay và tour trải nghiệm thực tế.</li>
			 <li>Lan tỏa thông điệp du lịch bền vững, để mỗi chuyến đi là một hành trình chữa lành.</li>
			 </ul>
			 <p>Thông điệp của chúng tôi – “Khỏe để đi – đi để khỏe” – thể hiện niềm tin rằng du lịch không chỉ là khám phá nơi mới, mà còn là hành trình tìm lại sự cân bằng trong chính mình.</p>
			 """	
			},
			{"title": "Liên Hệ Với Chúng Tôi",
			 "decs": """
			 <ul>
			 <li>Email: dulichkhoe.official@gmail.com</li>
			 <li>Điện thoại: 0903 000 ***</li>
			 <li>Địa chỉ: Trường Đại học FPT Thành phố Cần Thơ, Việt Nam</li>
			 </ul>
			 """	
			},
			{"title": "Theo Dõi Chúng Tôi",
			 "decs": """
			 <p>Cập nhật những câu chuyện du lịch, hướng dẫn và hình ảnh mới nhất tại:</p>
			 <ul>
			 <li>Facebook: fb.com/dulichkhoe</li>
			 <li>TikTok: @travelhealing***.official</li>
			 </ul>
			 """	
			},
			{"title": "Đồng Hành Cùng Chúng Tôi",
			 "decs": """
			 <p>Bạn yêu miền Tây và muốn góp phần lan tỏa du lịch tích cực?</p>
			 <p>Hãy cùng chúng tôi chia sẻ câu chuyện của bạn, trở thành cộng tác viên hoặc đại sứ của Travel Healing.</p>
			 <p>Cùng nhau, chúng ta xây dựng một cộng đồng du lịch xanh, thật và đầy cảm hứng.</p>
			 """	
			}
		],
        "places": [
            {"name": "Can Tho", "img": "cantho.jpg",
             "desc": "Thủ phủ miền Tây, nổi tiếng với chợ nổi sông nước, miệt vườn trù phú và nét văn hóa miệt vườn thân tình. Trải nghiệm chợ nổi buổi sáng, thưởng thức bún riêu và trái cây trên ghe."},
            {"name": "An Giang", "img": "nuicamangiang.jpg",
             "desc": "Miền đất của núi non Thất Sơn, văn hóa Chăm – Khmer giao thoa, nổi tiếng với cảnh đẹp thiêng liêng và đời sống sông nước hiền hòa."},
            {"name": "Ca Mau", "img": "muicamau.jpg",
            "desc": "Cà Mau là tỉnh cực Nam của Việt Nam, có ba mặt giáp biển, nổi bật với hệ sinh thái rừng ngập mặn, đầm phá, đảo nhỏ và điểm cực Nam thiêng liêng của Tổ quốc. Thiên nhiên hoang sơ, văn hóa sông nước và ẩm thực phong phú là những điểm hấp dẫn của du lịch Cà Mau"},
            {"name": "Vinh Long", "img": "vinhlong.jpg",
            "desc": "Vĩnh Long nằm giữa sông Tiền và sông Hậu, là trung tâm của vùng sông nước miền Tây. Nơi đây nổi bật với hệ thống kênh rạch chằng chịt, vườn cây ăn trái trĩu quả, cùng không gian miệt vườn thanh bình."},
            {"name": "Dong Thap", "img": "dongthap.jpg",
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
             "title": "Bánh Cống Sóc Trăng",
             "img": "/static/images/banhcong.jpg",
             "short": "Bánh cống Đại Tâm vàng ươm, thơm mùi bột gạo và tôm, phần nhân đậu xanh bùi béo – hương vị hài hòa, ăn hoài không ngán.",
             "desc": """
                 <p>Bánh Cống Đại Tâm là đặc sản trứ danh của huyện Mỹ Xuyên, tỉnh Sóc Trăng, đặc biệt là tại xã Đại Tâm – nơi có đông đồng bào Khmer sinh sống.</p>
				 <p>Món bánh được đặt tên theo địa danh “Đại Tâm”, nơi khởi nguồn của nghề làm bánh cống truyền thống đã tồn tại hơn nửa thế kỷ.</p>
				 <p>“Cống” là dụng cụ hình ống trụ (giống chiếc ly nhỏ) – được đổ bột và nhân vào, sau đó nhúng ngập trong chảo dầu nóng cho đến khi vàng đều.</p>
                 <p>📍 Địa chỉ gợi ý:</p>
				 <ul>
				 <li>Bánh Cống Cô Út Đại Tâm: Ấp Đại Nghĩa, xã Đại Tâm, huyện Mỹ Xuyên, Sóc Trăng</li>
				 <li>Bánh Cống Đại Tâm – Quán Sáu Dung: Xã Đại Tâm, huyện Mỹ Xuyên</li>
				 </ul>
             """},
        {    "id": "hutieu",
             "title": "Hủ Tiếu Mỹ Tho",
             "img": "/static/images/hutieu.jpg",
             "short": "Mỹ Tho nổi với hủ tiếu – sợi dai, nước dùng ngọt thanh, thường ăn sáng ở miền Tây.",
             "desc": """
                 <p>Hủ tiếu Mỹ Tho là món ăn đặc sản nổi tiếng của thành phố Mỹ Tho, tỉnh Tiền Giang, được xem là niềm tự hào ẩm thực của người dân nơi đây.</p>
                 <p>Sợi hủ tiếu: làm từ gạo Gò Cát (một vùng trồng lúa nổi tiếng của Mỹ Tho). Sợi nhỏ, dai, có độ trong và thơm mùi gạo tự nhiên – khác hẳn với các loại hủ tiếu nơi khác.</p>
            	 <p>Nước dùng: được ninh từ xương heo, mực khô, tôm khô trong nhiều giờ, cho vị ngọt thanh, trong veo chứ không béo gắt.</p>
				 <p>📍 Địa chỉ gợi ý:</p>
				 <ul>
				 <li>Hủ Tiếu Mỹ Tho Chín Của: 44 Nam Kỳ Khởi Nghĩa, Phường 1, thành phố Mỹ Tho, Tiền Giang</li>
				 <li>Hủ Tiếu Mỹ Tho Hương Quê: 63 Ấp Bắc, thành phố Mỹ Tho</li>
				 </ul>
			 """},
			{    "id": "nemnuong",
             "title": "Nem Nướng Cần Thơ",
             "img": "/static/images/nemnuong.jpg",
             "short": "Là món ăn biểu tượng của Cần Thơ, từng được vinh danh trong danh sách 100 món ăn ẩm thực Việt Nam tiêu biểu vùng Nam Bộ.",
             "desc": """
                 <p>Nem nướng Cần Thơ là món ăn đặc sản nổi tiếng của vùng Tây Đô, thường được nhắc cùng tên tuổi với nem nướng Ninh Hòa (Khánh Hòa) hay nem nướng Đà Lạt, nhưng lại mang hương vị riêng biệt, đặc trưng của miền Tây Nam Bộ.</p>
                 <p>Thành phần chính: thịt heo nạc xay (thường pha một ít mỡ để không khô), trộn với tỏi, hành, tiêu, nước mắm, đường, sau đó nướng trên than hồng cho chín vàng đều, thơm lừng.</p>
            	 <p>Ăn kèm: bánh hỏi, bánh tráng, bún tươi, rau sống (xà lách, húng quế, tía tô, diếp cá), chuối chát, khế chua, đồ chua (cà rốt, củ cải ngâm giấm).</p>
				 <p>Điểm đặc biệt nhất: là nước chấm sệt (pha từ gan heo, tương hột, đậu phộng xay, nước cốt dừa, tỏi và ớt băm) – béo ngậy, thơm bùi, vị ngọt nhẹ đặc trưng miền Tây.</p>
				 <p>📍 Địa chỉ gợi ý:</p>
				 <ul>
				 <li>Nem Nướng Thanh Vân: 17 Đại lộ Hòa Bình, phường Tân An, quận Ninh Kiều, Cần Thơ</li>
				 <li>Nem Nướng Cái Răng: 45/3 Lý Tự Trọng, phường An Cư, quận Ninh Kiều</li>
				 </ul>
			 """},
			{    "id": "banhxeo",
             "title": "Bánh Xèo Củ Hủ Khóm - Hậu Giang",
             "img": "/static/images/banhxeo.jpg",
             "short": "Đã được công nhận là Mn tiêu bón ăiểu của tỉnh Hậu Giang trong chương trình xác lập 130 món đặc sản vùng ĐBSCL năm 2022.",
             "desc": """
                 <p>Bánh xèo củ hủ khóm là món ăn đặc trưng của vùng Phụng Hiệp – Hậu Giang, nơi nổi tiếng với vùng trồng khóm (dứa) lớn nhất miền Tây.</p>
                 <p>Nguyên liệu chính: bột gạo xay pha nước cốt dừa, nghệ tươi (tạo màu vàng), tôm, thịt ba chỉ, củ hủ khóm, hành lá.</p>
            	 <p>Củ hủ khóm: giòn sần sật, vị ngọt thanh tự nhiên, không gắt, rất “bắt miệng”.</p>
				 <p>Nước chấm: nước mắm chua ngọt pha với tỏi, ớt, chanh – kèm rau sống các loại (rau thơm, lá xoài non, lá cách, diếp cá...).</p>
				 <p>📍 Địa chỉ gợi ý:</p>
				 <ul>
				 <li>Quán Bánh xèo Củ Hủ Khóm Út Mười: Ấp Đông Bình, xã Tân Bình, huyện Phụng Hiệp, Hậu Giang</li>
				 <li>Bánh xèo Sáu Xiện: Khu vực 3, phường 5, thành phố Vị Thanh, tỉnh Hậu Giang</li>
				 </ul>
			 """}, 
			{    "id": "goicatrich",
             "title": "Gỏi Cá Trích - Kiên Giang",
             "img": "/static/images/goicatrich.jpg",
             "short": "Gỏi cá trích Phú Quốc từng được Hiệp hội Du lịch Việt Nam bình chọn là một trong 50 món đặc sản nổi tiếng của Việt Nam.",
             "desc": """
                 <p>Gỏi cá trích là món ăn đặc sản nổi tiếng của Kiên Giang, đặc biệt phổ biến tại đảo Phú Quốc – nơi có nguồn hải sản tươi ngon quanh năm.</p>
                 <p>Nguyên liệu chính: cá trích tươi sống (loại nhỏ, thịt trong, ít tanh), dừa nạo, hành tây, ớt, tỏi, chanh, gừng, rau thơm, đậu phộng rang.</p>
            	 <p>Hương vị: chua nhẹ, béo của dừa, giòn của hành tây, cay của ớt, và ngọt tự nhiên từ cá tươi – tất cả hòa quyện tạo nên vị tươi mát, đậm đà, “ngon khó quên”.</p>
				 <p>📍 Địa chỉ gợi ý:</p>
				 <ul>
				 <li>Nhà hàng Ra Khơi: 131 đường 30/4, thị trấn Dương Đông, Phú Quốc</li>
				 <li>Nhà hàng Trùng Dương Marina: 136 đường 30/4, thị trấn Dương Đông, Phú Quốc</li>
				 </ul>
			 """}
    	],
		"health_list": [
			{"title": "Bệnh viện Đa khoa Trung ương Cần Thơ",
			"decs": """
			<p>Số 315 Nguyễn Văn Linh, Phường An Khánh, Quận Ninh Kiều, Thành phố Cần Thơ</p>
			<p>Liên lạc: 090 1215 115</p>
			"""
			}, {"title": "Bệnh viện Đa khoa tỉnh Hậu Giang",
			"decs": """
			<p>Số 647 Trần Hưng Đạo, Khu vực 4, Phường 3, Thành phố.Vị Thanh, tỉnh Hậu Giang</p>
			<p>Liên lạc: 0293 3876 333</p>
			"""
			}, {"title": "Bệnh viện Đa khoa tỉnh Kiên Giang",
			"decs": """
			<p>Số 13 Nam Kỳ Khởi Nghĩa, Phường An Hoà, Tành phố Rạch Giá, Kiên Giang</p>
			<p>Liên lạc: 0297 3863 328</p>
			"""
			}, {"title": "Bệnh viện Đa khoa tỉnh An Giang",
			"decs": """
			<p>Số 60 Ung Văn Khiêm, Phường Mỹ Phước, Thành phố Long Xuyên, An Giang</p>
			<p>Liên lạc: 0296 3852 989 hoặc 0296 3852 862</p>
			"""
			}, {"title": "Bệnh viện Đa khoa Đồng Tháp",
			"decs": """
			<p>Số 144 Mai Văn Khải, Ấp 3, Xã Mỹ Tân, Thành phố Cao Lãnh, Đồng Tháp</p>
			<p>Liên lạc: 0277 3854 065</p>
			"""
			}, {"title": "Bệnh viện Đa khoa tỉnh Sóc Trăng ",
			"decs": """
			<p>Số 378 đường Lê Duẩn, phường 9, Thành phố Sóc Trăng</p>
			<p>Liên lạc: 0299 3825 251</p>
			"""
			}, {"title": "Bệnh viện Đa khoa tỉnh Vĩnh Long",
			"decs": """
			<p>Số 301 Trần Phú, phường Phước Hậu, tỉnh Vĩnh Long</p>
			<p>Liên lạc: 0207 3823 520 hoặc 0207 3822 523</p>
			"""
			}, {"title": "Bệnh viện Đa khoa tỉnh Trà Vinh",
			"decs": """
			<p>Số 399 Nguyễn Đáng, Phường 7, Thành phố Trà Vinh, Tỉnh Trà Vinh</p>
			<p>Liên lạc: 0294 6251 919</p>
			"""
			}, {"title": "Bệnh viện Nguyễn Đình Chiểu",
			"decs": """
			<p>Số 109 Đoàn Hoàng Minh, Phường 5, Thành phố Bến Tre</p>
			<p>Liên lạc: 0275 3817 555</p>
			"""
			}, {"title": "Bệnh viện Đa khoa tỉnh Trà Vinh",
			"decs": """
			<p>Số 399 Nguyễn Đáng, Phường 7, Thành phố Trà Vinh, Tỉnh Trà Vinh</p>
			<p>Liên lạc: 0294 6251 919</p>
			"""
			}, {"title": "Bệnh viện Đa khoa tỉnh Cà Mau",
			"decs": """
			<p>Số 16 Hải Thượng Lãn Ông, Khóm 6, Phường 6, Thành phố Cà Mau, Tỉnh Cà Mau</p>
			<p>Liên lạc: 0967 731 818</p>
			"""
			}, {"title": "Bệnh viện Đa khoa Bạc Liêu",
			"decs": """
			<p>Số 06 Nguyễn Huệ, Thành phố Bạc Liêu, Tỉnh Bạc Liêu</p>
			<p>Liên lạc: 0291 3822 285</p>
			"""
			}
		]
    },
    "en": {
        "title": "Travel Healing - Mekong Delta",
        "intro": "Explore Southern Vietnam: rivers, cuisine, and unique culture.",
        "menu": {"home": "Home", "about": "About", "tips": "Tips", "checklist": "Check-list", "lang": "Language", "food": "Cuisine", "health": "Medical Support"},
        "about": [
			{"title": "About Us",
			"decs": """
			<p>Thank you for visiting Travel Healing!</p>
			<p>We are here to help you explore the Mekong Delta – a land of gentle rivers, friendly smiles and unforgettable local experiences.</p>
			<p>Our goal is simple: to help you “feel the West – not just visit it.”</p>
			<p>If you have any questions, comments or need travel advice, please do not hesitate to contact us.</p>
			<p>We are a group of students who love travel, culture and storytelling, with the belief that every trip can heal the soul.</p>
			"""},
			{"title": "About the Project",
			"decs": """
			<p>Travel Healing is a student-led project to promote the image of safe and green tourism – close to the community in the Mekong Delta region.</p>
			<p>We wish to:</p>
			<ul>
				<li>Introduce little-known but interesting destinations.</li>
				<li>Connect tourists with local people, homestays and real-life experience tours.</li>
				<li>Spread the message of sustainable tourism, so that every trip is a journey of healing.</li>
			</ul>
			<p>Our message – “Healthy to travel – travel to be healthy” – expresses the belief that travel is not only about discovering new places, but also about finding balance within yourself.</p>
			"""},
			{"title": "Contact Us",
			"decs": """
			<ul>
				<li>Email: dulichkhoe.official@gmail.com</li>
				<li>Phone: 0903 000 ***</li>
				<li>Address: FPT University, Can Tho City, Vietnam</li>
			</ul>
			"""},
			{"title": "Follow Us",
			"decs": """
			<p>Update the latest travel stories, guides and photos at:</p>
			<ul>
				<li>Facebook: fb.com/dulichkhoe</li>
				<li>TikTok: @travelhealing***.official</li>
			</ul>
			"""},
			{"title": "Travel With Us",
			"decs": """
			<p>Do you love the West and want to contribute to spreading positive tourism?</p>
			<p>Please share your story with us, become a collaborator or ambassador of Travel Healing.</p>
			<p>Together, we build a green, real and inspiring travel community.</p>
			"""}
			],
        "places": [
            {"name": "Can Tho", "img": "cantho.jpg",
             "desc": "The capital of the Western region, famous for its floating markets, rich orchards and friendly orchard culture. Experience the morning floating market, enjoy vermicelli soup and fruit on a boat."},
            {"name": "An Giang", "img": "nuicamangiang.jpg",
             "desc": "The land of That Son mountains, Cham - Khmer culture blend, famous for its sacred beauty and peaceful river life."},
            {"name": "Ca Mau", "img": "muicamau.jpg",
             "desc": "Ca Mau is the southernmost province of Vietnam, bordering the sea on three sides, famous for its mangrove ecosystem, lagoons, small islands and the sacred southernmost point of the country. Unspoiled nature, river culture and rich cuisine are the attractions of Ca Mau tourism"},
            {"name": "Vinh Long", "img": "vinhlong.jpg",
             "desc": "Vinh Long is located between the Tien and Hau rivers, the center of the Mekong Delta. This place stands out with its intricate canal system, fruit-laden orchards, and peaceful garden space."},
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
        ], 
			"food_list": [
			{ "id": "banhcong",
			"title": "Banh Cong Soc Trang",
			"img": "/static/images/banhcong.jpg",
			"short": "Banh Cong Dai Tam is a golden yellow cake, fragrant with the smell of rice flour and shrimp, the green bean filling is rich and fatty - a harmonious flavor, you can eat it forever without getting bored.",
			"desc": """
			<p>Banh Cong Dai Tam is a famous specialty of My Xuyen district, Soc Trang province, especially in Dai Tam commune - where many Khmer people live.</p>
			<p>The cake is named after the place "Dai Tam", where the traditional cake making profession has existed for more than half a century.</p>
			<p>"Cong" is a cylindrical tool (like a small cup) - poured with flour and filling, then dipped in a pan of hot oil until golden brown.</p>
			<p>📍 Suggested address meaning:</p>
			<ul>
				<li>Banh Cong Co Ut Dai Tam: Ap Dai Nghia, Dai Tam Commune, My Xuyen District, Soc Trang</li>
				<li>Banh Cong Dai Tam – Quan Sau Dung: Commune Dai Tam, My Xuyen District</li>
			</ul>
			"""},
			{ "id": "hutieu",
			"title": "Hu Tieu My Tho",
			"img": "/static/images/hutieu.jpg",
			"short": "My Tho is famous for hu tieu - chewy noodles, sweet broth, often eaten for breakfast in the West.",
			"desc": """
			<p>Hu Tieu My Tho is a famous specialty dish of My Tho city, Tien Giang province, considered the culinary pride of the people here.</p>
			<p>Hu Tieu noodles: made from Go Cat rice (a famous rice growing area of ​​My Tho). Small, chewy noodles, clear and fragrant with natural rice aroma - different different from other types of noodles.</p>
			<p>Broth: simmered from pork bones, dried squid, dried shrimp for many hours, giving a sweet, clear taste, not too fatty.</p>
			<p>📍 Suggested address:</p>
			<ul>
				<li>My Tho Chin Cua Noodles: 44 Nam Ky Khoi Nghia, Ward 1, My Tho City, Tien Giang</li>
				<li>My Tho Huong Que Noodles: 63 Ap Bac, My Tho City</li>
			</ul>
			"""},
			{ "id": "nemnuong",
			"title": "Nem Nuong Can Tho",
			"img": "/static/images/nemnuong.jpg",
			"short": "Is a symbolic dish of Can Tho, once honored in the list of 100 typical Vietnamese culinary dishes of the Southern region.",
			"desc": """
			<p>Nem Nuong Can Tho is A famous specialty dish of the Western region, often mentioned with the same name as Nem Nuong Ninh Hoa (Khanh Hoa) or Nem Nuong Da Lat, but with a unique flavor, typical of the Southwest region.</p>
			<p>Main ingredients: ground lean pork (usually mixed with a little fat to avoid dryness), mixed with garlic, onion, pepper, fish sauce, sugar, then grilled over hot coals until golden brown and fragrant.</p>
			<p>Accompaniments: rice vermicelli, rice paper, fresh vermicelli, raw vegetables (lettuce, basil, perilla, fish mint), green banana, sour star fruit, pickles (carrots, pickled radishes).</p>
			<p>The most special point: the thick dipping sauce (mixed from pork liver, soy sauce, ground peanuts, coconut milk, garlic and chopped chili) - fatty, fragrant, slightly sweet, typical of the West.</p>
			<p>📍 Suggested address:</p>
			<ul>
				<li>Thanh Van Grilled Spring Rolls: 17 Hoa Binh Avenue, Tan An Ward, Ninh Kieu District, Can Tho</li>
				<li>Cai Rang Grilled Spring Rolls: 45/3 Ly Tu Trong, An Cu Ward, Ninh Kieu District</li>
			</ul>
			"""},
			{ "id": "banhxeo",
			"title": "Banh Xeo Cu Hu Khom - Hau Giang",
			"img": "/static/images/banhxeo.jpg",
			"short": "Recognized as A typical dish of Hau Giang province in the program to establish 130 specialties of the Mekong Delta in 2022.",
			"desc": """
			<p>Banh Xeo Cu Hu Khom is a typical dish of Phung Hiep - Hau Giang region, famous for the largest pineapple growing area in the West.</p>
			<p>Main ingredients: ground rice flour mixed with coconut milk, fresh turmeric (to create yellow color), shrimp, pork belly, pineapple root, green onion.</p>
			<p>Pomelo root: crunchy, natural sweetness, not harsh, very "appetizing".</p>
			<p>Dipping sauce: sweet and sour fish sauce mixed with garlic, chili, lemon - with various raw vegetables (herbs, young mango leaves, cassia leaves, fish mint...).</p>
			<p>📍 Suggested address:</p>
			<ul>		
				<li>Ut Muoi Cu Hu Khom Banh Xeo Restaurant: Dong Binh Hamlet, Tan Binh Commune, Phung Hiep District, Hau Giang</li>
				<li>Sau Xien Banh Xeo: Area 3, Ward 5, Vi Thanh City, Hau Giang Province</li>
			</ul>
			"""},
			{ "id": "goicatrich",
			"title": "Gỏi Cá Herring - Kien Giang",
			"img": "/static/images/goicatrich.jpg",
			"short": "Phu Quoc herring salad was once voted by the Vietnam Tourism Association as one of the 50 famous specialties of Vietnam.",
			"desc": """
			<p>Herring salad is a famous specialty dish of Kien Giang, especially popular on Phu Quoc Island - where there is a source of fresh seafood all year round.</p>
			<p>Main ingredients: fresh herring (small, clear meat, less fishy smell), grated coconut, onion, chili, garlic, lemon, ginger, herbs, roasted peanuts.</p>
			<p>Taste: mild sourness, fatty coconut, crunchy onion, spicy chili, and natural sweetness from fresh fish - all blend together to create a fresh, rich, "unforgettable" taste.</p>
			<p>📍 Suggested address:</p>
			<ul>
				<li>Ra Khoi Restaurant: 131 30/4 Street, Duong Dong Town, Phu Quoc</li>
				<li>Truong Duong Marina Restaurant: 136 30/4 Street, Duong Dong Town, Phu Quoc</li>
			</ul>
			"""}
			],
		"health_list": [
			{"title": "Can Tho Central General Hospital",
			"decs": """
			<p>No. 315 Nguyen Van Linh, An Khanh Ward, Ninh Kieu District, Can Tho City</p>
			<p>Contact: 090 1215 115</p>
			"""
			}, {"title": "Hau Giang Provincial General Hospital",
			"decs": """
			<p>No. 647 Tran Hung Dao, Zone 4, Ward 3, Vi Thanh City, Hau Giang Province</p>
			<p>Contact: 0293 3876 333</p>
			"""
			}, {"title": "Kien Giang Provincial General Hospital",
			"decs": """
			<p>No. 13 Nam Ky Khoi Nghia, An Hoa Ward, Rach Gia City, Kien Giang Giang</p>
			<p>Contact: 0297 3863 328</p>
			"""
			}, {"title": "An Giang Provincial General Hospital",
			"decs": """
			<p>No. 60 Ung Van Khiem, My Phuoc Ward, Long Xuyen City, An Giang</p>
			<p>Contact: 0296 3852 989 or 0296 3852 862</p>
			"""
			}, {"title": "Dong Thap General Hospital",
			"decs": """
			<p>No. 144 Mai Van Khai, Hamlet 3, My Tan Commune, Cao Lanh City, Dong Thap</p>
			<p>Contact: 0277 3854 065</p>
			"""
			}, {"title": "General Hospital Soc Trang province ",
			"decs": """
			<p>No. 378 Le Duan Street, Ward 9, Soc Trang City</p>
			<p>Contact: 0299 ​​3825 251</p>
			"""
			}, {"title": "Vinh Long Provincial General Hospital",
			"decs": """
			<p>No. 301 Tran Phu, Phuoc Hau Ward, Vinh Long Province</p>
			<p>Contact: 0207 3823 520 or 0207 3822 523</p>
			"""
			}, {"title": "Tra Vinh Provincial General Hospital",
			"decs": """
			<p>No. 399 Nguyen Dang, Ward 7, Tra Vinh City, Tra Vinh Province</p>
			<p>Contact: 0294 6251 919</p>
			"""
			}, {"title": "Nguyen Dinh Chieu Hospital",
			"decs": """
			<p>No. 109 Doan Hoang Minh, Ward 5, Ben Tre City</p>
			<p>Contact: 0275 3817 555</p>
			"""
			}, {"title": "Tra Vinh Provincial General Hospital",
			"decs": """
			<p>No. 399 Nguyen Dang, Ward 7, Tra Vinh City, Tra Vinh Province</p>
			<p>Contact: 0294 6251 919</p>
			"""
			}, {"title": "Ca Mau Provincial General Hospital",
			"decs": """
			<p>No. 16 Hai Thuong Lan Ong, Hamlet 6, Ward 6, Ca Mau City, Ca Mau Province</p>
			<p>Contact: 0967 731 818</p>
			"""
			}, {"title": "Bac Lieu General Hospital",
			"decs": """
			<p>No. 06 Nguyen Hue, Bac Lieu City, Bac Lieu Province</p>
			<p>Contact: 0291 3822 285</p>
			"""
			}
		]
    },
    "kr": {
        "title": "Travel Healing - Mekong Delta",
        "intro": "남부 베트남 탐험: 강, 음식, 독특한 문화.",
        "menu": {"home": "홈", "about": "소개", "tips": "유의사항", "checklist": "체크리스트", "lang": "언어", "food": "음식", "health": "의료 지원"},
        "about": [
			{"title": "회사 소개",
			"decs": """
			<p>Travel Healing을 방문해 주셔서 감사합니다!</p>
			<p>잔잔한 강물, 친절한 미소, 잊지 못할 현지 경험으로 가득한 메콩 델타를 탐험하실 수 있도록 도와드리겠습니다.</p>
			<p>저희의 목표는 간단합니다. 바로 "단순히 방문하는 것이 아니라, 서부를 직접 느껴보세요."입니다.</p>
			<p>질문, 의견 또는 여행 관련 조언이 필요하시면 언제든지 문의해 주세요.</p>
			<p>저희는 여행, 문화, 스토리텔링을 사랑하는 학생들로 구성되어 있으며, 모든 여행이 영혼을 치유할 수 있다고 믿습니다.</p>
			"""},
			{"title": "프로젝트 소개",
			"decs": """	
			<p>Travel Healing은 메콩 델타 지역 사회와 가까운 곳에서 안전하고 친환경적인 관광의 이미지를 홍보하기 위한 학생 주도 프로젝트입니다.</p>
			<p>저희는 받는 사람:</p>
			<ul>
				<li>잘 알려지지 않았지만 흥미로운 여행지를 소개합니다.</li>
				<li>관광객을 지역 주민, 홈스테이, 그리고 실제 체험 투어와 연결해 드립니다.</li>
				<li>지속 가능한 관광의 메시지를 전파하여 모든 여행이 치유의 여정이 되도록 하세요.</li>
			</ul>
			<p>저희의 메시지인 "건강한 여행 - 건강한 여행을 위한 여행"은 여행이 새로운 장소를 발견하는 것뿐만 아니라 내면의 균형을 찾는 것이라는 믿음을 담고 있습니다.</p>
			"""},
			{"title": "문의하기",
			"decs": """
			<ul>
				<li>이메일: dulichkhoe.official@gmail.com</li>
				<li>전화: 0903 000 ***</li>
				<li>주소: 베트남 깐토시 FPT 대학교</li>
			</ul>
			"""},
			{"title": "팔로우 Us",
			"decs": """
			<p>최신 여행 이야기, 가이드, 사진을 다음 링크에서 확인하세요:</p>
			<ul>
				<li>Facebook: fb.com/dulichkhoe</li>
				<li>TikTok: @travelhealing***.official</li>
			</ul>
			"""},
			{"title": "저희와 함께 여행하세요",
			"decs": """
			<p>서부 지역을 좋아하시고 긍정적인 관광을 확산하는 데 기여하고 싶으신가요?</p>
			<p>저희와 함께 여러분의 이야기를 공유하고 Travel Healing의 협력자 또는 홍보대사가 되어 주세요.</p>
			<p>우리는 함께 친환경적이고, 진정성 있고, 영감을 주는 여행 커뮤니티를 만들어 나갑니다.</p>
			"""}
		],
        "places": [
            {"name": "Can Tho", "img": "cantho.jpg",
             "desc": "서부 지역의 수도로, 수상 시장, 풍성한 과수원, 그리고 정겨운 과수원 문화로 유명합니다. 아침 수상 시장을 경험하고, 배 위에서 당면 수프와 과일을 즐겨보세요."},
            {"name": "An Giang", "img": "nuicamangiang.jpg",
             "desc": "타트썬 산맥의 땅, 참족과 크메르족 문화가 혼합되어 있으며, 신성한 아름다움과 평화로운 강 생활로 유명합니다."},
            {"name": "Ca Mau", "img": "muicamau.jpg",
             "desc": "까마우는 베트남 최남단 성으로, 삼면이 바다에 접해 있으며, 맹그로브 생태계, 석호, 작은 섬들, 그리고 베트남 최남단의 성지로 유명합니다. 훼손되지 않은 자연, 강 문화, 그리고 풍부한 음식은 까마우 관광의 매력입니다."},
            {"name": "Vinh Long", "img": "vinhlong.jpg",
             "desc": "빈롱은 티엔 강과 허우 강 사이에 위치하며, 메콩 삼각주의 중심지입니다. 이곳은 정교한 운하 시스템, 과일이 가득한 과수원, 그리고 평화로운 정원으로 유명합니다."},
            {"name": "Dong Thap", "img": "dongthap.jpg",
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
        ], 
		"food_list": [
			{ "id": "banhcong",
			"title": "반꽁속짱",
			"img": "/static/images/banhcong.jpg",
			"short": "반꽁다이땀은 쌀가루와 새우 향이 가득한 황금빛 케이크입니다. 풋콩 속은 풍부하고 기름진 맛이 조화롭게 어우러져 질리지 않고 계속 먹을 수 있습니다.",
			"desc": """
			<p>반꽁다이땀은 속짱성 미쑤옌현, 특히 다이땀 마을의 유명한 특산품으로, 많은 크메르족이 거주합니다.</p>
			<p>이 케이크는 반세기 이상 전통 케이크 제조가 이어져 온 "다이땀" 지역의 이름을 따서 명명되었습니다.</p>
			<p>"콩"은 작은 컵처럼 생긴 원통형 도구로, 밀가루와 속을 채워 팬에 담가 굽습니다. 뜨거운 기름에 황금빛 갈색이 될 때까지 볶습니다.</p>
			<p>📍 추천 주소 의미:</p>
			<ul>
				<li>반꽁꼬웃다이땀: 속짱, 미쑤옌군, 다이땀사(Ap Dai Nghia), 압다이응이아</li>
				<li>반꽁다이땀 - 꽌사우중: 미쑤옌군, 다이땀사(Comune Dai Tam), 미쑤옌군</li>
			</ul>
			"""},
			{ "id": "hutieu",
			"title": "후띠에우미토",
			"img": "/static/images/hutieu.jpg",
			"short": "미토는 후띠에우(hu tieu)로 유명합니다. 후띠에우란 쫄깃한 국수와 달콤한 국물로, 서양에서는 아침 식사로 자주 먹습니다.",
			"desc": """
			<p>후띠에우미토는 띠엔장성, 미토시의 유명한 특선 요리로, 지역 주민들의 미식 자부심으로 여겨집니다. 여기.</p>
			<p>후띠에우 국수: 미토의 유명한 쌀 생산지인 고깟 쌀로 만듭니다. 작고 쫄깃한 면발에 쌀 고유의 향이 은은하게 풍겨 나와 다른 종류의 국수와는 차별화됩니다.</p>
			<p>육수: 돼지뼈, 마른 오징어, 마른 새우를 오랜 시간 끓여 달콤하고 맑은 맛을 내며, 너무 짜지 않습니다.</p>
			<p>📍 추천 주소:</p>
			<ul>
				<li>미토 친꾸아 국수: 띠엔장성 미토시 1구 남끼코이응이아 44번지</li>
				<li>미토 흐엉꾸에 국수: 미토시 압박 63번지</li>
			</ul>
			"""},
			{ "id": "nemnuong",
			"title": "넴느엉깐토",
			"img": "/static/images/nemnuong.jpg",
			"short": "베트남 남부 100대 요리에 선정된 적이 있는 깐토의 상징적인 음식입니다.",
			"desc": """
			<p>넴 느엉 깐토는 서부 지역의 유명한 특선 요리로, 넴 느엉 닌호아(칸 호아) 또는 넴 느엉 달랏과 같은 이름으로 자주 언급되지만, 남서부 지역의 독특한 풍미를 자랑합니다.</p>
			<p>주재료: 다진 살코기(보통 건조함을 방지하기 위해 약간의 지방을 섞음)에 마늘, 양파, 후추, 피시 소스, 설탕을 넣고 뜨거운 숯불에 노릇노릇하고 향긋해질 때까지 굽습니다.</p>
			<p>곁들임: 쌀국수, 쌀 종이, 생국수, 생채소(상추, 바질, 들깨, 피시 민트), 풋바나나, 신맛이 나는 스타프루트, 피클(당근, 절인 무).</p>
			<p>가장 특별한 포인트: 돼지 간, 간장, 땅콩 가루, 코코넛 밀크, 마늘, 다진 고추를 섞어 만든 진한 디핑 소스는 기름지고 향긋하며 은은한 단맛이 나는 서양식 맛입니다.</p>
			<p>📍 추천 주소:</p>
			<ul>
				<li>탄반 구이 스프링롤: 깐토 닌끼우 군 떤안 구 호아빈 거리 17번지</li>
				<li>까이랑 구이 스프링롤: 닌끼우 군 안꾸 구 리뚜쫑 45/3번지</li>
			</ul>
			"""},
			{ "id": "banhxeo",
			"title": "하우장 반쎄오 꾸후콤 - 하우장",
			"img": "/static/images/banhxeo.jpg",
			"short": "하우장의 대표적인 요리로 알려져 있습니다. 2022년 메콩 삼각주 130개 특산품 개발 프로그램에 장성이 선정되었습니다.",
			"desc": """
			<p>반쎄오 꾸후콤(Banh Xeo Cu Hu Khom)은 서부 최대 파인애플 재배지로 유명한 풍히엡-하우장 지역의 대표적인 요리입니다.</p>
			<p>주재료: 코코넛 밀크를 섞은 쌀가루, 신선한 강황(노란색을 내기 위해), 새우, 돼지고기 삼겹살, 파인애플 뿌리, 파.</p>
			<p>포멜로 뿌리: 아삭하고 자연스러운 단맛으로 자극적이지 않아 매우 "맛있습니다".</p>
			<p>소스: 마늘, 고추, 레몬을 섞은 새콤달콤한 생선 소스와 다양한 생야채(허브, 어린 망고 잎, 계피 잎, 피시 민트 등)를 곁들임.</p>
			<p>📍 추천 주소:</p>
			<ul>
				<li>웃 무오이 꾸후콤 반쎄오 레스토랑: 동빈 마을 하우장성 풍히엡군 떤빈마을</li>
				<li>사우시엔반쎄오: 하우장성 비탄시 5동 3구역</li>
			</ul>
			"""},
			{ "id": "goicatrich",
			"title": "끼엔장성 고이까 청어",
			"img": "/static/images/goicatrich.jpg",
			"short": "푸꾸옥 청어 샐러드는 베트남 관광협회에서 베트남 50대 특산품 중 하나로 선정한 적이 있습니다.",
			"desc": """
			<p>청어 샐러드는 끼엔장의 유명한 특산 요리로, 특히 일년 내내 신선한 해산물을 맛볼 수 있는 푸꾸옥 섬에서 인기가 높습니다.</p>
			<p>주요 재료: 신선한 청어(작고 살이 투명하며 비린내가 적음), 코코넛 가루, 양파, 고추, 마늘, 레몬 생강, 허브, 구운 땅콩.</p>
			<p>맛: 은은한 신맛, 탱글탱글한 코코넛, 아삭한 양파, 매콤한 고추, 그리고 신선한 생선의 자연스러운 단맛이 어우러져 신선하고 풍부하며 "잊을 수 없는" 맛을 선사합니다.</p>
			<p>📍 추천 주소:</p>
			<ul>
				<li>라 코이 레스토랑: 푸꾸옥 즈엉 동 타운, 30/4번가 131번지</li>
				<li>트엉 즈엉 마리나 레스토랑: 푸꾸옥 즈엉 동 타운, 30/4번가 136번지</li>
			</ul>
			"""}
			],
			"health_list": [
			{"title": "Can Tho 중앙 종합병원",
			"decs": """
			<p>아니요. 315 Nguyen Van Linh, An Khanh Ward, Ninh Kieu District, Can Tho City</p>
			<p>연락처: 090 1215 115</p>
			"""
			}, {"title": "하우장성 종합병원",
			"decs": """
			<p>아니요. 647 Tran Hung Dao, Zone 4, Ward 3, Vi Thanh City, Hau Giang Province</p>
			<p>연락처: 0293 3876 333</p>
			"""
			}, {"title": "끼엔장성 종합병원",
			"decs": """
			<p>연락처: 0297 3863 328</p>
			"""
			}, {"title": "안장성 종합병원",
			"decs": """
			<p>아니요. 60 Ung Van Khiem, My Phuoc Ward, Long Xuyen City, An Giang</p>
			<p>연락처: 0296 3852 989 또는 0296 3852 862</p>
			"""
			}, {"title": "동탑 종합병원",
			"decs": """
			<p>아니요. 144 Mai Van Khai, Hamlet 3, My Tan Commune, Cao Lanh City, Dong Thap</p>
			<p>연락처: 0277 3854 065</p>
			"""
			}, {"title": "속짱성 종합병원",
			"decs": """
			<p>속짱시 9구, 레주안 거리 378번지</p>
			<p>연락처: 0299 ​​​​3825 251</p>
			"""
			}, {"title": "빈롱성 종합병원",
			"decs": """
			<p>빈롱성 푸옥하우구 쩐푸 301번지</p>
			<p>연락처: 0207 3823 520 또는 0207 3822 523</p>
			"""
			}, {"title": "짜빈성 종합병원",
			"decs": """
			<p>응우옌당 399번지, 병동 7, 짜빈성, 짜빈시</p>
			<p>연락처: 0294 6251 919</p>
			"""
			}, {"title": "응우옌딘찌에우 병원",
			"decs": """
			<p>벤째시 5병동, 도안황민 109번지</p>
			<p>연락처: 0275 3817 555</p>
			"""
			}, {"title": "짜빈성 종합병원",
			"decs": """
			<p>짜빈성, 짜빈시 7병동, 응우옌당 399번지</p>
			<p>연락처: 0294 6251 919</p>
			"""
			}, {"title": "까마우성 종합병원",
			"decs": """
			<p>까마우성 까마우시 6구 6번 마을 하이트엉란옹 16번지</p>
			<p>연락처: 0967 731 818</p>
			"""
			}, {"title": "박리에우 종합병원",
			"decs": """
			<p>박리에우성 박리에우시 응우옌 후에 6번지</p>
			<p>연락처: 0291 3822 285</p>
			"""
			}
		]
    }
}
place_details_data = {
    "vi": {
        "Can Tho": [
        {   "title": "Bến Ninh Kiều – Biểu Tượng Thành Phố", 
            "slug": "ben-ninh-kieu",
            "lat": 10.035,
            "lng": 105.788,
            "img": "benninhkieu.jpg",
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
            "slug": "cho-cai-",
            "lat": 10.012,
            "lng": 105.742,
            "img": "chocairang.jpg",
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
                "slug": "chua-doi",
                "lat": 9.603,
                "lng": 105.973,
                "img": "chuadoi.jpg",
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
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
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
        "Ca Mau": [
            {   "title": "Mũi Cà Mau – Cột mốc cực Nam", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
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
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
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
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
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
        "Vinh Long": [
			{   "title": "Nhà cổ Cai Cường – di tích kiến trúc kiểu Pháp", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
                "desc": """ 
                <p>Nhà cổ Cai Cường là một trong những công trình kiến trúc cổ tiêu biểu ở miền Tây Nam Bộ, tọa lạc trên cù lao An Bình – vùng đất nổi tiếng với vẻ đẹp miệt vườn sông nước.</p>
                <p>📍Vị trí: Số 38, ấp Bình Hòa, xã Bình Hòa Phước, huyện Long Hồ, tỉnh Vĩnh Long.</p>
                <img src="/static/images/caicuong.jpg" class="detail-img" alt="Nhà cổ Cai Cường – di tích kiến trúc kiểu Pháp">
				<p>Lịch sử & kiến trúc:</p>
                <ul>
                    <li>Ngôi nhà được xây dựng vào năm 1885 do gia đình ông Phạm Văn Bổn (còn gọi là “Cai Cường”) – một đại địa chủ miệt vườn – khởi công.</li>
                    <li>Kiến trúc đặc biệt: xây theo hình chữ “Đinh” gồm hai nếp nhà vuông góc, mặt chính quay hướng Bắc nhìn ra rạch Cái Muối.</li>
                    <li>Sự kết hợp kiến trúc Đông – Tây: ngoại thất mang hơi hướng phương Tây (Pháp) còn nội thất gỗ lim, mái ngói âm dương, mái vảy cá… đậm phong cách Việt Nam.</li>
                </ul>					
				<img src="/static/images/caicuong1.jpg" class="detail-img" alt="Nhà cổ Cai Cường – Nội thất">
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Không chỉ là một di sản vật chất, nhà cổ Cai Cường còn phản ánh đời sống, văn hóa và phong thái của người Nam Bộ cuối thế kỷ XIX.</li>
                    <li>Giữ được gần như nguyên vẹn các chi tiết gỗ lim, gạch men, hoa văn, mái ngói âm dương hơn trăm năm tuổi.</li>
                    <li>Là điểm du lịch văn hóa – sinh thái đặc sắc khi kết hợp tham quan cùng vườn trái cây, trải nghiệm đời sống miệt vườn.</li>
                </ul>
                <p>Gợi ý:</p>
                <ul>
                    <li>Mặc dù không tìm được thông tin rất rõ ràng về giờ mở cửa chính xác, nhưng có ghi: phà An Bình hoạt động từ 4 giờ sáng đến 22 giờ tối.</li>
                    <li>Khi tham quan, nên giữ gìn nguyên vẹn nội thất, không tự ý di chuyển vật dụng cổ để giữ bản chất ngôi nhà.</li>
                    <li>Nên tới vào sáng sớm hoặc chiều muộn để tránh nắng gắt và ánh sáng đẹp cho chụp ảnh.</li>
                </ul>
                """},
			{   "title": "Văn Thánh Miếu Vĩnh Long", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
                "desc": """ 
                <p>Văn Thánh Miếu Vĩnh Long được xem là “Quốc Tử Giám của Nam Bộ”. Đây là nơi thờ Khổng Tử và các bậc hiền triết Nho giáo, đồng thời là trung tâm giáo dục và sinh hoạt văn hóa của người dân Nam Kỳ xưa.</p>
                <p>📍Vị trí: Tọa lạc tại đường Trần Phú, phường 4, thành phố Vĩnh Long, tỉnh Vĩnh Long.</p>
                <img src="/static/images/vanmieu.jpg" class="detail-img" alt="Văn Thánh Miếu Vĩnh Long">
				<p>Lịch sử & kiến trúc:</p>
                <ul>
                    <li>Được xây dựng trong khoảng năm 1864-1866 dưới thời triều Phan Thanh Giản và ông Nguyễn Thông (Đốc học) khởi xướng.</li>
                    <li>Là một trong ba “Văn Thánh Miếu” tại vùng Nam Bộ, và được xem như “Quốc Tử Giám ở phương Nam”.</li>
                    <li>Kiến trúc: cổng tam quan ba tầng mái cong, hai bên đường vào là hàng cây sao cao – tạo không gian uy nghiêm, tĩnh lặng.</li>
                </ul>
                <img src="/static/images/vanmieu1.jpg" class="detail-img" alt="Văn Thánh Miếu Vĩnh Long - bên trong">
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Di tích lịch sử – văn hóa cấp quốc gia.</li>
                    <li>Hằng năm tổ chức Lễ hội Văn Thánh Miếu (rằm tháng Hai âm lịch) thu hút đông đảo khách thập phương.</li>
                    <li>Là nơi lưu giữ giá trị văn hóa, tinh thần hiếu học và truyền thống tôn sư trọng đạo của người Việt.</li>
                </ul>
                <p>Gợi ý:</p>
                <ul>
                    <li>Giờ mở cửa: Từ khoảng 07:00 sáng đến 17:00 chiều hàng ngày.</li>
                    <li>Vì là nơi thờ phụng + di tích lịch sử, nên khi tham quan hãy giữ trật tự, mặc trang phục phù hợp.</li>
                    <li>Có thể kết hợp tham quan với dạo bộ quanh khu vực sông Long Hồ, thư giãn và chụp ảnh.</li>
                </ul>
                """},
            {   "title": "Chùa Âng: Angkorajaborey (Trà Vinh cũ)", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
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
                """}, 
			{	"title": "Khu di tích Đồng Khởi (Bến Tre)", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
                "desc": """ 
                <p>Khu di tích Đồng Khởi tại Bến Tre là nơi ghi dấu phong trào Đồng Khởi lịch sử năm 1960, biểu tượng cho tinh thần bất khuất, kiên cường của người dân miền Nam trong công cuộc đấu tranh giành độc lập dân tộc. Khu di tích không chỉ có giá trị lịch sử to lớn mà còn là điểm đến giáo dục truyền thống cách mạng cho các thế hệ hôm nay.</p>
                <p>📍Vị trí: Xã Định Thủy, huyện Mỏ Cày Nam, tỉnh Bến Tre.</p>
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Là nơi bùng nổ phong trào Đồng Khởi năm 1960, khởi đầu cho cao trào cách mạng miền Nam.</li>
                    <li>Khu di tích gồm tượng đài Đồng Khởi, nhà trưng bày hiện vật, khu tưởng niệm anh hùng liệt sĩ, và không gian tái hiện lịch sử.</li>
                    <li>Là điểm đến thường được các đoàn học sinh, sinh viên, cựu chiến binh viếng thăm.</li>
                </ul>                
				<img src="/static/images/dongkhoi.jpg" class="detail-img" alt="Khu di tích Đồng Khởi">
                <p>Gợi ý:</p>
                <ul>
                    <li>Thích hợp cho những ai yêu thích lịch sử – truyền thống cách mạng.</li>
                    <li>Có thể đi theo đoàn hoặc tour học tập thực tế.</li>
                    <li>Sau khi tham quan, có thể ghé chợ Bến Tre mua đặc sản như kẹo dừa, bánh tráng sữa.</li>
                </ul>
                """}
                ],
        "Dong Thap": [
            {   "title": "Đồng Sen Tháp Mười", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg", 
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
        {		"title": "Làng Hoa Sa Đéc", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
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
                """},
			{	"title": "Cù lao Thới Sơn (Cồn Lân)", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
                "desc": """ 
                <p>Cù Lao Thới Sơn nằm giữa dòng sông Tiền hiền hòa, là điểm du lịch sinh thái nổi tiếng với vườn cây trái xanh tươi, những con rạch nhỏ len lỏi và hoạt động du lịch cộng đồng hấp dẫn như đi xuồng ba lá, nghe đờn ca tài tử, thưởng thức đặc sản miệt vườn.</p>
                <p>📍Vị trí: Nằm giữa sông Tiền, Xã Thới Sơn, thành phố Mỹ Tho, tỉnh Tiền Giang.</p>
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Là cồn lớn và xanh mát, nổi tiếng với vườn cây ăn trái, nhà vườn, làng nghề truyền thống (làm kẹo dừa, mật ong, đan lát…).</li>
                    <li>Du khách có thể đi xuồng ba lá trên rạch nhỏ, nghe đờn ca tài tử, thưởng thức trái cây miệt vườn, và ăn trưa trong không gian dân dã.</li>
                    <li>Đây là điểm du lịch sinh thái – cộng đồng tiêu biểu, mang đậm nét miền Tây sông nước.</li>
                </ul>                
				<img src="/static/images/thoison.jpg" class="detail-img" alt="Cù Lao Thới Sơn">
                <p>Gợi ý:</p>
                <ul>
                    <li>Nên đi buổi sáng sớm để tránh nắng và tận hưởng không khí mát lành.</li>
                    <li>Mặc quần áo nhẹ, giày dép dễ di chuyển vì có nhiều đoạn đi xuồng, đi bộ.</li>
                    <li>Thử đờn ca tài tử, ăn cá tai tượng chiên xù và uống mật ong tươi – đặc sản nơi đây.</li>
                </ul>
                """},
			{		"title": "Chùa Vĩnh Tràng (Tiền Giang)", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
                "desc": """ 
                <p>Chùa Vĩnh Tràng – ngôi chùa cổ kính và lớn nhất Tiền Giang – mang trong mình nét kiến trúc độc đáo giao hòa giữa Á và Âu. Với không gian thanh tịnh, vườn cây xanh mát cùng những tượng Phật uy nghi, chùa là điểm dừng chân lý tưởng cho những ai muốn tìm lại sự bình yên và chiêm ngưỡng tinh hoa nghệ thuật kiến trúc.</p>
                <p>📍Vị trí: Số 66 Nguyễn Trung Trực, phường 8, thành phố Mỹ Tho.</p>
                <img src="/static/images/chuavinhtrang.jpg" class="detail-img" alt="Chùa Vĩnh Tràng">
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Là ngôi chùa cổ và lớn nhất Tiền Giang, được xây dựng từ thế kỷ XIX.</li>
                    <li>Kiến trúc kết hợp hài hòa giữa Á – Âu (Pháp, La Mã, Thái, Miên, Nhật), tạo nên vẻ độc đáo hiếm có.</li>
                    <li>Trong khuôn viên có tượng Phật Di Lặc khổng lồ, tượng A Di Đà nằm, vườn cảnh thoáng đãng và thanh tịnh.</li>
                </ul>
				<img src="/static/images/chuavinhtrang1.jpg" class="detail-img" alt="Chùa Vĩnh Tràng 1">
                <p>Gợi ý:</p>
                <ul>
                    <li>TĂn mặc lịch sự, kín đáo, giữ trật tự nơi tôn nghiêm.</li>
                    <li>Chụp ảnh ở khu tượng Phật Di Lặc và vườn chùa rất đẹp.</li>
                    <li>Nên kết hợp tham quan cùng Cù Lao Thới Sơn trong cùng một buổi.</li>
                </ul>
                """}
        ], "An Giang": [
            {   "title": "Núi Cấm (Thiên Cấm Sơn) – “Nóc nhà miền Tây”", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
                "desc": """ 
                <p>Đỉnh núi cao nhất nhất vùng Đồng bằng sông Cửu Long, khí hậu mát mẻ quanh năm,cảnh quan thiên nhiên khá đa dạng .Mang đậm yếu tố tâm linh, lịch sử và truyền thuyết, thường được ví như “nóc nhà miền Tây.</p>
                <p>📍Vị trí: Xã An Hảo, huyện Tịnh Biên,tỉnh An Giang.</p>
                <img src="/static/images/nuicamangiang.jpg" class="detail-img" alt="Núi Cấm (Thiên Cấm Sơn) – “Nóc nhà miền Tây”">
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Tượng Phật Di Lặc cao 33,6m – biểu tượng Núi Cấm,một trong những tượng Phật Di Lặc lớn nhất Việt Nam.</li>
                    <li>Hồ Thủy Liêm với mặt nước phẳng lặng soi bóng núi non, cùng các công trình tâm linh như Chùa Vạn Linh và Chùa Phật Lớn thu hút đông đảo khách hành hương.</li>
                    <li>Trải nghiệm Cáp treo Núi Cấm để ngắm nhìn toàn cảnh Thất Sơn hùng vĩ từ trên cao, cảm nhận trọn vẹn vẻ đẹp thiên nhiên kỳ vĩ của vùng Bảy Núi.</li>
                </ul>
                <p>Gợi ý:</p>
                <ul>
                    <li>⏰ Thời gian tham quan: cả ngày từ 6h00 – 18h00.</li>
                    <li>Vé cáp treo: trên 180.000đ/người.</li>
                    <li>Nên đi buổi sáng sớm để tránh nắng, mang giày thể thao, Nếu trekking chọn mùa khô.</li>
                </ul>
                """},
			{   "title": "Rừng Tràm Trà Sư – Thiên đường mùa nước nổi", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
                "desc": """ 
                <p>Thiên đường xanh với bèo phủ mặt nước tuyệt đẹp nơi sống của hàng trăm loài chim quý.</p>
                <p>📍Vị trí: Xã Văn Giáo, huyện Tịnh Biên, cách Châu Đốc khoảng 30 km.</p>
                <img src="/static/images/rungtram.jpg" class="detail-img" alt="Rừng Tràm Trà Sư – Thiên đường mùa nước nổi">
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Hơn 140 loài thực vật, 70+ loài chim (có loài quý hiếm trong Sách Đỏ).</li>
                    <li>Đi xuồng, ghe hoặc chèo thuyền giữa rừng bèo xanh. Check-in cầu tre dài nhất Việt Nam.</li>
                    <li>Khu bảo tồn đa dạng sinh học, điều hòa môi trường, được mệnh danh là “rừng tràm đẹp nhất Việt Nam”</li>
                </ul>
				<img src="/static/images/rungtram1.jpg" class="detail-img" alt="Rừng Tràm Trà Sư – Các loài Chim">
                <p>Gợi ý:</p>
                <ul>
                    <li>Cảnh quan đẹp nhất: Mùa nước nổi (tháng 9–11), đặc biệt lúc bình minh hoặc hoàng hôn.</li>
                    <li>Đi buổi sáng hoặc chiều muộn; mang máy ảnh, ống nhòm, và giày đế mềm để dễ di chuyển.</li>
                </ul>
                """},
			{   "title": "Phú Quốc – Đảo Ngọc", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
                "desc": """ 
                <p>Thiên đường nghỉ dưỡng biển nổi tiếng với Bãi biển trong xanh, resort sang trọng, hải sản tươi ngon.</p>
                <p>📍Vị trí: Phú Quốc là đảo lớn nhất Việt Nam, thuộc tỉnh Kiên Giang, nằm trong vịnh Thái Lan, gần biên giới Campuchia.</p>
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Biển và bãi cát đẹp: Nước trong, sóng hiền, rất phù hợp để tắm biển, lặn ngắm san hô.</li>
                    <li>Thiên nhiên đa dạng: Phần lớn đảo nằm trong khu bảo tồn sinh quyển do UNESCO công nhận, có rừng, núi, hệ sinh thái biển-mặn kết hợp.</li>
                    <li>Dễ tiếp cận & phát triển du lịch: Hạ tầng du lịch hiện đại, nhiều resort, trò chơi giải trí.</li>
                </ul>
				<img src="/static/images/phuquoc.jpg" class="detail-img" alt="Phú Quốc – Đảo Ngọc">
                <p>Gợi ý:</p>
                <ul>
                    <li>Thời điểm đẹp nhất: mùa khô từ khoảng tháng 11 đến tháng 4 — trời nắng, biển êm, thuận tiện tham quan ngoài trời và biển.</li>
                    <li>Cáp treo Hòn Thơm xuất phát khoảng từ 9:00 AM, nhiều chặng trong ngày — nên đi sớm để tránh đông.</li>
                	<li>Đi bộ tham quan biển/ngắm hoàng hôn: Khoảng 17:00 trở đi là thời điểm đẹp để ngắm hoàng hôn ở bãi tây đảo.</li>
				</ul>
                """}, 
			{   "title": "Hà Tiên – Thơ mộng hữu tình", 
                "slug": "ben-ninh-kieu",
                "lat": 10.035,
                "lng": 105.788,
                "img": "benninhkieu.jpg",
                "desc": """ 
                <p>Không khí chậm rãi, yên bình hơn nhiều so với Phú Quốc – phù hợp với du khách muốn thư giãn hoặc khám phá cảnh đẹp tự nhiên và văn hóa địa phương.</p>
                <p>📍Vị trí: Thị xã Hà Tiên, Tỉnh Kiên Giang cách TP Rạch Giá khoảng 100km.</p>
				<img src="/static/images/hatien.jpg" class="detail-img" alt="Hà Tiên">
                <p>Điểm nổi bật:</p>
                <ul>
                    <li>Cảnh quan sơn thủy hữu tình hiếm có ở miền Tây (núi – biển – sông – hang động).</li>
                    <li>Văn hóa đa dạng (Việt – Khmer – Hoa – Chăm) hòa trộn độc đáo.</li>
                    <li>Hải sản tươi ngon, giá phải chăng, đặc sản riêng như mắm cà xỉu và xôi xiêm.</li>
                </ul>
                <p>Gợi ý:</p>
                <ul>
                    <li>Thời gian đẹp nhất: Tháng 11 – tháng 4 (mùa khô, biển đẹp, ít mưa)</li>
					<li>Hoàng hôn đẹp nhất: Bãi Mũi Nai hoặc bờ kè nhìn ra đảo Phú Quốc.</li>
                    <li>ặc sản nên thử: Bánh canh chả ghẹ, xôi xiêm, mắm cà xỉu (mua về làm quà).</li>
                </ul>
                """}
		] 
    },
    "en": {
        "Can Tho": [
            { "title": "Ninh Kieu Wharf - City Symbol",
            "desc": """
            <p>The symbol of Can Tho on the gentle Hau River, is a place to walk, sightsee and take beautiful photos.</p>
            <img src="/static/images/benninhkieu.jpg" class="detail-img" alt="Panoramic view of Ninh Kieu Wharf">
            <p>📍 Location: Center of Can Tho City, on the banks of Hau River.</p>
            <p>Highlights:</p>
            <ul>
                <li>Ninh Kieu pedestrian bridge is brightly lit at night.</li>
                <li>Wharf to go to the floating market, cruise on Hau River.</li>
                <li>Uncle Ho's statue and airy park.</li>
            </ul>
            <img src="/static/images/bac_ho.jpg" class="detail-img" alt="Uncle Ho Statue at Can Tho Park">
            <p>Suggestion:</p>
            <ul>
                <li>Visiting hours: All day (best in the evening).</li>
                <li>Combine dinner on a cruise to watch the river at night.</li>
                <li>There is street music and dancing on weekends.</li>
            </ul>
            """},
            {"title": "Cai Rang Floating Market - Symbol of the West",
            "desc": """
            <p>One of the largest floating markets in the West, bustling from dawn, specializing in selling fruits and specialties of the river region.</p>
            <p>Highlights:</p>
            <ul>
                <li>Boats with "beo" (product samples hung on poles) for sale.</li>
                <li>Fruits, fresh agricultural products, breakfast dishes such as noodles, coffee sold right on the boat.</li>
            <img src="/static/images/chocairang.jpg" class="detail-img" alt="Cai Rang Floating Market Can Tho">
            </ul>
            <p>Suggestions:</p>
            <ul>
            <li>Visiting hours: 5:00 a.m. - 9:00 a.m.</li>
            <li>Should take a small boat tour to get into the market.</li>
            <li>The experience of eating noodles on a boat is a "must-try".</li>
            </ul>
            """},
            { "title": "Bat Pagoda - Unique Khmer Pagoda (Old Soc Trang)",
            "desc": """
            <p>An ancient Khmer pagoda over 400 years old, famous for thousands of bats hanging on the treetops in the campus.</p>
            <p>📍Location: Ward 3, Soc Trang City, about 2 km from the center.</p>
            <p>History & Architecture:</p>
            <ul>
                <li>Built in the 16th century, it is a typical Khmer Southern Buddhist temple.</li>
                <li>The main hall has typical Khmer architecture, multi-layered curved roof, and sophisticated patterns.</li>
                <li>The temple also preserves many precious ancient Buddha statues.</li>
            </ul>            
            <img src="/static/images/chuadoi.jpg" class="detail-img" alt="Bat Pagoda in Soc Trang">
            <p>Highlights:</p>
            <ul>
                <li>Thousands of crow bats (large species, wingspan up to 1m) live in the campus.</li>
                <li>Bats only hang around during the day, and fly out in the evening to find food → creating a unique and rare sight.</li>
            </ul>
            <p>Suggestions:</p>
            <ul>
                <li>Opening hours: Free Visit all day, best in the morning or cool afternoon.</li>
                <li>You should dress politely when entering the temple.</li>
                <li>Keep quiet, do not disturb the bats.</li>
            </ul>
            """},
            { "title": "Lung Ngoc Hoang Nature Reserve (old Hau Giang)",
            "desc": """
            <p>Lung Ngoc Hoang is considered the "green lung" of the West, possessing a rich flooded forest ecosystem with dense canals, dense vegetation, wild and cool space, very suitable for eco-tourism, exploring the forest by boat, bird watching and taking photos of natural forest and river scenery.</p>
            <p>📍Location: Phung Hiep district, Hau Giang province.</p>
            <img src="/static/images/lungngochoang.jpg" class="detail-img" alt="Lung Ngoc Hoang Nature Reserve">
            <p>Highlights:</p>
            <ul>
                <li>Large area (more than 2,800 hectares) of flooded Melaleuca forest. Wild natural space, winding canals, very suitable for eco-tourism, bird watching, walking in the Melaleuca forest.</li>
                <li>Great natural value - preserving rare biodiversity.</li>
            </ul>
            <p>Suggestions:</p>
            <ul>
                <li>Good time: early morning or late afternoon to avoid the harsh sunlight and enjoy the quiet space.</li>
                <li>Bring insect repellent, non-slip shoes because the road may be a bit wet or muddy.</li>
                <li>Because it is a nature reserve, keep it clean and do not encroach on wildlife areas.</li>
            </ul>
            """}
            ],
        "Ca Mau": [
            { "title": "Ca Mau Cape - Southernmost landmark",
            "desc": """
            <p>Ca Mau Cape is the southernmost point of the Fatherland, where the strip of land of Vietnam stretches out to the ocean. Coming here, you can check-in at GPS landmark 0001, the boat symbol and admire the view of the mangrove forest - the immense sea and sky.</p>
            <p>📍Location: Ca Mau Cape is located in Dat Mui commune, Ngoc Hien district, Ca Mau province, the southernmost point of mainland Vietnam.</p>
            <img src="/static/images/muicamau.jpg" class="detail-img" alt="Ca Mau Cape Southernmost landmark">
            <p>Highlights:</p>
            <ul>
                <li>This is one of the rare places where you can watch the sunrise of the East Sea and the sunset of the West Sea right at the same location, bringing a sacred and proud feeling when touching "the end of Vietnam".</li>
                <li>Symbolic works such as the Ho Chi Minh road milestone Km 2436 at Ca Mau cape, a symbol of sovereignty and the southernmost position.</li>
                <li>Mangrove ecosystem: mangrove trees, rhododendron trees grow on alluvial soil, mangrove roots grow upwards to hold the soil.</li>
            </ul>
            <p>Suggestions:</p>
            <ul>
                <li>Suitable for going early in the morning or late in the afternoon to see the sea and beautiful light.</li>
                <li>Going by road to Dat Mui can be a bit far - carefully prepare means of transport, fuel, and snacks.</li>
                <li>Respect the environment: do not litter, preserve the natural landscape.</li>
            </ul>
            """},
            { "title": "U Minh Ha mangrove forest",
            "desc": """
            <p>U Minh Ha forest is a typical mangrove-cajuput forest ecosystem in the West, considered the "green lung" of Ca Mau. Wild space with crisscrossing canals, dense vegetation and many rare birds and animals.</p>
            <p>📍Location: U Minh Ha National Park is located in Ca Mau province, in the mangrove - cajuput forest area.</p>
            <img src="/static/images/rungngapman.jpg" class="detail-img" alt="U Minh Ha Mangrove Forest">
            <p>Highlights:</p>
            <ul>
                <li>Flooded cajuput forest, rich ecosystem with many species of flora and fauna and interwoven canals.</li>
                <li>There is a high observatory to see the whole view of U Minh Ha forest.</li>
                <li>Sightseeing activities such as boating through canals, listening to the "forest frame" - very different from normal beach tourism.</li>
            </ul>
            <p>Suggestions Note:</p>
            <ul>
                <li>The forest can be visited all year round, but the best time is the dry season (less rain) or the flood season when you want to go deeper by boat.</li>
                <li>Wear long-sleeved shirts + insect repellent if you go into the forest because there may be a lot of mosquitoes and insects.</li>
                <li>If you go in the flood season, you can rent a boat to visit; in the dry season, the road will be more convenient.</li>
            </ul>
            """},
            {"title": "Quan Am Phat Dai (Mother Nam Hai)",
            "desc": """
            <p>Quan Am Phat Dai (also known as "Mother Nam Hai") is a large spiritual complex located on the coast of Bac Lieu province - the Southwest region. This is not only a place of worship for Buddhists but also a prominent spiritual tourist destination with the symbol of Bodhisattva Avalokitesvara facing the sea, meaning to protect and bring peace to the people of the sea.</p>
            <p>📍Location: Bo Tay hamlet, Nha Mat ward, Bac Lieu city, Bac Lieu province. Located about 8 km from the center of Bac Lieu city towards the sea.</p>
            <p>History & architecture:</p>
            <ul>
                <li>Established in 1973 with the idea of ​​Venerable Thich Tri Duc.</li>
                <li>The architecture is in the style of Northern Buddhism, with decorative details, three-door gate, and tall main hall, creating a solemn feeling.</li>
            </ul>
            <img src="/static/images/menamhai.jpg" class="detail-img" alt="Quan Am Phat Dai">
            <p>Highlights:</p>
            <ul>
                <li>The statue of Bodhisattva Avalokitesvara is about 11 m high, placed on a large lotus pedestal, facing the sea, and is the highlight of this spiritual area.</li>
                <li>With a strong meaning of Belief: Buddha statue facing the sea as if protecting fishermen and coastal people from the waves.</li>
				<li>Natural space combined with spiritual architecture - spacious campus, near the sea, lots of trees and convenient roads for sightseeing and taking photos.</li>
			</ul>
            <p>Suggestions:</p>
            <ul>
                <li>Dress politely because this is a sacred place, take time to worship and meditate.</li>
                <li>Bring a hat and sunscreen because the area near the sea has strong sunlight and sea breeze.</li>
				<li>There is free parking and vegetarian food service for guests Vietnam reaches out to the ocean. Coming here, you can check-in at GPS landmark 0001, the boat symbol and admire the mangrove forest - immense sea and sky.</p>
			<p>📍Location: Ca Mau Cape is located in Dat Mui commune, Ngoc Hien district, Ca Mau province, the southernmost mainland of Vietnam.</p>
			<img src="/static/images/muicamau.jpg" class="detail-img" alt="Ca Mau Cape, the southernmost landmark">
			<p>Highlights:</p>
			<ul>
				<li>This is one of the rare places where you can watch the sunrise of the East Sea and the sunset of the West Sea right at the same location, bringing a sacred and proud feeling when touching "the end of Vietnam".</li>
				<li>Symbolic works such as the Ho Chi Minh road landmark Km 2436 at Ca Mau cape, a symbol of sovereignty and the southernmost position.</li>
				<li>Mangrove ecosystem: trees mangroves, mangroves grow on alluvial soil, mangrove roots grow upwards to hold the soil.</li>
			</ul>
			<p>Suggestions:</p>
			<ul>
				<li>Suitable for going early in the morning or late in the afternoon to see the sea and beautiful light.</li>
				<li>Going by road to Dat Mui can be a bit far - carefully prepare your vehicle, fuel, and snacks.</li>
				<li>Respect the environment: do not litter, preserve the natural landscape.</li>
			</ul>
			"""},
			{ "title": "U Minh Ha Mangrove Forest",
			"desc": """
			<p>U Minh Ha Forest is a typical Melaleuca - Mangrove ecosystem of the West, considered the "green lung" of Ca Mau. Wild space with crisscrossing canals, dense vegetation and many rare birds and animals.</p>
			<p>📍Location: U Minh Ha National Park is located in Ca Mau province, in the mangrove forest - cajuput forest area.</p>
			<img src="/static/images/rungngapman.jpg" class="detail-img" alt="U Minh Ha Mangrove Forest">
			<p>Highlights:</p>
			<ul>
				<li>Flooded cajuput forest, rich ecosystem with many species of flora and fauna and interwoven canals.</li>
				<li>There is a high observatory to see the whole view of U Minh Ha forest.</li>
				<li>Sightseeing activities such as boating through canals, listening to the "forest frame" - very different from normal beach tourism.</li>
			</ul>
			<p>Suggestions:</p>
			<ul>
				<li>The forest can Visit all year round but the best time is the dry season (less rain) or the flood season when you want to go deeper by boat.</li>
				<li>Wear long sleeves + insect repellent if going into the forest because there may be a lot of mosquitoes and insects.</li>
				<li>If you go during the flood season, you can rent a boat to visit; in the dry season, the road will be more convenient.</li>
			</ul>
			"""},
			{"title": "Quan Am Phat Dai (Mother Nam Hai)",
			"desc": """
			<p>Quan Am Phat Dai (also known as "Mother Nam Hai") is a large spiritual complex located on the coast of Bac Lieu province - the Southwest region. This is not only a place of worship for Buddhists but also a prominent spiritual tourist destination with the symbol of Bodhisattva Avalokitesvara facing the sea, meaning to protect and bring peace to the people of the sea.</p>
			<p>📍Location: Bo Tay hamlet, Nha Mat ward, Bac Lieu city, Bac Lieu province. Located about 8 km from the center of Bac Lieu city towards the sea.</p>
			<p>History & architecture:</p>
			<ul>
				<li>Established in 1973 with the idea of ​​Venerable Thich Tri Duc.</li>
				<li>The architecture is in the style of Northern Buddhism, with decorative details, three-door gate, and tall main hall, creating a solemn feeling.</li>
			</ul>
			<img src="/static/images/menamhai.jpg" class="detail-img" alt="Quan Am Phat Dai">
			<p>Highlights:</p>
			<ul>
				<li>The statue of Bodhisattva Avalokitesvara is about 11 m high, placed on a large lotus pedestal, overlooking the sea, and is the highlight of this spiritual area.</li>
				<li>With a strong religious meaning: the Buddha statue facing the sea seems to protect fishermen and coastal people from the waves and wind.</li>
				<li>Natural space combined with spiritual architecture - spacious campus, near the sea, lots of trees and convenient roads for sightseeing and taking photos.</li>
			</ul>
			<p>Suggestions:</p>
			<ul>
				<li>Dress politely because this is a sacred place, take time to worship and meditate.</li>
				<li>Bring a hat and sunscreen because the area near the sea has strong sunlight and sea breeze.</li>
				<li>There is free parking and vegetarian food service for worshipers at certain times.</li>
			</ul>
			"""}
			],
			"Vinh Long": [
			{ "title": "Cai Cuong Ancient House - French-style architectural relic",
			"desc": """
			<p>Cai Cuong Ancient House is one of the typical ancient architectural works in the Southwest region, located on An Binh Islet - a land famous for its beautiful riverside gardens.</p>
			<p>📍Location: No. 38, Binh Hoa Hamlet, Binh Hoa Phuoc Commune, Long Ho District, Vinh Long Province.</p>			
			<img src="/static/images/caicuong.jpg" class="detail-img" alt="Cai Cuong Ancient House - French-style architectural relic">
			<p>History & Architecture:</p>
			<ul>
				<li>The house was built in 1885 by the family of Mr. Pham Van Bon (also known as "Cai Cuong") - a great landowner in the garden area.</li>
				<li>Special architecture: built in the shape of the letter "T" consists of two perpendicular houses, the main facade facing North overlooking Cai Muoi canal.</li>
				<li>The combination of East - West architecture: the exterior has a Western (French) feel while the interior is made of ironwood, yin-yang tile roof, fish-scale roof... in bold Vietnamese style.</li>
			</ul>
			<img src="/static/images/caicuong1.jpg" class="detail-img" alt="Cai Cuong Ancient House - Interior">
			<p>Highlights:</p>
			<ul>
			<li>Not only a material heritage, Cai Cuong ancient house also reflects the life, culture and style of the Southern people in the late 19th century.</li>
			<li>Preserving almost intact the ironwood details, ceramic tiles, patterns, yin-yang tile roof that are more than a hundred years old.</li>
			<li>A unique cultural - ecological tourist destination when combined with visiting the fruit garden, experiencing the garden life.</li>
			</ul>
			<p>Suggestions:</p>
			<ul>
				<li>Although we could not find very clear information about the exact opening hours, it is stated that An Binh ferry operates from 4am to 10pm.</li>
				<li>When visiting, you should keep the interior intact, do not arbitrarily move antique items to preserve the nature of the house.</li>
				<li>You should come early in the morning or late in the afternoon to avoid harsh sunlight and beautiful light for taking photos.</li>
			</ul>
			"""},
			{ "title": "Van Thanh Mieu Vinh Long",
			"desc": """
			<p>Van Thanh Mieu Vinh Long is considered the "Quoc Tu Giam of the South". This is the place to worship Confucius and Confucian sages, and is also the center of education and cultural activities of the ancient people of Cochinchina.</p>
			<p>📍Location: Located on Tran Phu Street, Ward 4, Vinh Long City, Province Vinh Long.</p>
			<img src="/static/images/vanmieu.jpg" class="detail-img" alt="Van Thanh Mieu Vinh Long">
			<p>History & architecture:</p>
			<ul>
				<li>Built between 1864-1866 under the reign of Phan Thanh Gian and initiated by Mr. Nguyen Thong (Director of Education).</li>
				<li>One of the three "Van Thanh Mieu" in the Southern region, and considered the "Quoc Tu Giam in the South".</li>
				<li>Architecture: three-story gate with curved roof, two sides of the entrance are rows of tall star trees - creating a solemn, quiet space.</li>
			</ul>
			<img src="/static/images/vanmieu1.jpg" class="detail-img" alt="Van Thanh Mieu Vinh Long - inside">
			<p>Highlights:</p>
			<ul>
				<li>National historical and cultural relic.</li>
				<li>Every year, the Van Thanh Mieu Festival (full moon of the second lunar month) attracts a large number of visitors from all over the world.</li>
				<li>It is a place to preserve cultural values, the spirit of learning and the tradition of respecting teachers of the Vietnamese people.</li>
			</ul>
			<p>Suggestions:</p>
			<ul>
				<li>Opening hours: From about 7:00 am to 5:00 pm every day.</li>
				<li>Because it is a place of worship + historical relic, when visiting, please keep order and wear appropriate clothing.</li>
				<li>You can combine sightseeing with walking around the Long Ho River area, relaxing and taking photos.</li>
			</ul>
			"""},
			{ "title": "Ang Pagoda: Angkorajaborey (Old Tra Vinh)",
			"desc": """
			<p>Ang Pagoda is one of the most ancient and famous Khmer pagodas in Tra Vinh, located next to Ba Om Pond. The pagoda has a strong Southern Khmer architecture with multi-layered curved roofs, intricately carved pillars and prominent gold tones.</p>
			<p>📍Location: In group 4, ward 8, Tra Vinh city, Tra Vinh province.</p>
			<p>History & architecture:</p>
			<ul>
				<li>Ang Pagoda (also known as Wat Angkor Raig Borei) is about 3.5 hectares wide.</li>
				<li>The architecture is a combination of ancient Khmer tradition and some modern architectural elements - preserving the art of bird head sculptures, the Naga snake god, and the characteristic curved roof.</li>
				<li>Carrying the cultural and historical values ​​of the Southern Khmer people, it is a place for religious activities and preserving traditions.</li>
			</ul>
			<img src="/static/images/chuaang.jpg" class="detail-img" alt="Ang Pagoda (Angkorajaborey) – Tra Vinh">		
			<p>Highlights:</p>
			<ul>
				<li>An ancient Khmer temple in the South, considered the most beautiful temple in Tra Vinh.</li>
				<li>Architecture with strong Khmer and Angkor features: temple roof, reliefs, Naga snake statue, solid sacred space.</li>
				<li>The surrounding environment is cool with ancient trees, large temple yard, creating a sense of serenity.</li>
			</ul>
			<p>Suggestions:</p>
			<ul>
				<li>When entering the temple, you should wear polite clothes and walk gently because this is a sacred place.</li>
				<li>Bring a hat/cap, sunscreen if going at noon; It is best to go in the morning or afternoon for beautiful light and pleasant weather.</li>
				<li>If you want to learn more about Khmer culture, ask a local guide or look at the information in advance.</li>
			</ul>
			"""}, 
			{ "title": "Dong Khoi Relic Site (Ben Tre)",
			"desc": """
			<p>Dong Khoi Relic Site in Ben Tre is the place that marks the historic Dong Khoi movement in 1960, symbolizing the indomitable and resilient spirit of the people of the South in the struggle for national independence. The relic site not only has great historical value but is also a destination for educating revolutionary traditions for today's generations.</p>
			<p>📍Location: Dinh Thuy Commune, Mo Cay Nam District, Ben Tre Province.</p>
			<p>Highlights:</p>
			<ul>
				<li>It is the place where the Dong Khoi movement broke out in 1960, starting the revolutionary climax in the South.</li>
				<li>The relic site includes the Dong Khoi monument Khoi, the exhibition house of artifacts, the memorial area for heroic martyrs, and the space for historical reenactment.</li>
				<li>This is a destination often visited by groups of students, university students, and veterans.</li>
			</ul>			
			<img src="/static/images/dongkhoi.jpg" class="detail-img" alt="Khu di tích Đồng khời">
			<p>Suggestions:</p>
			<ul>
				<li>Suitable for those who love history - revolutionary traditions.</li>
				<li>You can go in groups or on a practical study tour.</li>
				<li>After visiting, you can stop by Ben Tre market to buy specialties such as coconut candy and milk rice paper.</li>
			</ul>
			"""}	
		],
			"Dong Thap": [
			{ "title": "Dong Sen Thap Muoi",
			"desc": """
			<p>Dong Sen Thap Muoi is one of the largest and most beautiful lotus fields in the West, famous for its vast space of blooming lotus flowers, imbued with the rustic, peaceful features of the Dong Thap Muoi region.</p>
			<p>📍Location: My Hoa Commune, Thap Muoi District, Dong Thap Province. 10km from City. Cao Lanh about 40km</p>
			<p>History & architecture:</p>
			<img src="/static/images/dongthap.jpg" class="detail-img" alt="Dong Sen Thap Muoi">
			<p>Highlights:</p>
			<ul>
				<li>Immense lotus fields, most beautiful in lotus season (May to October).</li>
				<li>Experiential services: take a boat to take photos, wear Ao Ba Ba, pick lotus, check-in at the bamboo bridge.</li>
				<li>Lotus cuisine: lotus rice, lotus root salad, lotus sweet soup, lotus tea.</li>
			</ul>
			<p>Suggestions:</p>
			<ul>
				<li>Should go early 6:30 - 9:00 or cool afternoon 15:30 - 17:30</li>
				<li>Bring a hat and sunscreen; Wear low shoes/sandals.</li>
				<li>Avoid walking after rain because the dirt road can be slippery</li>
			</ul>
			"""},
			{
			"title": "Sa Dec Flower Village",
			"desc": """
			<p>Sa Dec Flower Village is the "Flower Capital of the West", famous for thousands of ornamental flowers grown on unique floating trellises, a famous cultural - ecological tourist destination, taking photos and buying flowers all year round.</p>
			<p>📍Location: Tan Quy Dong Ward, Sa Dec City, Dong Thap. About 30km from Cao Lanh.</p>
			<p>History & architecture:</p>
			<ul>
				<li>Formed in the late 19th - early 20th century</li>
				<li>A long-standing traditional flower village in the West.</li>
				<li>Architectural features: ancient houses, traditional craft villages, typical floating flower shelves.</li>
			</ul>
			<img src="/static/images/langhoa.jpg" class="detail-img" alt="Sa Dec Flower Village">
			<p>Highlights:</p>
			<ul>
				<li>A flower village over 100 years old.</li>
				<li>Thousands of flower & ornamental varieties: chrysanthemum, rose, bonsai, ancient ornamental plants.</li>
				<li>There is a check-in area, wooden bridge, greenhouse, village house making cakes, jams.</li>
			</ul>
			<p>Suggestions Note:</p>
			<ul>
				<li>Best time: December - January of the lunar calendar.</li>
				<li>Should go early in the morning or at sunset.</li>
				<li>Respect the flower growers - do not pick flowers when taking photos.</li>
			</ul>
			"""}, 
			{ "title": "Cu Lao Thoi Son (Con Lan)",
			"desc": """
			<p>Cu Lao Thoi Son is located in the middle of the gentle Tien River, a famous eco-tourism destination with lush green fruit gardens, small canals and attractive community tourism activities such as riding a sampan, listening to traditional music, and enjoying garden specialties.</p>
			<p>📍Location: Located in the middle of the Tien River, Thoi Son Commune, My Tho City, Tien Giang Province.</p>
			<p>Highlights:</p>
			<ul>
				<li>It is a large and green islet, famous for its fruit gardens, garden houses, traditional craft villages (making coconut candy, honey, weaving...).</li>
				<li>Visitors can ride a sampan on small canals, listen to traditional music, enjoy garden fruits, and have lunch in a rustic space.</li>
				<li>This is a tourist destination Ecological tourism - a typical community, imbued with the characteristics of the Mekong Delta.</li>
			</ul>
			<img src="/static/images/thoison.jpg" class="detail-img" alt="Cu Lao Thoi Son">
			<p>Suggestions:</p>
			<ul>
				<li>Should go early in the morning to avoid the sun and enjoy the cool air.</li>
				<li>Wear light clothes and shoes that are easy to move around because there are many sections by boat and on foot.</li>
				<li>Try traditional music, eat fried elephant ear fish and drink fresh honey - a local specialty.</li>
			</ul>
			"""},
			{ "title": "Vinh Trang Pagoda (Tien Giang)",
			"desc": """
			<p>Vinh Trang Pagoda - the oldest and largest pagoda in Tien Giang - has a unique architectural style that blends Asia and Europe. With a peaceful space and green gardens Cool with majestic Buddha statues, the pagoda is an ideal stop for those who want to find peace and admire the quintessence of architectural art.</p>
			<p>📍Location: No. 66 Nguyen Trung Truc, Ward 8, My Tho City.</p>
			<img src="/static/images/chuavinhtrang.jpg" class="detail-img" alt="Chua Vinh Trang">
			<p>Highlights:</p>
			<ul>
				<li>The oldest and largest pagoda in Tien Giang, built in the 19th century.</li>
				<li>The architecture harmoniously combines Asia - Europe (French, Roman, Thai, Cambodian, Japanese), creating a rare unique look.</li>
				<li>In the campus there is a giant Maitreya Buddha statue, a reclining Amitabha statue, an airy and peaceful garden.</li>
			</ul>
			<img src="/static/images/chuavinhtrang1.jpg" class="detail-img" alt="Chua Vinh Trang 1">
			<p>Suggestions:</p>
			<ul>	
				<li>Dress politely and discreetly, and keep order in the sacred place.</li>
				<li>Taking photos at the Maitreya Buddha statue area and the temple garden is very beautiful.</li>
				<li>Should combine a visit to Cu Lao Thoi Son in the same session.</li>
			</ul>
			"""}
			], "An Giang": [
			{ "title": "Cam Mountain (Thien Cam Son) - The Roof of the West",
			"desc": """
			<p>The highest mountain in the Mekong Delta, cool climate all year round, quite diverse natural landscape. Full of spiritual, historical and legendary elements, often likened to "the roof of the West".</p>
			<p>📍Location: An Hao Commune, Tinh Bien District, An Giang Province.</p>
			<img src="/static/images/nuicamangiang.jpg" class="detail-img" alt="Cam Mountain (Thien Cam Son) - "The Roof of the West"">
			<p>Highlights:</p>
			<ul>
				<li>The 33.6m high Maitreya Buddha statue - the symbol of Cam Mountain, one of the largest Maitreya Buddha statues in Vietnam.</li>
				<li>Thuy Liem Lake with its calm water reflecting the mountains, along with spiritual works such as Van Linh Pagoda and Big Buddha Pagoda, attracts a large number of pilgrims.</li>
				<li>Experience the Cam Mountain Cable Car to see the majestic That Son panorama from above, fully feel the majestic natural beauty of the Seven Mountains region.</li>
			</ul>
			<p>Suggestions:</p>
			<ul>
				<li>⏰ Visiting time: all day from 6:00 a.m. to 6:00 p.m.</li>
				<li>Cable car ticket: over 180,000 VND/person.</li>
				<li>Should go early in the morning to avoid the sun, wear sneakers. If trekking, choose the dry season.</li>
			</ul>
			"""},
			{ "title": "Tra Su Melaleuca Forest - Paradise in the flood season",
			"desc": """
			<p>Green paradise with duckweed covering the beautiful water surface where home to hundreds of rare bird species.</p>
			<p>📍Location: Van Giao Commune, Tinh Bien District, about 30 km from Chau Doc.</p>
			<img src="/static/images/rungtram.jpg" class="detail-img" alt="Tra Su Melaleuca Forest - Paradise in the flood season">
			<p>Highlights:</p>
			<ul>
				<li>More than 140 species of plants, 70+ species of birds (including rare species in the Red Book).</li>
				<li>Go by canoe, boat or row a boat among the green duckweed forest. Check-in at the longest bamboo bridge in Vietnam.</li>
				<li>Biodiversity conservation area, environmental regulation, known as "the most beautiful cajuput forest in Vietnam"</li>
			</ul>
			<img src="/static/images/rungtram1.jpg" class="detail-img" alt="Tra Su Cajuput Forest - Birds">
			<p>Suggestions:</p>
			<ul>
				<li>Most beautiful scenery: Flood season (September-November), especially at dawn or dusk.</li>
				<li>Go in the morning or late afternoon; Bring a camera, binoculars, and soft-soled shoes for easy movement.</li>
			</ul>
			"""},
			{ "title": "Phu Quoc - Pearl Island",
			"desc": """
			<p>A famous beach resort paradise with clear blue beaches, luxury resorts, and fresh seafood.</p>
			<p>📍Location: Phu Quoc is the largest island in Vietnam, in Kien Giang province, located in the Gulf of Thailand, near the Cambodian border.</p>
			<p>Highlights:</p>
			<ul>
				<li>Beautiful sea and sand: Clear water, gentle waves, very suitable for swimming and snorkeling.</li>
				<li>Diverse nature: Most of the island is located in a UNESCO-recognized biosphere reserve, with forests, mountains, and a combined marine-salt ecosystem.</li>
				<li>Easy access & tourism development: Modern tourism infrastructure, many resorts, and entertainment games location.</li>
			</ul>
			<img src="/static/images/phuquoc.jpg" class="detail-img" alt="Phu Quoc – Pearl Island">
			<p>Suggestions:</p>
			<ul>
				<li>Best time: dry season from around November to April — sunny, calm sea, convenient for outdoor and beach sightseeing.</li>
				<li>Hon Thom cable car departs from around 9:00 AM, many stops during the day — should go early to avoid crowds.</li>
				<li>Walking to visit the beach/watching the sunset: Around 17:00 onwards is a beautiful time to watch the sunset on the west beach of the island.</li>
			</ul>
			"""},
			{ "title": "Ha Tien – Dreamy and romantic",
			"desc": """
			<p>The atmosphere is slower and more peaceful than Phu Quoc – suitable for tourists who want to relax or explore natural beauty and local culture.</p>
			<p>📍Location: Ha Tien Town, Kien Giang Province, about 100km from Rach Gia City.</p>
			<img src="/static/images/hatien.jpg" class="detail-img" alt="Tra Su Melaleuca Forest - Birds">
			<p>Highlights:</p>
			<ul>
				<li>Rarely picturesque landscape in the West (mountains - sea - rivers - caves).</li>
				<li>Unique blend of diverse cultures (Vietnamese - Khmer - Chinese - Cham).</li>
				<li>Fresh seafood, affordable prices, unique specialties such as mam ca xiu and xoi xiem.</li>
			</ul>
			<p>Suggestions:</p>
			<ul>
				<li>Best time: November - April (dry season, beautiful sea, little rain)</li>
				<li>Best sunset: Mui Nai beach or the embankment overlooking Phu Quoc island.</li>
				<li>Specialties to try: Crab cake noodle soup, sticky rice, and fish sauce (buy as gifts).</li>
			</ul>
			"""}
			] 
		},
    "kr": {
		"Can Tho": [
			{ "title": "닌끼우 부두 - 도시의 상징",
			"desc": """
			<p>잔잔한 하우 강변에 위치한 칸토의 상징인 닌끼우 부두는 산책, 관광, 아름다운 사진 촬영을 즐기기에 좋은 곳입니다.</p>
			<img src="/static/images/benninhkieu.jpg" class="detail-img" alt="닌끼우 부두의 파노라마 전망">
			<p>📍 위치: 칸토 시내 중심가, 하우 강변.</p>
			<p>주요 볼거리:</p>
			<ul>
				<li>닌끼우 보행자 다리는 밤에 밝게 빛납니다.</li>
				<li>부두에서 수상 시장과 하우 강 크루즈를 즐겨보세요.</li>
				<li>호 아저씨 동상과 쾌적한 공원.</li>
				</ul>
				<img src="/static/images/bac_ho.jpg" class="detail-img" alt="깐토 공원의 호 아저씨 동상">
				<p>추천:</p>
			<ul>
				<li>방문 시간: 하루 종일 (저녁에 방문하시는 것이 좋습니다).</li>
				<li>크루즈에서 저녁 식사를 하며 밤에는 강변을 감상해 보세요.</li>
				<li>주말에는 거리 음악과 춤 공연이 펼쳐집니다.</li>
			</ul>
			"""},
			{ "title": "까이랑 수상시장 - 서양의 상징",
			"desc": """
			<p>서양 최대 규모의 수상시장 중 하나로, 새벽부터 활기가 넘치며 과일과 강변 지역의 특산품을 판매합니다.</p>
			<p>주요 볼거리:</p>
			<ul>
				<li>"베오"(제품 샘플을 장대에 걸어 판매하는 배).</li>
				<li>과일, 신선한 농산물, 아침 식사 메뉴 등 배 위에서 바로 판매되는 국수와 커피.</li>
			</ul>			
			<img src="/static/images/chocairang.jpg" class="detail-img" alt="깐토 까이랑 수상시장">
			<p>추천:</p>
			<ul>
				<li>방문 시간: 오전 5시 - 오전 9시</li>
				<li>시장에 들어가려면 작은 배를 타고 가는 것이 좋습니다.</li>
				<li>배 위에서 국수를 먹는 경험은 "꼭" 해봐야 할 일입니다.</li>
			</ul>
			"""},
			{ "title": "박쥐 사원 - 독특한 크메르 사원(올드 쏙짱)",
			"desc": """
			<p>400년이 넘은 고대 크메르 사원으로, 나무 꼭대기에 매달린 수천 마리의 박쥐로 유명합니다. 캠퍼스.</p>
			<p>📍위치: 속짱 시 3번 구, 도심에서 약 2km 거리.</p>
			<p>역사 및 건축:</p>
			<ul>
				<li>16세기에 건축된 이 사원은 전형적인 크메르 남방 불교 사원입니다.</li>
				<li>본당은 전형적인 크메르 건축 양식, 여러 겹의 곡선 지붕, 그리고 정교한 문양을 자랑합니다.</li>
				<li>사원에는 귀중한 고대 불상도 많이 보존되어 있습니다.</li>
			</ul>			
			<img src="/static/images/chuadoi.jpg" class="detail-img" alt="속짱 박쥐 사원">
			<p>주요 특징:</p>
			<ul>
				<li>캠퍼스에는 수천 마리의 까마귀 박쥐(날개폭 최대 1m)가 서식합니다.</li>
				<li>박쥐는 낮에만 서식하고 저녁에는 먹이를 찾아 날아갑니다. → 독특하고 보기 드문 광경입니다.</li>
			</ul>
			<p>추천:</p>
			<ul>
				<li>개방 시간: 무료. 하루 종일 방문 가능. 아침이나 시원한 오후에 방문하는 것이 좋습니다.</li>
				<li>사원에 들어갈 때는 예의 바른 복장을 착용해 주세요.</li>
				<li>조용히 하고 박쥐를 방해하지 마세요.</li>
			</ul>
			"""},
			{ "title": "룽응옥황 자연보호구역(구 하우장)",
			"desc": """
			<p>룽응옥황은 서부의 "녹색 허파"로 여겨지며, 울창한 운하, 울창한 초목, 야생적이고 시원한 공간을 갖춘 풍부한 침수림 생태계를 자랑합니다. 생태 관광, 보트를 타고 숲을 탐험하고, 조류를 관찰하고, 자연림과 강 풍경을 사진으로 촬영하기에 매우 적합합니다.</p>
			<p>📍위치: 하우장성 풍히엡 현.</p>
			<img src="/static/images/lungngochoang.jpg" class="detail-img" alt="룽 응옥 호앙 자연 보호 구역">
			<p>주요 특징:</p>
			<ul>
				<li>2,800헥타르가 넘는 넓은 면적의 멜라루카 숲. 야생 자연 공간, 구불구불한 운하는 생태 관광, 조류 관찰, 멜라루카 숲 산책에 매우 적합합니다.</li>
				<li>천부적인 자연적 가치 - 희귀한 생물 다양성 보존</li>
			</ul>
			<p>추천:</p>
			<ul>
				<li>좋아하는 시간: 강한 햇빛을 피해 조용한 공간을 즐기려면 이른 아침이나 늦은 오후가 좋습니다.</li>
				<li>길이 약간 젖어 있거나 진흙투성이일 수 있으므로 방충제와 미끄럼 방지 신발을 준비하세요.</li>
				<li>자연 보호 구역이므로 깨끗하게 유지하고 야생 동물을 침해하지 마세요. 지역.</li>
			</ul>
			"""}
			],
			"Ca Mau": [
			{ "title": "까마우 곶 - 최남단 랜드마크",
			"desc": """
			<p>까마우 곶은 베트남 본토 최남단으로, 베트남 땅이 바다로 뻗어 있는 곳입니다. 이곳에 오시면 GPS 랜드마크 0001(배 심볼)에서 체크인하고 맹그로브 숲, 광활한 바다와 하늘의 풍경을 감상하실 수 있습니다.</p>
			<p>📍위치: 까마우 곶은 까마우 성 응옥 히엔 현 닷 무이 사에 위치해 있으며, 베트남 본토 최남단에 있습니다.</p>
			<img src="/static/images/muicamau.jpg" class="detail-img" alt="까마우 곶 최남단 랜드마크">
			<p>주요 특징:</p>
			<ul>
				<li>동해의 일출과 서해의 일몰을 동시에 감상할 수 있는 드문 장소 중 하나로, 신성하고 자랑스러운 느낌을 선사합니다. "베트남의 끝"을 의미합니다.</li>
				<li>까마우 곶에 있는 호찌민 도로 이정표 2436km는 주권의 상징이자 최남단 위치입니다.</li>
				<li>맹그로브 생태계: 맹그로브 나무, 진달래 나무는 충적토에서 자라며, 맹그로브 뿌리는 위로 자라 토양을 지탱합니다.</li>
			</ul>
			<p>추천:</p>
		<ul>
			<li>바다와 아름다운 빛을 감상하기 위해 이른 아침이나 늦은 오후에 방문하기에 적합합니다.</li>
			<li>닷무이까지 육로로 가는 것은 다소 멀 수 있으므로 교통수단, 연료, 간식을 신중하게 준비하십시오.</li>
			<li>환경을 존중하십시오. 쓰레기를 버리지 말고 자연 경관을 보존하십시오.</li>
			</ul>
			"""},
			{ "title": "우민하 맹그로브 숲",
			"desc": """
			<p>우민하 숲 서부의 전형적인 맹그로브-카유풋 숲 생태계로, 까마우의 "녹색 허파"로 여겨집니다. 교차하는 운하, 울창한 초목, 그리고 수많은 희귀 조류와 동물들이 있는 야생 공간입니다.</p>
			<p>📍위치: 우민하 국립공원은 까마우 성의 맹그로브-카유풋 숲 지역에 위치해 있습니다.</p>
			<img src="/static/images/rungngapman.jpg" class="detail-img" alt="우민하 맹그로브 숲">

			<p>주요 특징:</p>
			<ul>
				<li>침수된 카유풋 숲, 다양한 동식물과 운하가 어우러진 풍부한 생태계.</li>
				<li>우민하 숲의 전경을 한눈에 볼 수 있는 높은 전망대가 있습니다.</li>
				<li>운하를 따라 보트를 타고 "숲의 틀"에 귀 기울이는 등 일반적인 해변 관광과는 매우 다른 관광 활동을 즐길 수 있습니다.</li>
			</ul>
			<p>추천 참고:</p>
			<ul>
				<li>숲은 일 년 내내 방문할 수 있지만, 가장 좋은 시기는 건기(비가 적게 내리는 시기)나 홍수기에 보트를 타고 더 깊이 들어가고 싶을 때입니다.</li>
				<li>모기와 곤충이 많을 수 있으므로 숲에 들어갈 때는 긴팔 셔츠와 방충제를 착용하세요.</li>
				<li>홍수기에 가면 보트를 빌려 방문할 수 있으며, 건기에는 도로가 더 편리합니다.</li>
			</ul>
			"""},
			{"title": "Quan Am Phat Dai (Mother Nam Hai)",
			"desc": """
			<p>Quan Am Phat Dai("Mother Nam Hai"라고도 함)는 박리에우 성(Bac Lieu Province) 해안에 위치한 대규모 영성 단지입니다. 이곳은 불교 신도들의 예배 장소일 뿐만 아니라, 관음보살의 상징이 정면을 향하고 있는 유명한 영적 관광지이기도 합니다. 바다를 보호하고 바다 사람들에게 평화를 가져다준다는 의미입니다.</p>
			<p>📍위치: 박리에우성 박리에우시 냐맛구 보따이 마을. 박리에우시 중심에서 바다 방향으로 약 8km 떨어져 있습니다.</p>
			<p>역사 및 건축:</p>
			<ul>
				<li>1973년 틱찌득 스님의 사상으로 설립되었습니다.</li>
				<li>이 건축물은 북방 불교 양식으로, 장식적인 디테일, 삼문, 높은 본당이 어우러져 엄숙한 분위기를 자아냅니다.</li>
			</ul>
			<img src="/static/images/menamhai.jpg" class="detail-img" alt="콴암팟다이">
			<p>주요 특징:</p>
			<ul>
				<li>관세음보살상은 높이 약 11m로, 큰 바다를 마주 보고 있는 연꽃 받침대는 이 영적인 공간의 하이라이트입니다.</li>
				<li>강력한 신앙의 의미를 담고 있습니다. 마치 어부와 해안가 주민들을 파도로부터 보호하는 듯 바다를 바라보는 불상입니다.</li>
				<li>자연 공간과 영적인 건축물이 어우러진 공간 - 넓은 캠퍼스, 바다 근처, 나무가 많고 관광과 사진 촬영에 편리한 도로가 있습니다.</li>
			</ul>
			<p>추천:</p>
			<ul>
				<li>신성한 장소이므로 예의 바른 복장을 착용하고, 예배와 명상을 위한 시간을 가지세요.</li>
				<li>바닷가 지역은 강한 햇살과 바닷바람이 불기 때문에 모자와 자외선 차단제를 지참하세요.</	li>
				<li>무료 주차가 가능하며, 투숙객을 위한 채식 음식 서비스도 제공됩니다. 어느 시점에서는 숭배해야 합니다.</li>
			</ul>
			"""}
			], 
			"Vinh Long": [
			{ "title": "까이끄엉 고택 - 프랑스식 건축 유적",
			"desc": """
			<p>까이끄엉 고택은 아름다운 강변 정원으로 유명한 안빈 섬에 위치한 남서부 지역의 대표적인 고대 건축물 중 하나입니다.</p>
			<p>📍위치: 빈롱성 롱호구 빈호아푹사 빈호아 마을 38번지</p>
			<img src="/static/images/caicuong.jpg" class="detail-img" alt="까이끄엉 고택 - 프랑스식 건축 유적">
			<p>역사 및 건축:</p>
			<ul>
				<li>이 고택은 1885년 정원 지역의 거물이었던 팜 반 본(Pham Van Bon, "까이끄엉"으로도 알려짐) 씨의 가족에 의해 지어졌습니다.</li>
				<li>특별한 건축물: "T"는 두 채의 수직 주택으로 구성되어 있으며, 북쪽을 향해 있는 본채는 까이 무어이 운하를 내려다보고 있습니다.</li>
				<li>동서양 건축 양식이 조화를 이루고 있습니다. 외관은 서양식(프랑스식) 느낌을 주는 반면, 내부는 철목, 음양 기와, 물고기 비늘 지붕 등 베트남 특유의 강렬한 스타일로 지어졌습니다.</li>
			</ul>
			<img src="/static/images/caicuong1.jpg" class="detail-img" alt="까이 끄엉 고택 - 내부">
			<p>주요 특징:</p>
			<ul>
				<li>까이 끄엉 고택은 단순한 물질적 유산이 아니라 19세기 후반 남방 사람들의 삶, 문화, 그리고 스타일을 반영합니다.</li>
				<li>100년이 넘은 철목 디테일, 도자기 기와, 문양, 음양 기와 지붕이 거의 그대로 보존되어 있습니다.</li>	
				<li>과일 농장을 방문하고 정원을 체험하는 것과 함께라면 독특한 문화 생태 관광지가 될 것입니다. 생활.</li>
			</ul>
			<p>추천:</p>
			<ul>
				<li>정확한 운영 시간에 대한 명확한 정보는 찾을 수 없었지만, 안빈 페리는 오전 4시부터 오후 10시까지 운행한다고 합니다.</li>
				<li>방문 시 집의 자연을 보존하기 위해 내부를 손상시키지 말고, 골동품을 함부로 옮기지 마세요.</li>
				<li>햇볕이 강하고 사진 촬영에 적합한 아름다운 조명을 피하려면 이른 아침이나 늦은 오후에 방문하는 것이 좋습니다.</li>
			</ul>
			"""},
			{ "title": "Van Thanh Mieu Vinh Long",
			"desc": """
			<p>Van Thanh Mieu Vinh Long은 "남부의 꾸옥 뜨 잠(Quoc Tu Giam)"으로 불립니다. 이곳은 공자와 유교 성현을 제사 지내는 곳이며, 코친차이나 고대 사람들의 교육과 문화 활동의 중심지이기도 합니다.</p>
			<p>📍위치: 빈롱성 빈롱시 4구 쩐푸 거리.</p>
			<img src="/static/images/vanmieu.jpg" class="detail-img" alt="반탄미에우 빈롱">
			<p>역사 및 건축:</p>
			<ul>
				<li>1864년에서 1866년 사이 판탄잔(Phan Thanh Gian) 통치 기간에 건립되었으며, 응우옌 통(Nguyen Thong) 교육감의 주도로 시작되었습니다.</li>
				<li>남부 지역의 세 "반탄미에우" 중 하나이며, "남부의 꾸옥 뜨 지암(Quoc Tu Giam)"으로 불립니다.</li>
				<li>건축: 곡선 지붕의 3층 대문, 입구 양쪽에는 키 큰 별나무들이 줄지어 있어 엄숙하고 조용한 공간을 조성합니다.</li>
			</ul>	
			<img src="/static/images/vanmieu1.jpg" class="detail-img" alt="반탄 미에우 빈롱 - 내부">
			<p>주요 볼거리:</p>
			<ul>
			<li>국가 역사 문화 유적지.</li>
			<li>매년 음력 2월 보름달을 기념하는 반탄미에우 축제는 전 세계에서 수많은 방문객을 끌어들입니다.</li>
			<li>베트남 국민의 문화적 가치, 학문 정신, 그리고 스승을 존중하는 전통을 보존하는 곳입니다.</li>
			</ul>
			<p>추천:</p>
			<ul>
				<li>운영 시간: 매일 오전 7시부터 오후 5시까지.</li>
				<li>신앙과 역사 유적지가 공존하는 곳이니, 방문 시에는 질서를 유지하고 적절한 복장을 착용해 주시기 바랍니다.</li>
				<li>롱호 강변을 산책하며 관광을 즐기고, 휴식을 취하며 사진을 찍는 것도 좋습니다.</li>
			</ul>
			"""},
			{ "title": "앙 파고다: 앙코르 자보레이(옛 짜빈)",
			"desc": """
			<p>앙 파고다는 짜빈에서 가장 오래되고 유명한 크메르 사원 중 하나로, 바옴 연못 옆에 위치해 있습니다. 이 사원은 여러 겹의 곡선 지붕, 정교하게 조각된 기둥, 그리고 눈에 띄는 금색으로 이루어진 남부 크메르 건축 양식의 특징을 보여줍니다.</p>
			<p>📍위치: 짜빈성 짜빈시 8번구 햄릿 4번지.</p>
			<p>역사 및 건축:</p>
			<ul>
				<li>앙 파고다(왓 앙코르 라이그 보레이라고도 함)는 약 3.5헥타르 넓이입니다.</li>
				<li>이 건축물은 고대 크메르 전통과 현대 건축 요소가 조화를 이루고 있으며, 새 머리 조각, 나가 뱀신, 그리고 특징적인 곡선 형태의 예술을 보존하고 있습니다. 지붕.</li>
				<li>남부 크메르족의 문화적, 역사적 가치를 간직한 이곳은 종교 활동과 전통 보존의 장소입니다.</li>
			</ul>
			<img src="/static/images/chuaang.jpg" class="detail-img" alt="앙 파고다(앙코라자보레이) - 짜빈">
			<p>주요 볼거리:</p>
			<ul>
				<li>남부 크메르족의 고대 탑으로, 짜빈에서 가장 아름다운 탑으로 손꼽힙니다.</li>
				<li>크메르와 앙코르 양식의 특징이 뚜렷한 건축물: 사원 지붕, 부조, 나가 뱀상, 견고한 성소.</li>
				<li>고대 나무와 넓은 사원 마당이 어우러져 시원한 주변 환경을 조성하여 고요한 분위기를 자아냅니다.</li>
			</ul>
			<p>추천:</p>
			<ul>
				<li>사원에 들어갈 때는 예의 바른 복장을 하고 걸어야 합니다. 이곳은 신성한 장소이므로 조심하세요.</li>
				<li>정오에 가시는 경우 모자/캡을 착용하고 자외선 차단제를 바르세요. 햇살이 좋고 날씨가 좋으면 아침이나 오후에 가시는 것이 가장 좋습니다.</li>
				<li>크메르 문화에 대해 더 자세히 알고 싶으시면 현지 가이드에게 문의하거나 사전에 안내 자료를 읽어보세요.</li>
			</ul>
			"""}, 
			{ "title": "동코이 유적지(벤째)",
			"desc": """
			<p>벤째에 위치한 동코이 유적지는 1960년 동코이 운동의 역사적인 현장으로, 민족 독립을 위한 투쟁에서 남부 주민들의 불굴의 의지와 불굴의 정신을 상징합니다. 이 유적지는 역사적 가치가 높을 뿐만 아니라 오늘날 세대에게 혁명 전통을 전수하는 장소이기도 합니다.</p>
			<p>📍위치: 벤째성 모까이남군 딘투이 사.</p>
			<p>주요 관광 명소:</p>
			<ul>
				<li>1960년 동코이 운동이 발발하여 남부 지역 혁명의 정점을 이룬 곳입니다.</li>
				<li>유적지 동커이 기념비, 유물 전시관, 영웅 순교자 기념관, 그리고 역사 재연 공간이 포함되어 있습니다.</li>
				<li>학생, 대학생, 참전 용사들이 단체로 자주 방문하는 곳입니다.</li>
			</ul>			
			<img src="/static/images/dongkhoi.jpg" class="detail-img" alt="Khu di tích Đồng Khởi">
			<p>추천:</p>
			<ul>
				<li>역사와 혁명 전통을 좋아하는 분들에게 적합합니다.</li>
				<li>단체 또는 실습 학습 투어로 방문할 수 있습니다.</li>
				<li>방문 후에는 벤째 시장에 들러 코코넛 캔디와 밀크 라이스 페이퍼와 같은 특산품을 구매할 수 있습니다.</li>
			</ul>
			"""}
			], 
			"Dong Thap": [
			{ "title": "동센탑무어이",
			"desc": """
			<p>동센탑무어이는 서부에서 가장 크고 아름다운 연꽃밭 중 하나로, 광활한 연꽃밭으로 유명하며, 동탑무어이만의 소박하고 평화로운 분위기를 자아냅니다.</p>
			<p>📍위치: 동탑성 탑무어이구 미호아마을. 까오란시에서 약 40km 거리</p>
			<p>역사 및 건축:</p>
			<img src="/static/images/dongthap.jpg" class="detail-img" alt="동센탑무어">
			<p>주요 볼거리:</p>
			<ul>
				<li>광활한 연꽃밭은 연꽃 시즌(5월~10월)에 가장 아름답습니다.</li>
				<li>체험 서비스: 보트를 타고 사진 촬영, 아오바바 착용, 연꽃, 다리 대나무에서 체크인하세요.</li>
				<li>연꽃 요리: 연밥, 연근 샐러드, 연꽃 달콤한 수프, 연꽃차.</li>
			</ul>
			<p>추천 메뉴:</p>
			<ul>
				<li>일찍 가세요. 오전 6시 30분~오후 9시 또는 시원한 오후 3시 30분~오후 5시 30분에 가세요.</li>
				<li>모자, 자외선 차단제를 챙기세요. 굽이 낮은 신발이나 샌들을 신으세요.</li>
				<li>비가 온 후에는 흙길이 미끄러울 수 있으니 피하세요.</li>
			</ul>
			"""},
			{"title": "사덱 꽃 마을",
			"desc": """
			<p>사덱 꽃 마을은 "서부의 꽃 수도"로, 독특한 물 위에 떠 있는 격자에 심어진 수천 송이의 관상용 꽃으로 유명합니다. 또한, 유명한 문화 생태 관광지로, 일 년 내내 사진을 찍고 꽃을 구매할 수 있습니다.</p>
			<p>📍위치: 탄 동탑, 사덱 시, 꾸이동 구. 까오란에서 약 30km 거리.</p>
			<p>역사 및 건축:</p>
			<ul>
				<li>19세기 후반에서 20세기 초에 형성됨.</li>
				<li>서부 지역의 오랜 전통 꽃 마을.</li>
				<li>건축적 특징: 고택, 전통 공예 마을, 전형적인 떠다니는 꽃꽂이.</li>
			</ul>
			<img src="/static/images/langhoa.jpg" class="detail-img" alt="사덱 꽃 마을">
			<p>주요 특징:</p>
			<ul>
				<li>100년이 넘는 역사를 자랑하는 꽃 마을.</li>
				<li>국화, 장미, 분재, 고대 관상용 식물 등 수천 종의 꽃과 관상용 식물.</li>
				<li>체크인 구역, 목조 다리, 온실, 마을의 집, 케이크 만들기 등이 있습니다. 잼.</li>
			</ul>
			<p>추천:</p>
			<ul>	
				<li>가장 좋은 시기: 음력 12월~1월.</li>
				<li>아침 일찍이나 해 질 무렵에 가는 것이 좋습니다.</li>
				<li>꽃 재배자를 존중하세요. 사진 촬영 시 꽃을 꺾지 마세요.</li>
			</ul>
			"""}, 
			{ "title": "꾸라오터이썬(꼰란)",
			"desc": """
			<p>꾸라오터이썬은 잔잔한 띠엔 강 한가운데에 위치해 있으며, 무성한 과수원과 작은 운하, 그리고 삼판 타기, 전통 음악 감상, 정원 특산품 즐기기 등 매력적인 지역 관광 활동을 즐길 수 있는 유명한 생태 관광지입니다.</p>
			<p>📍위치: 띠엔장성 미토시 토이썬 마을 띠엔 강 한가운데에 위치.</p>
			<p>주요 특징:</p>
			<ul>
				<li>넓고 푸른 섬으로, 과수원, 정원 가옥, 전통 공예 마을(코코넛 캔디, 꿀 만들기, 직조 등)로 유명합니다.</li>
				<li>방문객들은 작은 운하에서 삼판을 타고, 전통 음악을 듣고, 정원에서 수확한 과일을 맛보고, 소박한 공간에서 점심 식사를 즐길 수 있습니다.</li>
				<li>관광지입니다. 생태 관광 - 메콩 삼각주의 특징이 깃든 전형적인 공동체입니다.</li>
			</ul>
			<img src="/static/images/thoison.jpg" class="detail-img" alt="Cu Lao Thoi Son">
			<p>추천:</p>
			<ul>
				<li>햇볕을 피하고 시원한 공기를 즐기려면 아침 일찍 가는 것이 좋습니다.</li>
				<li>보트나 도보로 이동 가능한 구간이 많으므로 가벼운 옷과 움직이기 편한 신발을 착용하세요.</li>
				<li>전통 음악을 감상하고, 튀긴 코끼리 귀 생선을 먹고, 지역 특산품인 신선한 꿀을 마셔보세요.</li>
			</ul>
			"""},
			{ "title": "빈짱 사원(띠엔장)",
			"desc": """
			<p>띠엔장성에서 가장 오래되고 가장 큰 사원인 빈짱 사원은 아시아와 유럽이 어우러진 독특한 건축 양식을 자랑합니다. 평화로운 공간과 푸른 정원. 장엄한 불상이 있는 시원한 이 탑은 평화를 찾고 건축 예술의 정수를 감상하고 싶은 사람들에게 이상적인 곳입니다.</p>
			<p>📍위치: 미토시 8구 응우옌쭝쭉 66번지.</p>
			<img src="/static/images/chuavinhtrang.jpg" class="detail-img" alt="쭈아빈짱">
			<p>주요 특징:</p>
			<ul>
				<li>19세기에 건축된 띠엔장성에서 가장 오래되고 가장 큰 탑입니다.</li>
				<li>아시아와 유럽(프랑스, 로마, 태국, 캄보디아, 일본)의 건축 양식이 조화롭게 어우러져 보기 드문 독특한 모습을 자랑합니다.</li>
				<li>캠퍼스에는 거대한 미륵불상, 와불상, 그리고 아미타불이 있습니다. 정원.</li>
			</ul>
			<img src="/static/images/chuavinhtrang1.jpg" class="detail-img" alt="추아 빈 짱 1">
			<p>추천:</p>
			<ul>
				<li>예의 바르고 단정한 복장을 하고 신성한 장소에서는 질서를 유지하세요.</li>
				<li>미륵불상 주변과 사찰 정원에서 사진을 찍는 것은 매우 아름답습니다.</li>
				<li>꾸 라오 토이 썬도 같은 시간에 방문하세요.</li>
			</ul>
			"""}
			], 
			"An Giang": [
			{ "title": "깜산(티엔깜손) - 서쪽의 지붕",
			"desc": """
			<p>메콩 삼각주에서 가장 높은 산으로, 일 년 내내 서늘한 기후와 다채로운 자연 경관을 자랑합니다. 영적인 요소, 역사적 요소, 전설적인 요소로 가득 차 있어 종종 "서쪽의 지붕"으로 비유됩니다.</p>
			<p>📍위치: 안장성 띤비엔현 안하오사.</p>
			<img src="/static/images/nuicamangiang.jpg" class="detail-img" alt="깜산(티엔깜손) - "서쪽의 지붕"">
			<p>주요 볼거리:</p>
			<ul>
				<li>33.6m 높이의 미륵불상은 깜산의 상징으로, 베트남 최대 규모의 미륵불상 중 하나입니다.</li>
				<li>잔잔한 수면에 반사되는 투이리엠 호수의 반린 사원, 빅 부다 사원과 같은 영적인 사원과 함께 산은 많은 순례자를 끌어들입니다.</li>
				<li>깜산 케이블카를 타고 장엄한 탓썬 산의 파노라마를 위에서 감상하고 칠악산 지역의 장엄한 자연의 아름다움을 온전히 느껴보세요.</li>
			</ul>
			<p>추천:</p>
			<ul>
				<li>⏰ 방문 시간: 오전 6시부터 오후 6시까지 종일</li>
				<li>케이블카 티켓: 1인당 180,000 VND 이상</li>
				<li>햇볕을 피하려면 아침 일찍 가는 것이 좋으며, 운동화를 착용하세요. 트레킹을 할 경우 건기를 선택하세요.</li>
			</ul>
			"""},
			{ "title": "짜쑤 멜라루카 숲 - 홍수기의 낙원",
			"desc": """
			<p>부추풀이 뒤덮인 푸른 낙원 수백 종의 희귀 조류가 서식하는 아름다운 수면.</p>
			<p>📍위치: 띤비엔 현 반자오 마을, 쩌우독에서 약 30km 거리.</p>
			<img src="/static/images/rungtram.jpg" class="detail-img" alt="짜쑤 멜라루카 숲 - 홍수철의 천국">
			<p>주요 볼거리:</p>
			<ul>
				<li>140종 이상의 식물, 70종 이상의 조류(붉은 책에 등재된 희귀종 포함).</li>
				<li>푸른 개구리밥 숲 사이로 카누, 보트, 또는 노를 저어보세요. 베트남에서 가장 긴 대나무 다리에서 체크인하세요.</li>
				<li>생물다양성 보존 구역이자 환경 규제를 받는 곳으로, "베트남에서 가장 아름다운 카주풋 숲"으로 알려져 있습니다.</li>
			</ul>
			<img src="/static/images/rungtram1.jpg" class="detail-img" alt="Tra Su Cajuput Forest - Birds">
			<p>추천:</p>
			<ul>
				<li>가장 아름다운 풍경: 홍수기(9월~11월), 특히 새벽이나 해질녘에 방문하세요.</li>
				<li>아침이나 늦은 오후에 방문하세요. 카메라, 쌍안경, 그리고 편안한 신발을 준비하세요.</li>
			</ul>
			"""},
			{ "title": "푸꾸옥 - 진주섬",
			"desc": """
			<p>맑고 푸른 해변, 고급 리조트, 신선한 해산물을 자랑하는 유명한 해변 휴양지입니다.</p>
			<p>📍위치: 푸꾸옥은 베트남에서 가장 큰 섬으로, 끼엔장성에 속하며 태국만, 캄보디아 국경 근처에 있습니다.</p>
			<p>하이라이트:</p>
			<ul>
				<li>아름다운 바다와 모래사장: 맑은 바닷물, 잔잔한 파도, 수영하기에 매우 적합하며 스노클링.</li>
				<li>다양한 자연: 섬의 대부분은 유네스코가 지정한 생물권 보호구역에 위치해 있으며, 숲, 산, 그리고 해양-염생 생태계가 어우러져 있습니다.</li>
				<li>편리한 접근성 및 관광 개발: 현대적인 관광 인프라, 수많은 리조트, 그리고 엔터테인먼트 및 게임 시설이 있습니다.</li>
			</ul>
			<img src="/static/images/phuquoc.jpg" class="detail-img" alt="푸꾸옥 - 진주섬">
			<p>추천:</p>
			<ul>
				<li>가장 좋은 시기: 11월부터 4월까지의 건기 — 화창하고 잔잔한 바다에서 야외 및 해변 관광을 즐기기에 좋습니다.</li>
				<li>혼톰 케이블카는 오전 9시경 출발하며, 낮 동안 여러 정류장에 정차합니다. 혼잡을 피하려면 일찍 출발하는 것이 좋습니다.</li>
				<li>해변 산책/일몰 감상: 오후 5시경부터는 아름다운 일몰을 감상하기에 좋은 시간입니다. 섬의 서쪽 해변.</li>
			</ul>
			"""},
			{ "title": "하티엔 - 몽환적이고 낭만적인",
			"desc": """
			<p>푸꾸옥보다 느긋하고 평화로운 분위기가 감도는 이곳은 휴식을 취하거나 자연의 아름다움과 지역 문화를 탐험하고 싶은 관광객에게 적합합니다.</p>
			<p>📍위치: 끼엔장성 하티엔 타운, 락자 시에서 약 100km 거리.</p>
			<img src="/static/images/hatien.jpg" class="detail-img" alt="짜쑤 멜라루카 숲 - 조류">
			<p>주요 특징:</p>
			<ul>
				<li>서부에서는 보기 드문 그림 같은 풍경(산, 바다, 강, 동굴).</li>
				<li>다양한 문화(베트남, 크메르, 중국, 참)가 독특하게 어우러진 곳.</li>
				<li>신선한 해산물, 저렴한 가격, 다음과 같은 독특한 특산품 맘 까 슈와 소이 시엠.</li>
			</ul>
			<p>제안사항:</p>
			<ul>
				<li>최고의 시기: 11월~4월 (건기, 아름다운 바다, 적은 강우량)</li>
				<li>최고의 일몰: 무이나이 해변이나 푸꾸옥 섬이 내려다보이는 제방.</li>
				<li>추천 메뉴: 게살 국수, 찹쌀밥, 피시 소스 (선물로 구매 가능).</li>
			</ul>
			"""}
			]
		}
}
    # thêm dữ liệu map
map_places = []
    for province in place_details_data["vi"]:
        for p in place_details_data["vi"][province]:
            
             map_places.append({
                "title": p["title"],
                "slug": p.get("slug",""),
                "lat": p["lat"],
                "lng": p["lng"],
                "img": p.get("img",""),
                "province": province
            })


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
            "is_admin": False,
            "page": "home",
            "map_places": map_places,
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
            "map_places": map_places,
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
            "map_places": map_places,
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
            "map_places": map_places,
        })
@app.get("/food", response_class=HTMLResponse)
async def food(request: Request, lang: str = "vi"):
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
            "food_list": data.get("food_list", []),
            "comments": comments,
            "is_admin": False,
            "map_places": map_places,

        })
@app.get("/health", response_class=HTMLResponse)
async def health(request: Request, lang: str = "vi"):
    data = content.get(lang, content["vi"])
    health_list = data.get("health", [])

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
            "health_list": data.get("health_list", []),
            "comments": comments,
            "is_admin": False,
            "map_places": map_places,
        })
@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = "", lang: str = "vi"):
    data = content.get(lang, content["vi"])
    results = []

    if q:
        keyword = q.lower()
        for place in data.get("places", []):
            if keyword in place["name"].lower() or keyword in place.get("desc", "").lower():
                results.append(place)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data,
            "lang": lang,
            "results": results,
            "query": q,
            "comments": [],
            "is_admin": False,
            "page": "search",
            "map_places": map_places,
        }
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
		"title": data["title"],  
        "intro": data["intro"],
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
#-----------------------------------------------------
@app.get("/place/{slug}", response_class=HTMLResponse)
async def place_detail(request: Request, slug: str, lang: str = "vi"):

    for province in place_details_data[lang]:
        for p in place_details_data[lang][province]:
            if p["slug"] == slug:
                return templates.TemplateResponse(
                    "place_detail.html",
                    {
                        "request": request,
                        "place": p,
                        "lang": lang
                    }
                )

    # nếu không tìm thấy địa điểm
    raise HTTPException(status_code=404, detail="Place not found")



