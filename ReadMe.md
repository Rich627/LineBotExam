# AWS Quiz Bot 專案

AWS Quiz Bot是一個基於AWS服務構建的互動式測驗應用，它利用LINE Messaging API和AWS DynamoDB來創建和管理測驗問題，以及追蹤用戶的狀態和進度。

## 專案結構

- **Lambda函數**：處理LINE消息事件，管理用戶狀態，並與DynamoDB交互。
- **DynamoDB表**：
  - `QuizQuestions`：存儲測驗問題、選項和正確答案。
  - `UserStates`：追蹤用戶的答題狀態和測驗完成情況。

## 配置

### 前提條件

- AWS賬號
- LINE Developers賬號
- Python 3.11

### 環境變量

- `CHANNEL_ACCESS_TOKEN`：您的LINE頻道訪問令牌。
- `CHANNEL_SECRET`：您的LINE頻道密鑰。

### DynamoDB表格

#### `QuizQuestions`

- **QuestionID**：問題的唯一標識符（數字型）。
- **CorrectAnswer**：問題的正確答案選項（字串型）。
- **Options**：包含所有選項的映射（映射型）。
- **Question**：問題的描述（字串型）。

#### `UserStates`

- **UserID**：用戶的唯一標識符（字串型）。
- **HasAnswered**：標記用戶是否已經回答了問題（布爾型）。
- **QuizCompleted**：標記用戶是否完成了測驗（布爾型）。

## 部署

1. 將Lambda函數代碼部署到AWS Lambda。
2. 設置Lambda函數的環境變量。
3. 在DynamoDB中創建`QuizQuestions`和`UserStates`表格。
4. 在LINE Developers控制台配置Webhook URL。

## 使用

用戶通過發送消息給LINE Bot來開始或繼續他們的測驗。Bot會根據用戶的當前狀態回復適當的問題或反饋。

## 功能

- **開始測驗**：用戶發送"start quiz"開始測驗。
- **答題**：用戶回答問題，Bot根據答案的正確性給予反饋。
- **測驗進度**：追蹤用戶的答題狀態和測驗完成情況。
