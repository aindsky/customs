# 地址报关单自动填写工具
import tkinter as tk
from tkinter import scrolledtext, messagebox
import re
import time
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

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
        self.title("地址报关单填充工具")
        self.geometry("750x650")
        tk.Label(self, text="地址报关单填充", font=("微软雅黑", 14, "bold")).pack(pady=10)
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
        tk.Label(extra_frame1, text="税号:").pack(side=tk.LEFT, padx=2)
        self.tax_entry = tk.Entry(extra_frame1, width=20)
        self.tax_entry.pack(side=tk.LEFT, padx=2)
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="解析订单", font=("",11), bg="#21ba45", fg="white",
                 command=self.parse).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="⚡自动填写", font=("",11, "bold"), bg="#e74c3c", fg="white",
                 command=self.auto_fill).pack(side=tk.LEFT, padx=5)
        self.result = scrolledtext.ScrolledText(self, width=85, height=6)
        self.result.pack(padx=10, pady=5)
        tk.Label(self, text="先解析订单，再点自动填写即可秒填网页！",
                font=("微软雅黑", 9), fg="gray").pack(pady=3)
        self.parsed_info = None
        self.driver = None

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

    def init_driver(self):
        if self.driver is not None:
            return True
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        chrome_options.add_argument("--no-sandbox")
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        ]
        chrome_exe = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_exe = path
                break
        if chrome_exe is None:
            messagebox.showerror("错误", "找不到Chrome！")
            return False
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except:
            pass
        os.system("taskkill /f /im chrome.exe 2>nul")
        time.sleep(1)
        try:
            subprocess.Popen([chrome_exe, "--remote-debugging-port=9222", "--no-first-run"])
            time.sleep(3)
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"启动失败！\n\n请手动操作：\n1.关闭所有Chrome\n2.Win+R输入:\nchrome.exe --remote-debugging-port=9222\n3.登录后重试")
            return False

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
        tax = self.tax_entry.get()
        state = info.get('state', info['city'])
        self.result.insert(tk.END, "\n正在连接Chrome...")
        self.update()
        if not self.init_driver():
            return
        self.result.insert(tk.END, "\n正在填写...")
        self.update()
        try:
            windows = self.driver.window_handles
            if windows:
                self.driver.switch_to.window(windows[-1])
            fields = {
                "refernumb": info['orderNumber'],
                "domesticno": info['orderNumber'],
                "goodsnum": qty,
                "weight": weight,
                "recname": info.get('en_name', info['name']),
                "recaddr1": info['street'],
                "recpost": info['zip'],
                "rectel": info['phone'],
                "reccity": info['city'],
                "recmobile": info['phone'],
                "recprovince": state,
                "cont_1": g['cn'],
                "customs_1": g['en'],
                "prodno_1": g['hs'],
                "itemweight_1": weight,
                "num_1": qty,
                "sbprice_1": price,
            }
            filled = 0
            errors = []
            for name, value in fields.items():
                try:
                    elem = self.driver.find_element(By.NAME, name)
                    elem.clear()
                    elem.send_keys(str(value))
                    filled += 1
                except:
                    errors.append(name)
            if errors:
                self.result.insert(tk.END, f"\n成功:{filled} 失败:{len(errors)}")
                messagebox.showwarning("部分完成", f"成功:{filled}个\n失败:{len(errors)}个\n\n未找到:\n"+"\n".join(errors))
            else:
                self.result.insert(tk.END, f"\n全部完成！共{filled}个")
                messagebox.showinfo("完成", f"全部填写完成！共{filled}个字段")
        except Exception as e:
            self.result.insert(tk.END, f"\n失败:{str(e)}")
            messagebox.showerror("错误", f"填写失败！\n请确保已打开填写页面。\n\n{str(e)}")

if __name__ == "__main__":
    app = CustomsApp()
    app.mainloop()
