# 报关单订单解析 + 自动填写工具
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import re
import csv
import time
import pyautogui
import pyperclip

GOODS_DATA = {
    1: {"cn": "休闲鞋", "en": "Casual shoes", "hs": "6402190090"},
    2: {"cn": "休闲上衣", "en": "Men's casual top", "hs": "6203330000"},
    3: {"cn": "帽子", "en": "Hat", "hs": "4304002000"},
    4: {"cn": "休闲包", "en": "Casual bag", "hs": "4202119090"},
    5: {"cn": "LED灯鞋", "en": "LED Light Shoe", "hs": "4203100090"},
    6: {"cn": "机械表", "en": "Mechanical Watch", "hs": "9017300000"},
}

def parse_order_info(text):
    order_info = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    for line in lines:
        if line.startswith("Order number:"):
            order_info["orderNumber"] = line.replace("Order number:", "").strip()
        elif line.startswith("Name:"):
            full_name = line.replace("Name:", "").strip()
            order_info["name"] = full_name
            parts = full_name.split()
            en_name = []
            for p in parts:
                if re.match(r'[a-zA-Z]', p):
                    en_name.append(p)
                else:
                    break
            order_info["en_name"] = " ".join(en_name) if en_name else full_name
        elif line.startswith("street:"):
            order_info["street"] = line.replace("street:", "").strip()
        elif line.startswith("City:"):
            order_info["city"] = line.replace("City:", "").strip()
        elif line.startswith("Province/state:") or line.startswith("Province:"):
            order_info["state"] = line.split(":", 1)[1].strip()
        elif line.startswith("Country:"):
            order_info["country"] = line.split(":", 1)[1].strip()
        elif re.search(r"ZIP\/postal\s*code:", line, re.I):
            order_info["zip"] = line.split(":", 1)[1].strip()
        elif line.startswith("Phonenumber:"):
            order_info["phone"] = line.replace("Phonenumber:", "").strip()
    
    if "state" not in order_info:
        order_info["state"] = order_info.get("city", "")
    
    required = ["orderNumber", "name", "street", "city", "zip", "phone"]
    missing = [f for f in required if f not in order_info]
    if missing:
        raise Exception("缺少字段：" + ",".join(missing))
    
    return order_info

class CustomsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("报关单填充工具 V3.1")
        self.geometry("750x750")
        
        tk.Label(self, text="报关单订单解析 + 自动填写工具", font=("微软雅黑", 14, "bold")).pack(pady=10)
        
        tk.Label(self, text="📋 订单信息粘贴区", font=("微软雅黑", 11)).pack(pady=3)
        self.text_input = scrolledtext.ScrolledText(self, width=85, height=12)
        self.text_input.pack(padx=10, pady=5)
        
        tk.Label(self, text="📦 选择商品类型", font=("微软雅黑", 11)).pack(pady=3)
        self.goods_var = tk.StringVar(value="1")
        goods_frame = tk.Frame(self)
        goods_frame.pack(pady=3)
        for key, goods in GOODS_DATA.items():
            tk.Radiobutton(goods_frame, text=goods['cn'], variable=self.goods_var,
                          value=str(key), font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=3)
        
        extra_frame1 = tk.Frame(self)
        extra_frame1.pack(pady=5)
        tk.Label(extra_frame1, text="件数:").pack(side=tk.LEFT, padx=2)
        self.qty_entry = tk.Entry(extra_frame1, width=8)
        self.qty_entry.pack(side=tk.LEFT, padx=2)
        self.qty_entry.insert(0, "1")
        
        tk.Label(extra_frame1, text="重量:").pack(side=tk.LEFT, padx=2)
        self.weight_entry = tk.Entry(extra_frame1, width=8)
        self.weight_entry.pack(side=tk.LEFT, padx=2)
        self.weight_entry.insert(0, "1")
        
        tk.Label(extra_frame1, text="单价:").pack(side=tk.LEFT, padx=2)
        self.price_entry = tk.Entry(extra_frame1, width=8)
        self.price_entry.pack(side=tk.LEFT, padx=2)
        self.price_entry.insert(0, "12")
        
        tk.Label(extra_frame1, text="备注:").pack(side=tk.LEFT, padx=2)
        self.remark_entry = tk.Entry(extra_frame1, width=12)
        self.remark_entry.pack(side=tk.LEFT, padx=2)
        self.remark_entry.insert(0, "DHL")
        
        extra_frame2 = tk.Frame(self)
        extra_frame2.pack(pady=5)
        tk.Label(extra_frame2, text="税号:").pack(side=tk.LEFT, padx=2)
        self.tax_entry = tk.Entry(extra_frame2, width=20)
        self.tax_entry.pack(side=tk.LEFT, padx=2)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="🔍 解析订单", font=("",11), bg="#21ba45", fg="white",
                 command=self.parse).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🤖 自动填写网页", font=("",11, "bold"), bg="#e74c3c", fg="white",
                 command=self.auto_fill).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="💾 导出CSV", font=("",11), bg="#2185d0", fg="white",
                 command=self.export_csv).pack(side=tk.LEFT, padx=5)
        
        self.result = scrolledtext.ScrolledText(self, width=85, height=8)
        self.result.pack(padx=10, pady=5)
        
        tk.Label(self, text="⚠️ 先点网页第一个输入框，再点自动填写", 
                font=("微软雅黑", 9), fg="gray").pack(pady=3)
        
        self.parsed_info = None
    
    def parse(self):
        try:
            info = parse_order_info(self.text_input.get("1.0", tk.END))
            self.parsed_info = info
            goods_key = int(self.goods_var.get())
            g = GOODS_DATA[goods_key]
            
            res = f"""订单号：{info['orderNumber']}
收件人：{info['name']}
地址：{info['street']}
城市：{info['city']}
省/州：{info.get('state', '')}
邮编：{info['zip']}
电话：{info['phone']}

商品：{g['cn']} | {g['en']} | {g['hs']}
"""
            self.result.delete("1.0", tk.END)
            self.result.insert("1.0", res)
            messagebox.showinfo("成功", "解析完成！")
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def auto_fill(self):
        if not self.parsed_info:
            messagebox.showwarning("提示", "请先解析订单信息！")
            return
        
        info = self.parsed_info
        goods_key = int(self.goods_var.get())
        g = GOODS_DATA[goods_key]
        
        qty = self.qty_entry.get()
        weight = self.weight_entry.get()
        price = self.price_entry.get()
        remark = self.remark_entry.get()
        tax = self.tax_entry.get()
        state = info.get('state', info['city'])
        
        # 修正后的Tab顺序，共34步
        fill_data = [
            ("fill", info['orderNumber']),   # 1. 客户订单号
            ("fill", info['orderNumber']),   # 2. 国内快递单号
            ("tab", None),                   # 3. 服务商单号-跳过
            ("tab", None),                   # 4. 渠道-下拉跳过
            ("tab", None),                   # 5. 渠道多跳一次
            ("tab", None),                   # 6. 目的地-下拉跳过
            ("tab", None),                   # 7. 是否退件-跳过
            ("tab", None),                   # 8. 是否带电-跳过
            ("tab", None),                   # 9. 是否购买保险-跳过
            ("fill", qty),                   # 10. 件数
            ("tab", None),                   # 11. 销售平台-跳过
            ("fill", weight),                # 12. 总重量(KG)
            ("tab", None),                   # 13. 货物类型-下拉跳过
            ("fill", remark),                # 14. 订单备注
            ("tab", None),                   # 15. 选择收件人-跳过
            ("fill", info.get('en_name', info['name'])),  # 16. 收件人名称
            ("fill", info['street']),        # 17. 地址1
            ("tab", None),                   # 18. 收件人邮箱-跳过
            ("fill", info['zip']),           # 19. 收件人邮编
            ("fill", info['phone']),         # 20. 收件人电话
            ("tab", None),                   # 21. 门牌号-跳过
            ("fill", info['city']),          # 22. 收件人城市
            ("fill", info['phone']),         # 23. 收件人手机
            ("fill", tax),                   # 24. 收件人税号
            ("fill", state),                 # 25. 收件人省/州
            ("tab", None),                   # 26. SKU-跳过
            ("tab", None),                   # 27. 配货信息-跳过
            ("fill", g['cn']),               # 28. 产品名称(中文)
            ("fill", g['en']),               # 29. 海关品名(英文)
            ("fill", g['hs']),               # 30. 海关编号(HS)
            ("fill", weight),                # 31. 净重(KG)
            ("fill", qty),                   # 32. 产品数量
            ("fill", price),                 # 33. 产品单价
            ("tab", None),                   # 34. 货币单位-下拉跳过
        ]
        
        messagebox.showinfo("准备填写", 
            "请立即点击网页第一个输入框！\n\n3秒后开始填写...")
        
        time.sleep(3)
        
        for i, (action, value) in enumerate(fill_data):
            if action == "tab":
                pyautogui.press('tab')
            else:
                pyautogui.doubleClick()
                time.sleep(0.05)
                pyperclip.copy(str(value))
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.05)
                pyautogui.press('tab')
            
            time.sleep(0.2)
        
        messagebox.showinfo("完成", "填写完成！请检查后手动提交。")
    
    def export_csv(self):
        content = self.result.get("1.0", tk.END)
        if not content.strip():
            messagebox.showwarning("警告", "没有可导出的内容")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                  filetypes=[("CSV文件", "*.csv")])
        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                for line in content.split('\n'):
                    if '：' in line:
                        key, value = line.split('：', 1)
                        writer.writerow([key.strip(), value.strip()])
            messagebox.showinfo("成功", f"已导出到: {file_path}")

if __name__ == "__main__":
    app = CustomsApp()
    app.mainloop()
