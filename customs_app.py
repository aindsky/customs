# 报关单订单解析工具
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import re
import csv

GOODS_DATA = {
    1: {"cn": "休闲鞋", "en": "Casual shoes", "hs": "6402190090", "unit": "双"},
    2: {"cn": "休闲上衣", "en": "Men's casual top", "hs": "6203330000", "unit": "件"},
    3: {"cn": "帽子", "en": "Hat", "hs": "4304002000", "unit": "个"},
    4: {"cn": "休闲包", "en": "Casual bag", "hs": "4202119090", "unit": "个"},
    5: {"cn": "LED灯鞋", "en": "LED Light Shoe", "hs": "4203100090", "unit": "双"},
    6: {"cn": "机械表", "en": "Mechanical Watch", "hs": "9017300000", "unit": "块"},
}

def parse_order_info(text):
    order_info = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if line.startswith("Order number:"):
            order_info["orderNumber"] = line.replace("Order number:", "").strip()
        elif line.startswith("Name:"):
            order_info["name"] = line.replace("Name:", "").strip()
        elif line.startswith("street:"):
            order_info["street"] = line.replace("street:", "").strip()
        elif line.startswith("City:"):
            order_info["city"] = line.replace("City:", "").strip()
        elif re.search(r"ZIP\/postal\s*code:", line, re.I):
            order_info["zip"] = line.split(":", 1)[1].strip()
        elif line.startswith("Phonenumber:"):
            order_info["phone"] = line.replace("Phonenumber:", "").strip()
    required = ["orderNumber", "name", "street", "city", "zip", "phone"]
    missing = [f for f in required if f not in order_info]
    if missing:
        raise Exception("缺少字段：" + ",".join(missing))
    return order_info

class CustomsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("报关单填充工具 V2.0")
        self.geometry("700x600")
        
        tk.Label(self, text="订单信息粘贴区", font=("微软雅黑", 12)).pack(pady=5)
        self.text_input = scrolledtext.ScrolledText(self, width=80, height=14)
        self.text_input.pack(padx=10, pady=5)
        
        tk.Label(self, text="选择商品类型", font=("微软雅黑", 11)).pack(pady=2)
        self.goods_var = tk.StringVar(value="1")
        goods_frame = tk.Frame(self)
        goods_frame.pack(pady=3)
        for key, goods in GOODS_DATA.items():
            tk.Radiobutton(goods_frame, text=goods['cn'], variable=self.goods_var,
                          value=str(key), font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=3)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="解析订单信息", font=("",11), bg="#21ba45", fg="white",
                 command=self.parse).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="导出CSV", font=("",11), bg="#2185d0", fg="white",
                 command=self.export_csv).pack(side=tk.LEFT, padx=5)
        
        self.result = scrolledtext.ScrolledText(self, width=80, height=10)
        self.result.pack(padx=10, pady=5)
    
    def parse(self):
        try:
            info = parse_order_info(self.text_input.get("1.0", tk.END))
            goods_key = int(self.goods_var.get())
            g = GOODS_DATA[goods_key]
            res = f"""订单号：{info['orderNumber']}
收件人：{info['name']}
地址：{info['street']}
城市：{info['city']}
邮编：{info['zip']}
电话：{info['phone']}

商品中文：{g['cn']}
商品英文：{g['en']}
HS编码：{g['hs']}
单位：{g['unit']}
"""
            self.result.delete("1.0", tk.END)
            self.result.insert("1.0", res)
            messagebox.showinfo("成功", "解析完成！")
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
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
