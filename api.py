from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from pymongo import MongoClient
from datetime import datetime
from pyfcm import FCMNotification
import uvicorn
from datetime import date

fcm = FCMNotification(service_account_file="service_account_file.json", project_id = "chatroom-4cb12")

# 连接到 MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["chatroom_db"]

print(client.list_database_names())
# 定义 FastAPI 应用
app = FastAPI()

# 定义数据模型
class Chatroom(BaseModel):
    id: int
    name: str

class Message(BaseModel):
    message: str
    name: str
    message_time: str
    user_id: int

class FCMtoken(BaseModel):
    token: str
    user_id: int

class SendMessage(BaseModel):
    chatroom_id: int
    user_id: int
    name: str
    message: str


@app.get("/demo/")
async def get_demo(a: int = 0, b: int = 0, status_code=200):
  sum = a+b
  data = {"sum": sum, "date": date.today()}
  return JSONResponse(content=jsonable_encoder(data))

# define a route, binding a function to a URL (e.g. GET method) of the server
@app.get("/hello")
async def root():
    fcm_token = "dj6N8x51T4CjrJ7qIGICEg:APA91bEI9SSxS4q3CQrd-KMCRC9lXdn7WZL9h12x_Zx2wJtbMrYhoxW0N-sjJ1B3IaArYw7-tHsTSr3rDKUsHSFezJN3WUWiCziqhqpYfdlBcbHbwx_IL5c"
    notification_title = "Server sends you a text message!"
    notification_body = "Hello, I'm server."
    result1 = fcm.notify(fcm_token = fcm_token, notification_title = notification_title,notification_body=notification_body)

    data_payload = {
        "foo":"bar",
        "body": "great match",
        "room": "ssss"
    }
    result2 = fcm.notify(fcm_token = fcm_token,notification_title = "Server sends you a data message!",notification_body=notification_body,data_payload=data_payload)

    return {"message": "Hello World"}  # the API returns a JSON response


@app.get("/init")
async def initialize():
    chatrooms = db.create_collection("chatrooms")
    # chatrooms = db.get_collection("chatrooms")
    chatrooms.insert_many([
        {"id": 3, "name": "Chatroom 2"},
        {"id": 2, "name": "General Chatroom"}
    ])

    # 创建 messages 集合并插入数据
    messages = db.create_collection("messages")
    # messages = db.get_collection("messages")
    messages.insert_many([
        {
            "message": "5722",
            "name": "Danny",
            "message_time": "2024-09-29 19:36",
            "user_id": 1,
            "chatroom_id": 3
        },
        {
            "message": "distributed system",
            "name": "Danny",
            "message_time": "2024-09-29 19:36",
            "user_id": 1,
            "chatroom_id": 3
        },
        {
            "message": "scalable system",
            "name": "Danny",
            "message_time": "2024-09-29 19:36",
            "user_id": 1,
            "chatroom_id": 3
        },
        {
            "message": "mobile app",
            "name": "Danny",
            "message_time": "2024-09-29 19:36",
            "user_id": 1,
            "chatroom_id": 3
        },
        {
            "message": "test",
            "name": "Danny",
            "message_time": "2024-09-29 19:36",
            "user_id": 1,
            "chatroom_id": 3
        },
        {
            "message": "software engineering",
            "name": "Danny",
            "message_time": "2024-09-29 19:44",
            "user_id": 1,
            "chatroom_id": 2
        },
        {
            "message": "testing 123 TESTING 123",
            "name": "Danny",
            "message_time": "2024-09-29 19:41",
            "user_id": 1,
            "chatroom_id": 2
        },
        {
            "message": "agile scrum",
            "name": "Danny",
            "message_time": "2024-09-29 19:38",
            "user_id": 1,
            "chatroom_id": 2
        }
    ])
    return {"message": "Initialize Success!"}



# 获取聊天室列表
@app.get("/get_chatrooms/")
async def get_chatrooms(request: Request):
    # 检查是否有额外的查询参数
    if request.query_params:
        raise HTTPException(status_code=400, detail="Extra parameters are not allowed")

    # 假设 db 是一个数据库连接对象
    chatrooms = db.chatrooms.find({}, {"_id": 0})
    chatrooms_list = list(chatrooms)

    if not chatrooms_list:
        raise HTTPException(status_code=404, detail="No chatrooms found")

    return JSONResponse(content={"data": chatrooms_list, "status": "OK"})


# 获取特定聊天室的消息
@app.get("/get_messages/")
async def get_messages(chatroom_id: int):
    # 检查 chatroom_id 是否存在
    chatroom_exists = db.chatrooms.find_one({"id": chatroom_id})
    if not chatroom_exists:
        raise HTTPException(status_code=404, detail=f"Chatroom with id {chatroom_id} does not exist")

    # 获取指定聊天室的消息
    messages = db.messages.find({"chatroom_id": chatroom_id}, {"_id": 0, "chatroom_id": 0})
    messages_list = list(messages)
    if not messages_list:
        raise HTTPException(status_code=404, detail="No messages found")

    return JSONResponse(content={"data": {"messages": messages_list}, "status": "OK"})

# 添加到 FCM 应用
@app.post("/submit_push_token/")
async def submit_push_token(token: FCMtoken):
    print("New token submitted from user",token.user_id,":",token.token)
    # 存储token到数据库
    db.tokens.insert_one({"user_id": token.user_id, "token": token.token})

    return JSONResponse(content={"status": "OK"})

# 发送消息
@app.post("/send_message/")
async def send_message(message: SendMessage):

    # 检查名称和消息的长度
    if len(message.name) > 20:
        raise HTTPException(status_code=400, detail="Name exceeds 20 characters")
    if len(message.message) > 200:
        raise HTTPException(status_code=400, detail="Message exceeds 200 characters")

    # 检查 chatroom_id 是否存在
    chatroom_exists = db.chatrooms.find_one({"id": message.chatroom_id})
    if not chatroom_exists:
        raise HTTPException(status_code=404, detail=f"Chatroom with id {message.chatroom_id} does not exist")

    # 将消息存储到数据库
    db.messages.insert_one({
        "chatroom_id": message.chatroom_id,
        "message": message.message,
        "name": message.name,
        "message_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user_id": message.user_id
    })

    return JSONResponse(content={"status": "OK"})

# 启动 Uvicorn 服务
if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=55722)