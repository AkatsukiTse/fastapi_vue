### 基于FastApi的RuoYi-Vue后端框架

适配RuoYi-Vue前端，实现了基本模块接口

### 部署

1. 复制项目
2. 添加.env配置文件
```properties
# Mysql数据库地址
DATABASE_URI=mysql+aiomysql://root:root@localhost:3306/ry
# Redis地址
REDIS_URL=localhost:6379
```
3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行
```bash
fastapi dev app.py --port 8080
```

### 前端

请参考 https://gitee.com/y_project/RuoYi-Vue


### 还没实现的功能
* 日志
* 监控
* 代码生成