這是一個實驗型的小專題: Customer Service Agent System
-----------------------------------

請先安裝適用於您的電腦的MySQL版本，並在VS Code中擴充 MySQL(我擴充的是Database Client版本)。

在主資料庫的Query貼上: DB_CREATE.text 的內容 (ai_agent_db是我創建的資料庫名稱，請您遵照您的資料庫名稱)

創建好可連線的資料庫後，請到db_pool.py裡面，調整成適合您的連線command。(DB_URL = "mysql+pymysql://"User Name":"DB Password"@localhost:"Port"/ai_agent_db")

運行後，Terminal應該要顯示: **Successfully connected to database!**

接下來，就可以運行agent.py，並嘗試用看看此 Customer Service Agent!
----------------------------------------------------------------

功能(tool.py):

  -查詢客戶資料
  
  -查詢訂單資料
  
  -處理(登記)退款
  
  -退款取消
  
  -登錄客訴內容(包含客戶喜好資訊)
  
  -創建新會員 (須提供名字與信箱，信箱格式目前固定為: xxx@example.com，只有xxx的部分可改動)
  
  -創建新訂單
