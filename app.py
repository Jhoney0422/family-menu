import streamlit as st
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# ================= 🔧 配置区 (已升级为读取云端保险箱) =================
DB_FILE = "orders.csv"

# 👇 尝试从 Secrets 读取配置，如果没有配置(比如本地运行)，则使用空值防止报错
if "email" in st.secrets:
    SENDER_EMAIL = st.secrets["email"]["sender"]
    PASSWORD = st.secrets["email"]["password"]
    RECEIVER_EMAIL = st.secrets["email"]["receiver"]
    ENABLE_EMAIL = True
else:
    SENDER_EMAIL = ""
    PASSWORD = ""
    RECEIVER_EMAIL = ""
    ENABLE_EMAIL = False # 没密码就不发邮件
    
SMTP_SERVER = "smtp.qq.com"      
SMTP_PORT = 465                  
# ===================================================================

st.set_page_config(page_title="🏠 爱家小食堂", page_icon="🍲")

# --- 核心函数 ---
def load_data():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame(columns=["时间", "点餐人", "菜名", "状态"])
    return pd.read_csv(DB_FILE)

def save_data(time, user, dish):
    df = load_data()
    new_order = pd.DataFrame({"时间": [time], "点餐人": [user], "菜名": [dish], "状态": ["待制作"]})
    df = pd.concat([df, new_order], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

def send_email_msg(user, dish):
    # 如果没开邮件功能或者密码为空，直接返回失败
    if not ENABLE_EMAIL or not PASSWORD: 
        print("❌ 邮件发送跳过：未配置密码")
        return False
        
    try:
        subject_text = f"🔔 新订单：{user} - {dish}"
        content = f"""
        <h3>👨‍🍳 大厨请接单！</h3>
        <p><b>⏰ 时间：</b>{datetime.now().strftime('%H:%M')}</p>
        <p><b>👤 谁点的：</b>{user}</p>
        <p><b>🍲 点的啥：</b>{dish}</p>
        <hr>
        <p style="font-size:12px;color:gray;">来自爱家小食堂自动推送</p>
        """
        
        # 🟢【修复乱码的关键】使用 Header 对象处理中文
        message = MIMEText(content, 'html', 'utf-8')
        message['From'] = formataddr((Header("家庭点餐助手", 'utf-8').encode(), SENDER_EMAIL))
        message['To'] = formataddr((Header("大厨", 'utf-8').encode(), RECEIVER_EMAIL))
        message['Subject'] = Header(subject_text, 'utf-8')

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, PASSWORD)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ 邮件发送报错: {e}") # 这里会在后台打印错误原因
        return False

# --- 页面UI ---
st.title("🍲 爱家小食堂 (云端版)")

# 侧边栏
with st.sidebar:
    st.header("👨‍🍳 厨房后台")
    if st.checkbox("我是大厨"):
        pwd = st.text_input("输入密码", type="password")
        if pwd == "8888": 
            df = load_data()
            if not df.empty:
                st.write(df.iloc[::-1])
                # 下载按钮
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下载今日菜单", csv, "menu.csv", "text/csv")
                
                # 清空按钮
                if st.button("🗑️ 清空所有订单"):
                    if os.path.exists(DB_FILE):
                        os.remove(DB_FILE)
                        st.rerun()
            else:
                st.info("暂无订单")

# 菜单
menu = {
    "🍖 硬菜": ["红烧肉", "糖醋排骨", "可乐鸡翅", "清蒸鱼"],
    "🥬 素菜": ["番茄炒蛋", "酸辣土豆丝", "炒青菜", "地三鲜"],
    "🍚 主食": ["米饭", "面条", "馒头", "水饺"]
}

st.subheader("📝 今天吃点啥？")
user_name = st.text_input("你的大名")
category = st.selectbox("分类", list(menu.keys()))
dish_name = st.radio("菜品", menu[category])

if st.button("🚀 提交订单", type="primary"):
    if not user_name:
        st.error("不写名字不给做！")
    else:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_data(current_time, user_name, dish_name)
        
        with st.spinner("正在呼叫大厨..."):
            is_sent = send_email_msg(user_name, dish_name)
        
        if is_sent:
            st.success("✅ 下单成功！大厨已收到邮件通知！")
            st.balloons()
        else:
            st.warning("✅ 下单成功！(但邮件通知发送失败，请让大厨手动看后台)")
            # 这里给用户一点提示，告诉他们是不是因为密码没配对
            if not ENABLE_EMAIL:
                st.caption("原因：未检测到Secrets配置，请在后台配置[email]信息。")
