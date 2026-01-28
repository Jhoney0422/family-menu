import streamlit as st
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ================= 🔧 配置区 (请修改这里) =================
# ================= 🔧 配置区 (已修改为读取机密) =================
DB_FILE = "orders.csv"
ENABLE_EMAIL = True 
SMTP_SERVER = "smtp.qq.com"      
SMTP_PORT = 465                  

# 👇 关键修改：从云端保险箱读取隐私信息
if "email" in st.secrets:
    SENDER_EMAIL = st.secrets["email"]["sender"]
    PASSWORD = st.secrets["email"]["password"]
    RECEIVER_EMAIL = st.secrets["email"]["receiver"]
else:
    # 防止本地运行时报错
    SENDER_EMAIL = ""
    PASSWORD = ""
    RECEIVER_EMAIL = ""
# ========================================================
# ========================================================

st.set_page_config(page_title="🏠 爱家小食堂Pro", page_icon="🍲", layout="centered")


# --- 核心功能函数 ---

# 1. 读取数据库
def load_data():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame(columns=["时间", "点餐人", "菜名", "状态"])
    return pd.read_csv(DB_FILE)


# 2. 写入数据库
def save_data(time, user, dish):
    df = load_data()
    new_order = pd.DataFrame({"时间": [time], "点餐人": [user], "菜名": [dish], "状态": ["待制作"]})
    df = pd.concat([df, new_order], ignore_index=True)
    df.to_csv(DB_FILE, index=False)


# 3. 发送邮件通知
def send_email_msg(user, dish):
    if not ENABLE_EMAIL: return
    try:
        # 邮件内容
        subject = f"🔔 新订单：{user} 点了 {dish}"
        content = f"<h3>👨‍🍳 大厨请接单！</h3><p><b>点餐人：</b>{user}</p><p><b>菜品：</b>{dish}</p><p><b>时间：</b>{datetime.now().strftime('%H:%M')}</p>"

        message = MIMEText(content, 'html', 'utf-8')
        message['From'] = Header("爱家小食堂助手", 'utf-8')
        message['To'] = Header("大厨", 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')

        # 连接服务器发送
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, PASSWORD)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False


# --- 页面逻辑 ---

st.title("🍲 爱家小食堂 (云端版)")

# 侧边栏：大厨后台
with st.sidebar:
    st.header("👨‍🍳 厨房后台")
    # 简单的密码保护，防止乱点
    pwd = st.text_input("输入暗号查看订单", type="password")
    if pwd == "8888":  # 🔴 这里可以改你的密码
        df = load_data()
        if not df.empty:
            st.write("📋 **今日订单:**")
            st.table(df.iloc[::-1])  # 倒序显示

            if st.button("🗑️ 清空订单 (新的一天)"):
                if os.path.exists(DB_FILE):
                    os.remove(DB_FILE)
                    st.rerun()
        else:
            st.info("暂无订单")

# 菜单
menu = {
    "🍖 硬菜": ["红烧肉", "糖醋排骨", "清蒸鱼", "白灼虾"],
    "🥬 素菜": ["番茄炒蛋", "酸辣土豆丝", "蒜蓉青菜", "地三鲜"],
    "🍜 主食/汤": ["米饭", "馒头", "紫菜蛋花汤", "排骨汤"]
}

# 点餐区
st.subheader("📝 请点餐")
user_name = st.text_input("点餐人姓名", placeholder="例如：乖女儿")
category = st.selectbox("分类", list(menu.keys()))
dish_name = st.radio("菜品", menu[category])

if st.button("🚀 提交给大厨", type="primary"):
    if not user_name:
        st.error("请填写真实姓名！")
    else:
        # 1. 存数据
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_data(current_time, user_name, dish_name)

        # 2. 发邮件
        with st.spinner("正在通知大厨..."):
            success = send_email_msg(user_name, dish_name)

        if success:
            st.success(f"✅ 下单成功！邮件已发送给大厨！")
        else:
            st.warning("✅ 下单成功！(但邮件通知发送失败，请大厨手动查看后台)")

        st.balloons()


