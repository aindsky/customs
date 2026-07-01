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
        elif re.search(r"ZIP\/postal\s*code:", line, re.I):
            order_info["zip"] = line.split(":", 1)[1].strip()
        elif line.startswith("Phonenumber:"):
            order_info["phone"] = line.replace("Phonenumber:", "").strip()
    if "state" not in order_info:
        order_info["state"] = order_info.get("city", "")
    required = ["orderNumber", "name", "street", "city", "zip", "phone"]
    missing = [f for f in required if f not in order_info]
    if missing:
        raise Exception("Missing: " + ",".join(missing))
    return order_info

class CustomsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("报关单填充工具 V3.2")
        self.geometry("750x700")
        tk.Label(self, text="报关单订单解析 + 自动填写工具", font=("微软雅黑", 14, "bold")).pack(pady=10)
        tk.Label(self, text="订单信息粘贴区", font=("微软雅黑", 11)).pack(pady=3)
        self.text_input = scrolledtext.ScrolledText(self, width=85, height=12)
        self.text_input.pack(padx=10, pady=5)
        tk.Label(self, text="选择商品类型", font=("微软雅黑", 11)).pack(pady=3)
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
        tk.Button(btn_frame, text="解析订单", font=("",11), bg="#21ba45", fg="white",
                 command=self.parse).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="自动填写网页", font=("",11, "bold"), bg="#e74c3c", fg="white",
                 command=self.auto_fill).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="导出CSV", font=("",11), bg="#2185d0", fg="white",
                 command=self.export_csv).pack(side=tk.LEFT, padx=5)
        self.result = scrolledtext.ScrolledText(self, width=85, height=8)
        self.result.pack(padx=10, pady=5)
        tk.Label(self, text="先点网页第一个输入框，再点自动填写",
                font=("微软雅黑", 9), fg="gray").pack(pady=3)
        self.parsed_info = None

    def parse(self):
        try:
            info = parse_order_info(self.text_input.get("1.0", tk.END))
            self.parsed_info = info
            goods_key = int(self.goods_var.get())
            g = GOODS_DATA[goods_key]
            res = "订单号：" + info['orderNumber'] + "\n"
            res += "收件人：" + info['name'] + "\n"
            res += "地址：" + info['street'] + "\n"
            res += "城市：" + info['city'] + "\n"
            res += "省/州：" + info.get('state', '') + "\n"
            res += "邮编：" + info['zip'] + "\n"
            res += "电话：" + info['phone'] + "\n"
            res += "商品：" + g['cn'] + " | " + g['en'] + " | " + g['hs']
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
        fill_values = [
            info['orderNumber'],
            info['orderNumber'],
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            qty,
            None,
            weight,
            None,
            remark,
            None,
            info.get('en_name', info['name']),
            info['street'],
            None,
            info['zip'],
            info['phone'],
            None,
            info['city'],
            info['phone'],
            tax,
            state,
            None,
            None,
            g['cn'],
            g['en'],
            g['hs'],
            weight,
            qty,
            price,
            None,
        ]
        messagebox.showinfo("准备", "请点击网页第一个输入框！\n\n3秒后开始...")
        time.sleep(3)
        for value in fill_values:
            if value is None:
                pyautogui.press('tab')
            else:
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.03)
                pyperclip.copy(str(value))
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.03)
                pyautogui.press('tab')
            time.sleep(0.25)
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
            messagebox.showinfo("成功", "已导出到: " + file_path)

if __name__ == "__main__":
    app = CustomsApp()
    app.mainloop()
