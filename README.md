# StarResonanceSimpleDamageDistribution
Damage distribution for Star Resonance 星恒共鸣分时段增量伤害图




<img width="2482" height="974" alt="QQ_1754365166259" src="https://github.com/user-attachments/assets/935a6edc-f511-4d1f-93c7-4ad54dc26572" />




<img width="2338" height="723" alt="QQ_1754363666663" src="https://github.com/user-attachments/assets/552dd8d8-e10d-41e1-909b-ef61764478d7" />





本代码仅作为分析工具，不具备抓取游戏数据的功能。
抓取操作基于StarResonanceDamageCounter  https://github.com/dmlgzs/StarResonanceDamageCounter  
感谢大佬分享~

本代码由gemini协助生成，我参与了修改和优化。

无法区分职业或者伤害类型，治疗和伤害均会被算作增量伤害。

使用说明：

首先要安装并启动StarResonanceDamageCounter
参考：https://github.com/dmlgzs/StarResonanceDamageCounter  
确保可以打开 http://localhost:8989/ 的网页查看到DPS等详细参数。


然后克隆仓库

  ```bash
   git clone https://github.com/amoeet/StarResonanceSimpleDamageDistribution.git
   cd StarResonanceSimpleDamageDistribution
   ```

安装必要依赖：

   ```bash
   pip install dash pandas requests plotly Flask
   ```

启动：
   ```bash
   python app.py
   ```

打开 http://127.0.0.1:8050/

在API地址栏输入： http://localhost:8989/ 后，点击开始就会进行抓取，下拉菜单可以选择玩家，


修改代码中的
 ```bash
PLAYER_NAMES = {
    # 在这里预设一些已知的玩家ID和名称
    "114514": "老玩家",
    "9226643": "伊咪塔",
}
 ```

这个字典就可以自定义玩家名字。

数据仅供参考，可能存在失真，请勿用其伤害其他玩家，或者拉踩职业。




 
