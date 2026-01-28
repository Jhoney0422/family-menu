import streamlit as st
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# ================= 🔧 配置区 =================
DB_FILE = "orders.csv"

# 👇 读取 Secrets 配置
if "email" in st.secrets:
    SENDER_EMAIL = st.secrets["email"]["sender"]
    PASSWORD = st.secrets["email"]["password"]
    RECEIVER_EMAIL = st.secrets["email"]["receiver"]
    ENABLE_EMAIL = True
else:
    SENDER_EMAIL = ""
    PASSWORD = ""
    RECEIVER_EMAIL = ""
    ENABLE_EMAIL = False
    
SMTP_SERVER = "smtp.qq.com"      
SMTP_PORT = 465                  
# ============================================

st.set_page_config(page_title="🏠 快快家族大食堂", page_icon="🍲")

# --- 核心函数 ---
def load_data():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame(columns=["时间", "点餐人", "菜名", "状态"])
    return pd.read_csv(DB_FILE)

def save_data(time, user, dish_string):
    df = load_data()
    # dish_string 现在可能是一串菜名，比如 "红烧肉, 米饭, 可乐"
    new_order = pd.DataFrame({"时间": [time], "点餐人": [user], "菜名": [dish_string], "状态": ["待制作"]})
    df = pd.concat([df, new_order], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

def send_email_msg(user, dish_string):
    if not ENABLE_EMAIL or not PASSWORD: 
        return False
        
    try:
        # 邮件标题也稍微改一下，显示菜的数量
        dish_count = len(dish_string.split(','))
        subject_text = f"🔔 新订单：{user} 点了 {dish_count} 个菜"
        
        # 把菜名换行显示，更清晰
        formatted_dishes = dish_string.replace(", ", "<br>🥘 ")
        
        content = f"""
        <h3>👨‍🍳 大厨请接单！</h3>
        <p><b>⏰ 时间：</b>{datetime.now().strftime('%H:%M')}</p>
        <p><b>👤 谁点的：</b>{user}</p>
        <hr>
        <p><b>👇 菜单详情：</b></p>
        <p style="font-size:16px; font-weight:bold; color:#d9534f;">🥘 {formatted_dishes}</p>
        <hr>
        """
        
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
        print(f"❌ 邮件错误: {e}")
        return False

# --- 页面UI ---
st.title("🍲 快快家族大食堂")

# 侧边栏：大厨后台
with st.sidebar:
    st.header("👨‍🍳 厨房后台")
    if st.checkbox("我是大厨"):
        pwd = st.text_input("输入密码", type="password")
        if pwd == "8888": 
            df = load_data()
            if not df.empty:
                st.write(df.iloc[::-1])
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下载今日菜单", csv, "menu.csv", "text/csv")
                if st.button("🗑️ 清空所有订单"):
                    if os.path.exists(DB_FILE):
                        os.remove(DB_FILE)
                        st.rerun()
            else:
                st.info("暂无订单")

# 菜单配置
menu = {
    "🍖 硬菜区": ["香菜牛肉", "香芋排骨", "可乐鸡翅", "清蒸鱼", "黄瓜火腿","红烧猪蹄","白灼虾"],
    "🥬 素菜区": ["番茄炒蛋", "酸辣土豆丝", "炒青菜", "地三鲜", "凉拌黄瓜","虎皮尖椒"],
    "🍜 汤": ["丝瓜肉丸汤","鲜鲜美美土鸡汤", "玉米排骨汤"],
    "🥤 快乐水": ["冰可乐", "雪碧", "热牛奶", "鲜榨果汁"]
}

st.subheader("📝 请开始点餐")
user_name = st.text_input("你的大名")

# 🟢 核心修改：使用多选框 (Multiselect)
all_selected = [] # 用来存所有选中的菜

# 遍历菜单，为每个分类创建一个多选框
for category, items in menu.items():
    # specifically multiselect allows multiple choices
    selected = st.multiselect(f"选择 {category}", items)
    if selected:
        all_selected.extend(selected) # 把选中的菜加到总列表里

st.divider() # 分割线

# 结算区
if st.button("🚀 提交整张订单", type="primary"):
    if not user_name:
        st.error("请先留下大名！")
    elif not all_selected:
        st.warning("你什么都没点呀！")
    else:
        # 把列表变成字符串，例如 "红烧肉, 米饭"
        order_str = ", ".join(all_selected)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 保存并发送
        save_data(current_time, user_name, order_str)
        
        with st.spinner("正在把菜单飞鸽传书给大厨..."):
            is_sent = send_email_msg(user_name, order_str)
        
        if is_sent:
            st.balloons()
            st.success(f"✅ 下单成功！你点了 {len(all_selected)} 个菜，大厨已收到！")
        else:
            st.success("✅ 下单成功！(但邮件通知未发送，请口头提醒大厨)")



