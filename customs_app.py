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
    
    # 要填写的值（只填需要填写的位置，None=跳过按Tab）
    fill_values = [
        info['orderNumber'],       # 1. 客户订单号
        info['orderNumber'],       # 2. 国内快递单号
        None,                      # 3. 服务商单号-跳过
        None,                      # 4. 渠道-下拉跳过
        None,                      # 5. 渠道多一次Tab
        None,                      # 6. 目的地-下拉跳过
        None,                      # 7. 是否退件
        None,                      # 8. 是否带电
        None,                      # 9. 是否购买保险
        qty,                       # 10. 件数
        None,                      # 11. 销售平台
        weight,                    # 12. 总重量
        None,                      # 13. 货物类型
        remark,                    # 14. 订单备注
        None,                      # 15. 选择收件人
        info.get('en_name', info['name']),  # 16. 收件人名称
        info['street'],            # 17. 地址1
        None,                      # 18. 邮箱
        info['zip'],               # 19. 邮编
        info['phone'],             # 20. 电话
        None,                      # 21. 门牌号
        info['city'],              # 22. 城市
        info['phone'],             # 23. 手机
        tax,                       # 24. 税号
        state,                     # 25. 省/州
        None,                      # 26. SKU
        None,                      # 27. 配货信息
        g['cn'],                   # 28. 产品名称(中文)
        g['en'],                   # 29. 海关品名(英文)
        g['hs'],                   # 30. 海关编号(HS)
        weight,                    # 31. 净重
        qty,                       # 32. 产品数量
        price,                     # 33. 产品单价
        None,                      # 34. 货币单位
    ]
    
    messagebox.showinfo("准备填写",
        "请立即点击网页第一个输入框（客户订单号）！\n\n3秒后开始...\n\n⚠️填写期间请勿碰键盘鼠标！")
    
    time.sleep(3)
    
    for i, value in enumerate(fill_values):
        if value is None:
            # 跳过，只按Tab
            pyautogui.press('tab')
        else:
            # 先全选再输入
            pyautogui.hotkey('ctrl', 'a')  # 全选
            time.sleep(0.05)
            pyperclip.copy(str(value))
            pyautogui.hotkey('ctrl', 'v')  # 粘贴
            time.sleep(0.05)
            pyautogui.press('tab')         # 跳到下一个
        
        time.sleep(0.25)  # 每个框之间延迟0.25秒
    
    messagebox.showinfo("完成", "填写完成！请检查网页后手动提交。")
